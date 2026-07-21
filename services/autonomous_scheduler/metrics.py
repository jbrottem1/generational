"""Durable production metrics for the Autonomous Production Scheduler."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.env import project_root

ROOT = project_root() / "data" / "autonomous_scheduler"
METRICS_PATH = ROOT / "METRICS.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_metric(event: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    ROOT.mkdir(parents=True, exist_ok=True)
    row = {"at": _now(), "event": event, **(payload or {})}
    with METRICS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")
    return row


def load_metrics(*, limit: int = 500) -> list[dict[str, Any]]:
    if not METRICS_PATH.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in METRICS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows[-limit:]


def summarize_metrics(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = rows if rows is not None else load_metrics()
    completed = [r for r in rows if r.get("event") == "production_completed"]
    failed = [r for r in rows if r.get("event") == "production_failed"]
    durations = [int(r.get("elapsed_ms") or 0) for r in completed if r.get("elapsed_ms")]
    qualities = [
        float(r["quality_score"])
        for r in completed
        if r.get("quality_score") is not None
    ]
    total_finish = len(completed) + len(failed)
    return {
        "events": len(rows),
        "completed": len(completed),
        "failed": len(failed),
        "average_render_time_ms": int(sum(durations) / len(durations)) if durations else 0,
        "average_quality": round(sum(qualities) / len(qualities), 1) if qualities else 0.0,
        "production_success_rate": round(100.0 * len(completed) / total_finish, 1) if total_finish else 0.0,
        "path": str(METRICS_PATH),
    }
