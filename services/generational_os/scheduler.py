"""GenOS production scheduler — façade over core.jobs + production_operations queue."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.env import project_root
from core.jobs import JobStatus, get_queue
from services.generational_os.errors import classify_error, should_retry
from services.production_operations.queue import (
    OPS_JOB_TYPE,
    enqueue_production,
    ensure_ops_queue_handler,
    queue_summary,
)

GENOS_QUEUE = project_root() / "data" / "generational_os" / "PRODUCTION_QUEUE.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fingerprint(topic: str, platform: str) -> str:
    return hashlib.sha256(f"{platform}::{topic.strip().lower()}".encode()).hexdigest()[:16]


def _load_queue() -> dict[str, Any]:
    if not GENOS_QUEUE.exists():
        return {"jobs": [], "updated_at": _now()}
    try:
        return json.loads(GENOS_QUEUE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"jobs": [], "updated_at": _now()}


def _save_queue(data: dict[str, Any]) -> None:
    GENOS_QUEUE.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _now()
    GENOS_QUEUE.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")


def _upsert_job(row: dict[str, Any]) -> None:
    data = _load_queue()
    jobs = [j for j in (data.get("jobs") or []) if j.get("job_id") != row.get("job_id")]
    jobs.append(row)
    jobs.sort(key=lambda j: (-int(j.get("priority") or 0), j.get("created_at") or ""))
    data["jobs"] = jobs[-300:]
    _save_queue(data)


def list_genos_jobs(*, status: str = "") -> list[dict[str, Any]]:
    jobs = list((_load_queue().get("jobs") or []))
    if status:
        jobs = [j for j in jobs if j.get("status") == status]
    return jobs


def has_duplicate(topic: str, platform: str = "youtube_shorts") -> dict[str, Any] | None:
    """Prevent duplicate work for same topic/platform while pending/running."""
    fp = _fingerprint(topic, platform)
    for j in list_genos_jobs():
        if j.get("fingerprint") != fp:
            continue
        if j.get("status") in (JobStatus.PENDING, JobStatus.RUNNING, "queued", "retry_queued"):
            return j
    return None

def schedule_production(
    *,
    topic: str,
    platform: str = "youtube_shorts",
    length_sec: int = 45,
    style: str = "educational",
    narrator: str = "professor",
    command: str = "",
    priority: int = 50,
    category: str = "",
    target_channel: str = "",
    world: str = "",
    constraints: dict | None = None,
    production_brief: dict | None = None,
    run_immediately: bool = False,
    allow_duplicate: bool = False,
) -> dict[str, Any]:
    """Queue a production job with GenOS metadata (priority, stage, ETA)."""
    ensure_ops_queue_handler()
    dup = None if allow_duplicate else has_duplicate(topic, platform)
    if dup:
        return {
            "ok": False,
            "duplicate": True,
            "existing_job": dup,
            "message": "Duplicate work prevented — identical topic/platform already queued or running",
        }

    cons = dict(constraints or {})
    cons.setdefault("publishing_enabled", False)
    cons.setdefault("from_genos", True)
    brief = production_brief if isinstance(production_brief, dict) else {}
    world_val = world or str(
        (brief.get("world_selection") or {}).get("world_id")
        if isinstance(brief.get("world_selection"), dict)
        else brief.get("world_selection") or cons.get("world") or ""
    )
    category_val = category or str(brief.get("category") or cons.get("category") or "")
    channel_val = target_channel or str(
        cons.get("target_channel") or cons.get("channel_id") or brief.get("target_channel") or ""
    )
    if brief:
        cons["trend_opportunity_brief"] = {
            "topic": brief.get("topic"),
            "hook": brief.get("hook"),
            "world_selection": brief.get("world_selection"),
            "overall_opportunity_score": brief.get("overall_opportunity_score"),
        }
    if category_val:
        cons.setdefault("category", category_val)
    if channel_val:
        cons.setdefault("target_channel", channel_val)
    if world_val:
        cons.setdefault("world", world_val)

    enq = enqueue_production(
        topic=topic,
        platform=platform,
        length_sec=length_sec,
        style=style,
        narrator=narrator,
        command=command,
        priority=priority,
        constraints=cons,
        run_immediately=run_immediately,
    )
    job_id = str(enq.get("job_id") or "")
    status = str(enq.get("status") or JobStatus.PENDING)
    row = {
        "job_id": job_id,
        "topic": topic,
        "category": category_val,
        "priority": int(priority),
        "target_channel": channel_val,
        "narrator": narrator,
        "world": world_val,
        "estimated_duration_sec": int(length_sec),
        "length_sec": int(length_sec),
        "platform": platform,
        "style": style,
        "status": status if status != "scheduled" else "queued",
        "retry_count": 0,
        "creation_time": _now(),
        "start_time": _now() if run_immediately else None,
        "completion_time": None,
        "failure_reason": "",
        "quality_score": None,
        "current_stage": "queued" if not run_immediately else "running",
        "estimated_time_remaining_sec": max(60, length_sec * 8),
        "fingerprint": _fingerprint(topic, platform),
        "production_id": (enq.get("result") or {}).get("production_id") if isinstance(enq.get("result"), dict) else None,
        "error": enq.get("error"),
        "publishing_enabled": bool(cons.get("publishing_enabled")),
        "attempts": 0,
    }
    if run_immediately and status == JobStatus.SUCCEEDED:
        result = enq.get("result") if isinstance(enq.get("result"), dict) else {}
        report = result.get("report") if isinstance(result.get("report"), dict) else {}
        row["completion_time"] = _now()
        row["current_stage"] = "completed"
        row["estimated_time_remaining_sec"] = 0
        row["quality_score"] = report.get("overall_quality_score") or report.get("creative_excellence_score")
        row["production_id"] = result.get("production_id") or row.get("production_id")
    elif run_immediately and status == JobStatus.FAILED:
        row["completion_time"] = _now()
        row["current_stage"] = "failed"
        row["failure_reason"] = str(enq.get("error") or "run_failed")[:400]
        row["classification"] = classify_error(enq.get("error"))
    _upsert_job(row)
    return {"ok": True, "duplicate": False, "job": row, "enqueue": enq}


def _rehydrate_ops_job(target: dict[str, Any]) -> str:
    """Rebuild an in-memory core.jobs entry from durable GenOS metadata.

    JobQueue is process-local; GenOS JSON is the durable source of truth across
    CLI invocations / autonomous ticks.
    """
    ensure_ops_queue_handler()
    queue = get_queue()
    job_id = str(target.get("job_id") or "")
    if job_id and queue.get(job_id) is not None:
        return job_id

    cons = {
        "publishing_enabled": bool(target.get("publishing_enabled")),
        "from_genos": True,
        "from_autonomous_scheduler": True,
        "category": target.get("category") or "",
        "target_channel": target.get("target_channel") or "",
        "world": target.get("world") or "",
    }
    enq = enqueue_production(
        topic=str(target.get("topic") or ""),
        platform=str(target.get("platform") or "youtube_shorts"),
        length_sec=int(target.get("length_sec") or target.get("estimated_duration_sec") or 45),
        style=str(target.get("style") or "educational"),
        narrator=str(target.get("narrator") or "professor"),
        priority=int(target.get("priority") or 50),
        resume_production_id=str(target.get("production_id") or ""),
        run_immediately=False,
        constraints=cons,
    )
    new_id = str(enq.get("job_id") or "")
    if new_id:
        if job_id and job_id != new_id:
            target["prior_job_id"] = job_id
        target["job_id"] = new_id
        target["status"] = JobStatus.PENDING
        _upsert_job(target)
    return new_id


def run_next_job(*, max_retries: int = 2) -> dict[str, Any] | None:
    """Run the highest-priority pending GenOS/ops job sequentially."""
    ensure_ops_queue_handler()
    queue = get_queue()

    # Recover stale "running" rows left by crashed ticks (no live job)
    for stale in list_genos_jobs():
        if stale.get("status") != JobStatus.RUNNING:
            continue
        live_id = str(stale.get("job_id") or "")
        if live_id and queue.get(live_id) is not None:
            continue
        stale["status"] = JobStatus.PENDING
        stale["current_stage"] = "queued"
        stale["failure_reason"] = stale.get("failure_reason") or "recovered_stale_running"
        _upsert_job(stale)

    # Prefer GenOS tracked pending sorted by priority
    pending = [j for j in list_genos_jobs() if j.get("status") in (JobStatus.PENDING, "queued")]
    pending.sort(key=lambda j: (-int(j.get("priority") or 0), j.get("creation_time") or ""))
    if not pending:
        job = queue.run_next()
        if not job:
            return None
        return {"job_id": job.id, "status": job.status, "error": job.error, "result": job.result}

    target = pending[0]
    job_id = _rehydrate_ops_job(target)
    if not job_id:
        target["status"] = JobStatus.FAILED
        target["failure_reason"] = "rehydrate_failed"
        target["completion_time"] = _now()
        _upsert_job(target)
        return {"job_id": "", "status": JobStatus.FAILED, "error": "rehydrate_failed", "job": target}

    # Reload after possible job_id rewrite
    target = next((j for j in list_genos_jobs() if j.get("job_id") == job_id), target)
    target["status"] = JobStatus.RUNNING
    target["current_stage"] = "production_operations"
    target["start_time"] = target.get("start_time") or _now()
    _upsert_job(target)

    attempt = int(target.get("attempts") or 0)
    finished = queue.run(job_id)
    attempt += 1
    target["attempts"] = attempt
    target["retry_count"] = max(0, attempt - 1)

    if finished.status == JobStatus.SUCCEEDED:
        result = finished.result if isinstance(finished.result, dict) else {}
        report = result.get("report") if isinstance(result.get("report"), dict) else {}
        status_block = result.get("status") if isinstance(result.get("status"), dict) else {}
        # Honest deliverable: treat missing MP4 as failed for GenOS metrics
        video_ok = bool(
            result.get("video_exists")
            or status_block.get("video_exists")
            or result.get("success")
            or status_block.get("success")
        )
        target["production_id"] = result.get("production_id") or status_block.get("production_id")
        target["quality_score"] = (
            report.get("overall_quality_score")
            or report.get("creative_excellence_score")
            or status_block.get("validation_score")
        )
        target["error"] = ""
        target["failure_reason"] = "" if video_ok else "mp4_missing"
        target["completion_time"] = _now()
        target["estimated_time_remaining_sec"] = 0
        if video_ok:
            target["status"] = JobStatus.SUCCEEDED
            target["current_stage"] = "completed"
        else:
            target["status"] = JobStatus.FAILED
            target["current_stage"] = "failed"
            target["failure_reason"] = "mp4_missing — pipeline finished without deliverable"
        _upsert_job(target)
        return {
            "job_id": job_id,
            "status": target["status"],
            "result": finished.result,
            "job": target,
            "video_exists": video_ok,
        }

    classification = classify_error(finished.error, context={"job_id": job_id, "stage": "production_operations"})
    target["classification"] = classification
    target["error"] = finished.error
    target["failure_reason"] = str(finished.error or classification.get("message") or "unknown")[:400]
    if should_retry(classification, attempt=attempt, max_attempts=max_retries):
        topic = target.get("topic") or ""
        enq = enqueue_production(
            topic=topic,
            platform=str(target.get("platform") or "youtube_shorts"),
            length_sec=int(target.get("length_sec") or target.get("estimated_duration_sec") or 45),
            style=str(target.get("style") or "educational"),
            narrator=str(target.get("narrator") or "professor"),
            priority=int(target.get("priority") or 50),
            resume_production_id=str(target.get("production_id") or ""),
            run_immediately=False,
            constraints={
                "publishing_enabled": bool(target.get("publishing_enabled")),
                "from_genos_retry": True,
                "category": target.get("category") or "",
                "target_channel": target.get("target_channel") or "",
                "world": target.get("world") or "",
            },
        )
        # Track retry under the new ops job id while preserving GenOS row linkage
        target["status"] = "retry_queued"
        target["current_stage"] = "retry_queued"
        target["retry_job_id"] = enq.get("job_id")
        target["retry_count"] = int(target.get("retry_count") or 0) + 1
        # Keep original pending drainability: swap job_id to new enqueue when available
        new_id = str(enq.get("job_id") or "")
        if new_id:
            target["prior_job_id"] = job_id
            target["job_id"] = new_id
            target["status"] = JobStatus.PENDING
        _upsert_job(target)
        return {
            "job_id": target["job_id"],
            "status": "retry_queued",
            "classification": classification,
            "enqueue": enq,
            "job": target,
        }

    # Unrecoverable — skip / fail without further automation
    target["status"] = JobStatus.FAILED
    target["completion_time"] = _now()
    target["current_stage"] = "skipped_unrecoverable" if not classification.get("retryable") else "failed"
    _upsert_job(target)
    return {
        "job_id": job_id,
        "status": JobStatus.FAILED,
        "error": finished.error,
        "classification": classification,
        "escalate": classification.get("escalate"),
        "skipped_unrecoverable": not bool(classification.get("retryable")),
        "job": target,
    }


def scheduler_dashboard() -> dict[str, Any]:
    jobs = list_genos_jobs()
    waiting = [j for j in jobs if j.get("status") in (JobStatus.PENDING, "queued")]
    retry_q = [j for j in jobs if j.get("status") == "retry_queued" or j.get("current_stage") == "retry_queued"]
    running = [j for j in jobs if j.get("status") == JobStatus.RUNNING]
    completed = [j for j in jobs if j.get("status") == JobStatus.SUCCEEDED]
    failed = [j for j in jobs if j.get("status") == JobStatus.FAILED]
    return {
        "current": running,
        "queued": waiting + retry_q,
        "waiting": waiting,
        "retry_queue": retry_q,
        "completed": completed,
        "failed": failed,
        "jobs_waiting": len(waiting),
        "jobs_running": len(running),
        "jobs_completed": len(completed),
        "jobs_failed": len(failed),
        "jobs_retry": len(retry_q),
        "ops_summary": queue_summary(),
        "path": str(GENOS_QUEUE),
    }
