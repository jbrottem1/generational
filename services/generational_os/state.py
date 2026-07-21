"""GenOS system state — SYSTEM_STATE.json + unified views."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.env import project_root

STATE_PATH = project_root() / "data" / "generational_os" / "SYSTEM_STATE.json"
HEALTH_MD = project_root() / "data" / "generational_os" / "SYSTEM_HEALTH.md"


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def build_system_state(*, publishing_enabled: bool = False) -> dict[str, Any]:
    """Unified GenOS state snapshot for observability."""
    from services.generational_os.dashboard import build_operating_dashboard
    from services.generational_os.departments import OPERATING_LOOP, department_health, list_departments
    from services.generational_os.resources import snapshot_resources
    from services.generational_os.scheduler import scheduler_dashboard

    sched = scheduler_dashboard()
    resources = snapshot_resources()
    deps = department_health()
    os_dash = build_operating_dashboard(include_genos=False)

    trending = []
    try:
        from services.trend_opportunity import list_opportunities

        trending = list_opportunities(limit=10)
    except Exception:  # noqa: BLE001
        trending = []

    pub_queue: dict[str, Any] = {"publishing_enabled": publishing_enabled}
    try:
        from services.production_operations.queue import queue_summary

        pub_queue["ops"] = queue_summary()
    except Exception:  # noqa: BLE001
        pass

    providers = []
    try:
        from services.trend_opportunity import list_provider_interfaces

        providers = list_provider_interfaces()
    except Exception:  # noqa: BLE001
        providers = []

    creative_avg = None
    try:
        from services.generational_os.learning_store import list_lessons

        scores = [float(l["creative_score"]) for l in list_lessons(40) if l.get("creative_score") is not None]
        if scores:
            creative_avg = round(sum(scores) / len(scores), 1)
    except Exception:  # noqa: BLE001
        creative_avg = (os_dash.get("metrics") or {}).get("average_qc_score")

    failed = sched.get("failed") or []
    health = "healthy"
    if len(failed) >= 3:
        health = "critical"
    elif failed or int(deps.get("available_count") or 0) < int(deps.get("total") or 1) // 2:
        health = "degraded"
    elif int((sched.get("ops_summary") or {}).get("failed") or 0) > 0:
        health = "degraded"

    throughput = {
        "completed_jobs": len(sched.get("completed") or []),
        "queued_jobs": len(sched.get("queued") or []),
        "estimated_productions_per_day": min(24, max(1, len(sched.get("completed") or []) + 2)),
    }

    return {
        "schema_version": 1,
        "os_name": "GenOS",
        "os_version": "1.0.0",
        "generated_at": _now(),
        "publishing_enabled": publishing_enabled,
        "system_health": health,
        "departments": list_departments(),
        "department_health": deps,
        "operating_loop": list(OPERATING_LOOP),
        "jobs": {
            "current": sched.get("current"),
            "queued": sched.get("queued"),
            "completed": sched.get("completed"),
            "failed": sched.get("failed"),
        },
        "trending_opportunities": [
            {
                "topic": t.get("topic"),
                "score": t.get("opportunity_score"),
                "status": t.get("current_status"),
                "priority": t.get("production_priority"),
            }
            for t in trending[:10]
        ],
        "publishing_queue": pub_queue,
        "platform_status": {"youtube_shorts": "ready", "publishing_enabled": publishing_enabled},
        "provider_status": providers,
        "analytics_summary": {
            "creative_excellence_average": creative_avg,
            "os_qc_average": (os_dash.get("metrics") or {}).get("average_qc_score"),
            "production_success_rate": (os_dash.get("metrics") or {}).get("production_success_rate"),
        },
        "creative_excellence_average": creative_avg,
        "resources": resources,
        "estimated_throughput": throughput,
        "legacy_os_dashboard": {
            "queues": os_dash.get("queues"),
            "metrics": os_dash.get("metrics"),
            "system_health": os_dash.get("system_health"),
        },
        "paths": {
            "system_state": str(STATE_PATH),
            "production_queue": str(project_root() / "data" / "generational_os" / "PRODUCTION_QUEUE.json"),
        },
    }


def write_system_state(*, publishing_enabled: bool = False) -> Path:
    state = build_system_state(publishing_enabled=publishing_enabled)
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, default=str) + "\n", encoding="utf-8")
    return STATE_PATH


def format_system_health_md(state: dict[str, Any] | None = None) -> str:
    state = state or build_system_state()
    lines = [
        "# SYSTEM_HEALTH",
        "",
        f"**Status:** {state.get('system_health')}",
        f"**Generated:** {state.get('generated_at')}",
        f"**Publishing enabled:** {state.get('publishing_enabled')}",
        "",
        "## Departments",
        "",
    ]
    dh = state.get("department_health") or {}
    lines.append(f"Available: {dh.get('available_count')}/{dh.get('total')}")
    for d in dh.get("departments") or []:
        mark = "OK" if d.get("available") else "DOWN"
        lines.append(f"- [{mark}] {d.get('label')}")
    jobs = state.get("jobs") or {}
    lines += [
        "",
        "## Jobs",
        "",
        f"- Current: {len(jobs.get('current') or [])}",
        f"- Queued: {len(jobs.get('queued') or [])}",
        f"- Completed: {len(jobs.get('completed') or [])}",
        f"- Failed: {len(jobs.get('failed') or [])}",
        "",
        f"Creative Excellence Avg: {state.get('creative_excellence_average')}",
        f"Throughput est./day: {(state.get('estimated_throughput') or {}).get('estimated_productions_per_day')}",
        "",
        "_GenOS — orchestration only; departments unchanged._",
        "",
    ]
    return "\n".join(lines)


def write_system_health(*, publishing_enabled: bool = False) -> Path:
    state = build_system_state(publishing_enabled=publishing_enabled)
    write_system_state(publishing_enabled=publishing_enabled)
    HEALTH_MD.parent.mkdir(parents=True, exist_ok=True)
    HEALTH_MD.write_text(format_system_health_md(state), encoding="utf-8")
    return HEALTH_MD
