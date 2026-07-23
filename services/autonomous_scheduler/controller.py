"""Autonomous Production Scheduler controller — Trend → Queue → GenOS → Ops."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from core.log import get_logger, log_event
from services.autonomous_scheduler.dashboard import build_scheduler_dashboard, write_scheduler_dashboard
from services.autonomous_scheduler.finalize import organize_completed_project, prepare_publishing_queue
from services.autonomous_scheduler.metrics import record_metric
from services.generational_os.scheduler import run_next_job, schedule_production, scheduler_dashboard
from services.trend_opportunity.brief import to_studio_brief_kwargs

logger = get_logger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ingest_trend_rankings(
    *,
    subject: str = "science education",
    category: str = "science",
    queue_count: int = 5,
    top_n: int = 25,
    publishing_enabled: bool = False,
    target_channel: str = "",
) -> dict[str, Any]:
    """Read Trend Intelligence rankings and enqueue production priorities into GenOS."""
    import services.trend_opportunity as trend_opportunity

    trends = trend_opportunity.run_trend_opportunity(
        subject,
        category=category,
        top_n=top_n,
        brief_count=max(10, queue_count),
        high_confidence_count=min(5, queue_count),
        persist=True,
        write_reports=True,
    )
    top = list(trends.get("top_opportunities") or [])
    queued: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for i, opp in enumerate(top[:queue_count]):
        brief = opp.get("production_brief") or {}
        kwargs = to_studio_brief_kwargs(brief)
        priority = int(opp.get("production_priority") or (100 - i))
        cons = dict(kwargs.get("constraints") or {})
        cons["publishing_enabled"] = bool(publishing_enabled)
        cons["from_autonomous_scheduler"] = True
        cons["from_genos"] = True
        if target_channel:
            cons["target_channel"] = target_channel
        # Soft channel route when Channel OS is available
        if not target_channel:
            try:
                from services.channel_os.routing import route_opportunity

                routed = route_opportunity(opp)
                channel_id = (routed or {}).get("selected_channel_id") if isinstance(routed, dict) else None
                if channel_id:
                    cons["target_channel"] = channel_id
                    cons["channel_route"] = {
                        "channel_id": channel_id,
                        "score": routed.get("selected_score"),
                        "brand": routed.get("selected_brand"),
                    }
            except Exception:  # noqa: BLE001
                pass

        result = schedule_production(
            topic=str(kwargs.get("topic") or opp.get("topic") or ""),
            platform=str(kwargs.get("platform") or "youtube_shorts"),
            length_sec=int(kwargs.get("length_sec") or 40),
            style=str(kwargs.get("style") or "educational"),
            narrator=str(kwargs.get("narrator") or "professor"),
            command=str(kwargs.get("command") or ""),
            priority=priority,
            category=str(category or brief.get("category") or cons.get("category") or ""),
            target_channel=str(cons.get("target_channel") or target_channel or ""),
            world=str(
                (brief.get("world_selection") or {}).get("world_id")
                if isinstance(brief.get("world_selection"), dict)
                else brief.get("world_selection") or ""
            ),
            constraints=cons,
            production_brief=brief,
            run_immediately=False,
            allow_duplicate=False,
        )
        if result.get("ok"):
            queued.append(result)
            record_metric(
                "job_queued",
                {
                    "job_id": (result.get("job") or {}).get("job_id"),
                    "topic": opp.get("topic"),
                    "priority": priority,
                    "category": category,
                },
            )
        else:
            skipped.append(result)

    log_event(
        logger,
        "autonomous_scheduler.ingested",
        ranked=len(top),
        queued=len(queued),
        skipped=len(skipped),
    )
    return {
        "ok": True,
        "ranked": len(top),
        "queued_ok": len(queued),
        "skipped_duplicates": len(skipped),
        "queued": queued,
        "skipped": skipped,
        "top_topic": (top[0] or {}).get("topic") if top else None,
        "scheduler": scheduler_dashboard(),
    }


def run_scheduler_tick(
    *,
    max_retries: int = 2,
    publishing_enabled: bool = False,
) -> dict[str, Any]:
    """
    One autonomous tick:
    monitor queue → launch highest-priority pending job → track → retry/skip → finalize.
    """
    t0 = time.time()
    pending_before = scheduler_dashboard()
    record_metric(
        "tick_started",
        {
            "waiting": pending_before.get("jobs_waiting"),
            "running": pending_before.get("jobs_running"),
        },
    )

    result = run_next_job(max_retries=max_retries)
    if not result:
        dash_paths = write_scheduler_dashboard()
        return {
            "ok": True,
            "idle": True,
            "message": "No pending jobs — scheduler idle",
            "dashboard": dash_paths,
            "elapsed_ms": int((time.time() - t0) * 1000),
        }

    job = result.get("job") if isinstance(result.get("job"), dict) else {}
    ops = result.get("result") if isinstance(result.get("result"), dict) else {}
    status = str(result.get("status") or "")
    elapsed_ms = int((time.time() - t0) * 1000)
    finalized: dict[str, Any] = {}
    publish_prep: dict[str, Any] = {}

    if status == "succeeded":
        finalized = organize_completed_project(job, ops)
        publish_prep = prepare_publishing_queue(
            job, ops, publishing_enabled=publishing_enabled or bool(job.get("publishing_enabled"))
        )
        record_metric(
            "production_completed",
            {
                "job_id": job.get("job_id"),
                "production_id": job.get("production_id") or ops.get("production_id"),
                "topic": job.get("topic"),
                "quality_score": job.get("quality_score"),
                "elapsed_ms": elapsed_ms,
                "retry_count": job.get("retry_count"),
                "category": job.get("category"),
            },
        )
    elif status == "retry_queued":
        record_metric(
            "production_retry_queued",
            {
                "job_id": result.get("job_id"),
                "topic": job.get("topic"),
                "failure_reason": job.get("failure_reason"),
                "classification": (result.get("classification") or {}).get("class"),
            },
        )
    else:
        record_metric(
            "production_failed",
            {
                "job_id": job.get("job_id") or result.get("job_id"),
                "topic": job.get("topic"),
                "failure_reason": job.get("failure_reason") or result.get("error"),
                "skipped_unrecoverable": bool(result.get("skipped_unrecoverable")),
                "classification": (result.get("classification") or {}).get("class"),
                "elapsed_ms": elapsed_ms,
            },
        )

    dash_paths = write_scheduler_dashboard(build_scheduler_dashboard())
    log_event(
        logger,
        "autonomous_scheduler.tick",
        status=status,
        job_id=result.get("job_id"),
        idle=False,
    )
    return {
        "ok": True,
        "idle": False,
        "status": status,
        "job_id": result.get("job_id"),
        "job": job,
        "result": {
            "production_id": ops.get("production_id") if ops else None,
            "success": ops.get("success") if ops else None,
            "video_exists": result.get("video_exists") or ops.get("video_exists"),
        },
        "finalized": finalized,
        "publishing_prep": publish_prep,
        "classification": result.get("classification"),
        "skipped_unrecoverable": result.get("skipped_unrecoverable"),
        "dashboard": dash_paths,
        "elapsed_ms": elapsed_ms,
        "generated_at": _now(),
    }


def run_autonomous_batch(
    *,
    subject: str = "science education",
    category: str = "science",
    queue_count: int = 3,
    execute_count: int = 2,
    top_n: int = 20,
    publishing_enabled: bool = False,
    target_channel: str = "",
    max_retries: int = 2,
    skip_ingest: bool = False,
) -> dict[str, Any]:
    """Ingest trend rankings (optional) then autonomously drain N jobs."""
    t0 = time.time()
    ingest = None
    if not skip_ingest:
        ingest = ingest_trend_rankings(
            subject=subject,
            category=category,
            queue_count=queue_count,
            top_n=top_n,
            publishing_enabled=publishing_enabled,
            target_channel=target_channel,
        )

    ticks: list[dict[str, Any]] = []
    for _ in range(max(0, int(execute_count))):
        tick = run_scheduler_tick(max_retries=max_retries, publishing_enabled=publishing_enabled)
        ticks.append(tick)
        if tick.get("idle"):
            break

    summary = {
        "ok": True,
        "generated_at": _now(),
        "publishing_enabled": bool(publishing_enabled),
        "architecture_frozen": True,
        "ingest": {
            "ranked": (ingest or {}).get("ranked"),
            "queued_ok": (ingest or {}).get("queued_ok"),
            "top_topic": (ingest or {}).get("top_topic"),
        }
        if ingest
        else {"skipped": True},
        "ticks": len(ticks),
        "executed": sum(1 for t in ticks if not t.get("idle")),
        "succeeded": sum(1 for t in ticks if t.get("status") == "succeeded"),
        "failed": sum(1 for t in ticks if t.get("status") == "failed"),
        "retried": sum(1 for t in ticks if t.get("status") == "retry_queued"),
        "tick_results": [
            {
                "status": t.get("status"),
                "job_id": t.get("job_id"),
                "idle": t.get("idle"),
                "production_id": (t.get("result") or {}).get("production_id"),
                "elapsed_ms": t.get("elapsed_ms"),
            }
            for t in ticks
        ],
        "dashboard": write_scheduler_dashboard(),
        "scheduler": scheduler_dashboard(),
        "elapsed_ms": int((time.time() - t0) * 1000),
        "operational_summary": _operational_summary(ticks, ingest),
    }
    record_metric("batch_finished", {"succeeded": summary["succeeded"], "failed": summary["failed"]})
    return summary


def _operational_summary(ticks: list[dict], ingest: dict | None) -> str:
    lines = [
        f"Autonomous Scheduler batch @ {_now()}",
        f"Ingest queued: {(ingest or {}).get('queued_ok', 'n/a')}",
        f"Ticks: {len(ticks)}",
        f"Succeeded: {sum(1 for t in ticks if t.get('status') == 'succeeded')}",
        f"Failed/skipped: {sum(1 for t in ticks if t.get('status') == 'failed')}",
        f"Retry queued: {sum(1 for t in ticks if t.get('status') == 'retry_queued')}",
        "Publishing: prepared only when enabled; never auto-executed by scheduler.",
    ]
    return "\n".join(lines)
