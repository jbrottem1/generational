"""Acceptance dashboard + historical trend builder."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from services.production_acceptance.models import (
    DASHBOARD_PATH,
    AcceptanceRun,
    load_history,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_acceptance_dashboard(run: AcceptanceRun | None = None) -> dict[str, Any]:
    history = load_history(limit=50)
    current = run.summary() if run else (history[0] if history else {})
    # Trends: pass_pct and average_quality over time
    trend_pass = [{"run_id": h.get("run_id"), "at": h.get("finished_at") or h.get("started_at"), "pass_pct": h.get("pass_pct")} for h in reversed(history)]
    trend_quality = [
        {
            "run_id": h.get("run_id"),
            "at": h.get("finished_at") or h.get("started_at"),
            "average_quality": h.get("average_quality"),
            "average_render_time_ms": h.get("average_render_time_ms"),
        }
        for h in reversed(history)
    ]
    # Improvement delta vs previous
    improvement = None
    if len(history) >= 2:
        a, b = history[0], history[1]
        improvement = {
            "pass_pct_delta": round(float(a.get("pass_pct") or 0) - float(b.get("pass_pct") or 0), 1),
            "quality_delta": round(float(a.get("average_quality") or 0) - float(b.get("average_quality") or 0), 1),
            "render_ms_delta": int(float(a.get("average_render_time_ms") or 0) - float(b.get("average_render_time_ms") or 0)),
        }

    dash = {
        "generated_at": _now(),
        "version": (run.version if run else current.get("version") or "1.0.0"),
        "pass_pct": current.get("pass_pct", 0),
        "failure_pct": current.get("failure_pct", 0),
        "average_quality": current.get("average_quality", 0),
        "average_render_time": current.get("average_render_time_ms", 0),
        "fastest_render": current.get("fastest_render_ms", 0),
        "slowest_render": current.get("slowest_render_ms", 0),
        "common_failures": current.get("common_failures") or [],
        "recovery_success": current.get("recovery_success_pct", 100.0),
        "latest_run_id": current.get("run_id"),
        "latest_mode": current.get("mode"),
        "latest_ok": current.get("ok"),
        "history_count": len(history),
        "trends": {
            "pass_pct": trend_pass,
            "quality": trend_quality,
            "improvement_vs_previous": improvement,
        },
        "category_breakdown": _category_breakdown(run) if run else {},
    }
    DASHBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    DASHBOARD_PATH.write_text(json.dumps(dash, indent=2), encoding="utf-8")
    return dash


def _category_breakdown(run: AcceptanceRun) -> dict[str, Any]:
    buckets: dict[str, dict[str, int]] = {}
    for r in run.results:
        b = buckets.setdefault(r.category, {"passed": 0, "failed": 0, "total": 0})
        b["total"] += 1
        if r.passed:
            b["passed"] += 1
        else:
            b["failed"] += 1
    for b in buckets.values():
        b["pass_pct"] = round(100.0 * b["passed"] / b["total"], 1) if b["total"] else 0
    return buckets
