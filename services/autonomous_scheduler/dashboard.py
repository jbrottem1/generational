"""Operational dashboard for Autonomous Production Scheduler."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from core.env import project_root
from services.autonomous_scheduler.metrics import summarize_metrics
from services.generational_os.scheduler import scheduler_dashboard

ROOT = project_root() / "data" / "autonomous_scheduler"
DASH_JSON = ROOT / "SCHEDULER_DASHBOARD.json"
DASH_MD = project_root() / "AUTONOMOUS_SCHEDULER_DASHBOARD.md"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def build_scheduler_dashboard() -> dict[str, Any]:
    sched = scheduler_dashboard()
    metrics = summarize_metrics()
    all_jobs = (
        list(sched.get("waiting") or [])
        + list(sched.get("retry_queue") or [])
        + list(sched.get("current") or [])
        + list(sched.get("completed") or [])
        + list(sched.get("failed") or [])
    )
    # Prefer complete job list from GenOS queue file
    try:
        from services.generational_os.scheduler import list_genos_jobs

        all_jobs = list_genos_jobs()
    except Exception:  # noqa: BLE001
        pass

    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    completed = [j for j in all_jobs if j.get("status") == "succeeded"]
    today = [
        j
        for j in completed
        if (ts := _parse_ts(j.get("completion_time"))) and ts >= day_ago
    ]
    week = [
        j
        for j in completed
        if (ts := _parse_ts(j.get("completion_time"))) and ts >= week_ago
    ]

    qualities = [
        float(j["quality_score"])
        for j in completed
        if j.get("quality_score") is not None
    ]
    # Render time from start→completion when present
    render_ms: list[int] = []
    for j in completed:
        start = _parse_ts(j.get("start_time"))
        end = _parse_ts(j.get("completion_time"))
        if start and end and end >= start:
            render_ms.append(int((end - start).total_seconds() * 1000))

    finished = len(completed) + len(sched.get("failed") or [])
    success_rate = round(100.0 * len(completed) / finished, 1) if finished else float(
        metrics.get("production_success_rate") or 0
    )

    trend_top = []
    try:
        from services.trend_opportunity.library import list_opportunities

        ranked = list_opportunities(limit=8) or []
        trend_top = [
            {
                "topic": r.get("topic"),
                "score": r.get("overall_opportunity_score"),
                "priority": r.get("production_priority"),
                "status": r.get("status"),
            }
            for r in ranked
            if isinstance(r, dict)
        ]
    except Exception:  # noqa: BLE001
        trend_top = []

    dash = {
        "title": "Autonomous Production Scheduler",
        "generated_at": _now(),
        "architecture_frozen": True,
        "publishing_default": False,
        "jobs_waiting": int(sched.get("jobs_waiting") or 0),
        "jobs_running": int(sched.get("jobs_running") or 0),
        "jobs_completed": int(sched.get("jobs_completed") or 0),
        "failed_jobs": int(sched.get("jobs_failed") or 0),
        "retry_queue": int(sched.get("jobs_retry") or 0),
        "average_render_time_ms": int(sum(render_ms) / len(render_ms)) if render_ms else int(
            metrics.get("average_render_time_ms") or 0
        ),
        "average_quality": round(sum(qualities) / len(qualities), 1) if qualities else float(
            metrics.get("average_quality") or 0
        ),
        "production_success_rate": success_rate,
        "todays_output": len(today),
        "weekly_output": len(week),
        "waiting": sched.get("waiting") or [],
        "running": sched.get("current") or [],
        "completed_recent": completed[:15],
        "failed_recent": list(sched.get("failed") or [])[:10],
        "retry_jobs": sched.get("retry_queue") or [],
        "trend_rankings_top": trend_top,
        "metrics": metrics,
        "genos_queue_path": sched.get("path"),
        "workflow": [
            "Trend Intelligence",
            "Production Queue",
            "GenOS Scheduler",
            "Research → Psychology → Script → Scene → World → Assets → Voice → Director → Render → QA",
            "Library",
            "Publishing Queue (disabled unless enabled)",
        ],
    }
    return dash


def write_scheduler_dashboard(dash: dict[str, Any] | None = None) -> dict[str, str]:
    dash = dash or build_scheduler_dashboard()
    ROOT.mkdir(parents=True, exist_ok=True)
    DASH_JSON.write_text(json.dumps(dash, indent=2, default=str) + "\n", encoding="utf-8")

    md = [
        "# Autonomous Production Scheduler Dashboard",
        "",
        f"Generated: `{dash.get('generated_at')}`",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Jobs waiting | {dash.get('jobs_waiting')} |",
        f"| Jobs running | {dash.get('jobs_running')} |",
        f"| Jobs completed | {dash.get('jobs_completed')} |",
        f"| Failed jobs | {dash.get('failed_jobs')} |",
        f"| Retry queue | {dash.get('retry_queue')} |",
        f"| Avg render time (ms) | {dash.get('average_render_time_ms')} |",
        f"| Avg quality | {dash.get('average_quality')} |",
        f"| Production success rate | {dash.get('production_success_rate')}% |",
        f"| Today's output | {dash.get('todays_output')} |",
        f"| Weekly output | {dash.get('weekly_output')} |",
        "",
        "## Workflow",
        "",
    ]
    for step in dash.get("workflow") or []:
        md.append(f"- {step}")
    md.extend(["", f"JSON: `{DASH_JSON}`", ""])
    DASH_MD.write_text("\n".join(md), encoding="utf-8")
    return {"json": str(DASH_JSON), "markdown": str(DASH_MD)}
