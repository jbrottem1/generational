"""GenOS — Generational Operating System orchestrator (Agent 0 executive loop).

Composes existing departments. Does not redesign the pipeline or add engines.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from services.generational_os.learning_store import extract_lesson_from_ops_result
from services.generational_os.reports_os import generate_all_reports
from services.generational_os.resources import record_production_resources
from services.generational_os.scheduler import run_next_job, schedule_production, scheduler_dashboard
from services.generational_os.state import build_system_state, write_system_state
from services.trend_opportunity.brief import to_studio_brief_kwargs

# Soft façade: Autonomous Scheduler composes GenOS without replacing this cycle.


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_operating_cycle(
    *,
    category: str = "science",
    subject: str = "science education",
    queue_count: int = 5,
    execute_one: bool = True,
    publishing_enabled: bool = False,
    top_n: int = 25,
) -> dict[str, Any]:
    """
    One GenOS operating cycle:

    Trend → select → brief → queue N → optionally execute one via Production Operations
    → QA/package (inside ops) → audience/lessons → update library → reports.

    Publishing remains disabled unless publishing_enabled=True.
    """
    t0 = time.time()
    log: list[dict[str, Any]] = []

    def step(name: str, **payload: Any) -> None:
        log.append({"step": name, "at": _now(), **payload})

    # 1) Discover opportunities
    import services.trend_opportunity as trend_opportunity

    trends = trend_opportunity.run_trend_opportunity(
        subject,
        category=category,
        top_n=top_n,
        brief_count=max(10, queue_count),
        high_confidence_count=5,
        persist=True,
        write_reports=True,
    )
    top = list(trends.get("top_opportunities") or [])
    step("check_trend_intelligence", ranked=len(top))
    if not top:
        return {"ok": False, "error": "no_opportunities", "log": log}

    # 2) Select highest-priority + queue
    queued = []
    for i, opp in enumerate(top[:queue_count]):
        brief = opp.get("production_brief") or {}
        kwargs = to_studio_brief_kwargs(brief)
        priority = int(opp.get("production_priority") or (100 - i))
        cons = dict(kwargs.get("constraints") or {})
        cons["publishing_enabled"] = bool(publishing_enabled)
        cons["from_genos"] = True
        result = schedule_production(
            topic=str(kwargs.get("topic") or opp.get("topic") or ""),
            platform=str(kwargs.get("platform") or "youtube_shorts"),
            length_sec=int(kwargs.get("length_sec") or 45),
            style=str(kwargs.get("style") or "educational"),
            narrator=str(kwargs.get("narrator") or "professor"),
            command=str(kwargs.get("command") or ""),
            priority=priority,
            constraints=cons,
            production_brief=brief,
            run_immediately=False,
            allow_duplicate=False,
        )
        queued.append(result)
        step("queue_production", topic=opp.get("topic"), ok=result.get("ok"), job=result.get("job"))

    step("select_opportunity", topic=(top[0] or {}).get("topic"), score=(top[0] or {}).get("overall_opportunity_score"))

    # 3) Execute one complete production (Agent 0 ops path)
    execution = None
    lesson = None
    if execute_one:
        # Prefer running #1 immediately via studio ops for a complete cycle
        number_one = top[0]
        brief = number_one.get("production_brief") or {}
        kwargs = to_studio_brief_kwargs(brief)
        cons = dict(kwargs.get("constraints") or {})
        cons["publishing_enabled"] = False  # self-test / default OS policy
        cons["from_genos"] = True
        from services.production_operations import run_studio_ops

        step("launch_research_through_export", note="delegated_to_run_studio_ops")
        ops = run_studio_ops(
            topic=str(kwargs.get("topic") or number_one.get("topic") or ""),
            platform=str(kwargs.get("platform") or "youtube_shorts"),
            length_sec=int(kwargs.get("length_sec") or 45),
            style=str(kwargs.get("style") or "educational"),
            narrator=str(kwargs.get("narrator") or "professor"),
            command=str(kwargs.get("command") or ""),
            constraints=cons,
            context={
                "trend_opportunity_brief": brief,
                "publishing_enabled": False,
                "genos_cycle": True,
            },
        )
        execution = {
            "production_id": ops.get("production_id") or (ops.get("status") or {}).get("production_id"),
            "success": ops.get("success") or (ops.get("status") or {}).get("success"),
            "status": ops.get("status"),
            "report_keys": list((ops.get("report") or {}).keys())[:20] if isinstance(ops.get("report"), dict) else [],
        }
        step("execute_production", **{k: execution.get(k) for k in ("production_id", "success")})

        # Resources + lesson
        elapsed_ms = int((time.time() - t0) * 1000)
        record_production_resources(
            str(execution.get("production_id") or "unknown"),
            length_sec=int(kwargs.get("length_sec") or 45),
            processing_ms=elapsed_ms,
            elevenlabs_present=True,
        )
        lesson = extract_lesson_from_ops_result(
            ops if isinstance(ops, dict) else {},
            topic=str(number_one.get("topic") or ""),
            trend_score=float(number_one.get("overall_opportunity_score") or 0),
        )
        step("store_lessons_learned", lesson=lesson.get("highest_impact_lesson"))

        # Soft: update opportunity library status via upsert
        try:
            from services.trend_opportunity import upsert_opportunity

            upsert_opportunity(
                {
                    **number_one,
                    "status": "in_production" if execution.get("success") else "ranked",
                    "previous_productions": [{"production_id": execution.get("production_id"), "at": _now()}],
                }
            )
            step("update_opportunity_library", ok=True)
        except Exception as exc:  # noqa: BLE001
            step("update_opportunity_library", ok=False, error=str(exc)[:120])

    # 4) Reports (publishing disabled)
    report_paths = generate_all_reports(publishing_enabled=publishing_enabled)
    state_path = write_system_state(publishing_enabled=publishing_enabled)
    step("generate_operations_report", paths=report_paths)

    return {
        "ok": True,
        "generated_at": _now(),
        "publishing_enabled": publishing_enabled,
        "opportunities_ranked": len(top),
        "queued": queued,
        "queued_ok_count": sum(1 for q in queued if q.get("ok")),
        "execution": execution,
        "lesson": lesson,
        "scheduler": scheduler_dashboard(),
        "system_state_path": str(state_path),
        "report_paths": report_paths,
        "log": log,
        "elapsed_ms": int((time.time() - t0) * 1000),
        "note": "GenOS composed Trend Intelligence + Production Operations; publishing disabled unless enabled",
    }


def simulate_operating_day(
    *,
    category: str = "science",
    queue_count: int = 5,
    execute_one: bool = True,
) -> dict[str, Any]:
    """Self-test: discover, queue five, execute one, QA/package inside ops, report. Publishing off."""
    return run_operating_cycle(
        category=category,
        subject=f"{category} education",
        queue_count=queue_count,
        execute_one=execute_one,
        publishing_enabled=False,
        top_n=25,
    )


def build_genos_dashboard(*, publishing_enabled: bool = False) -> dict[str, Any]:
    """Operations dashboard payload for Studio / CLI."""
    state = build_system_state(publishing_enabled=publishing_enabled)
    sched = scheduler_dashboard()
    return {
        "title": "Generational Operating System",
        "generated_at": state.get("generated_at"),
        "system_health": state.get("system_health"),
        "current_jobs": sched.get("current"),
        "queued_jobs": sched.get("queued"),
        "completed_jobs": sched.get("completed"),
        "failed_jobs": sched.get("failed"),
        "trending_opportunities": state.get("trending_opportunities"),
        "publishing_queue": state.get("publishing_queue"),
        "platform_status": state.get("platform_status"),
        "provider_status": state.get("provider_status"),
        "analytics_summary": state.get("analytics_summary"),
        "creative_excellence_average": state.get("creative_excellence_average"),
        "system_health_detail": state.get("department_health"),
        "estimated_throughput": state.get("estimated_throughput"),
        "resources": state.get("resources"),
        "operating_loop": state.get("operating_loop"),
        "departments": state.get("departments"),
    }
