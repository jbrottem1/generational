"""GCIS — Generational Continuous Improvement System helpers.

Additive ops layer. Does not modify Orchestrator or production pipeline.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
GCIS_DIR = ROOT / "data" / "gcis"
DASHBOARD_PATH = GCIS_DIR / "dashboard.json"
REVIEWS_DIR = GCIS_DIR / "reviews"
VALIDATION_DIR = ROOT / "data" / "productions" / "_validation"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_dashboard() -> dict[str, Any]:
    if DASHBOARD_PATH.exists():
        return json.loads(DASHBOARD_PATH.read_text(encoding="utf-8"))
    return {"system": "GCIS", "metrics": {}}


def save_dashboard(data: dict[str, Any]) -> Path:
    GCIS_DIR.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _utc_now()
    DASHBOARD_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return DASHBOARD_PATH


def collect_validation_summaries() -> list[dict[str, Any]]:
    """Scan validation reports for completed series."""
    summaries: list[dict[str, Any]] = []
    if not VALIDATION_DIR.exists():
        return summaries
    for path in sorted(VALIDATION_DIR.rglob("*REPORT*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        completed = data.get("completed")
        requested = data.get("requested")
        success = data.get("success")
        summaries.append(
            {
                "report": str(path.relative_to(ROOT)),
                "series": data.get("series") or data.get("project") or path.parent.name,
                "completed": completed,
                "requested": requested,
                "success": success,
                "batch_runtime_sec": data.get("batch_runtime_sec"),
                "generated_at": data.get("generated_at"),
            }
        )
    return summaries


def refresh_dashboard_from_validation() -> dict[str, Any]:
    """Update dashboard counters from validation reports (best-effort)."""
    dash = load_dashboard()
    metrics = dict(dash.get("metrics") or {})
    summaries = collect_validation_summaries()
    ok_series = [s for s in summaries if s.get("success") is True]
    metrics["validation_reports_scanned"] = len(summaries)
    metrics["successful_series_reports"] = len(ok_series)
    # Prefer latest biology batch timing if present
    for s in reversed(summaries):
        if s.get("batch_runtime_sec") and "biology" in str(s.get("series") or "").lower():
            metrics["avg_series_batch_runtime_sec"] = s["batch_runtime_sec"]
            break
    metrics["gcis_active"] = True
    metrics["generational_method_active"] = True
    dash["metrics"] = metrics
    dash["validation_summaries"] = summaries[-12:]
    dash["tracks"] = dict(dash.get("tracks") or {})
    dash["tracks"]["D_gcis"] = "established"
    save_dashboard(dash)
    return dash


def write_review(slug: str, payload: dict[str, Any]) -> Path:
    """Write a structured post-production review JSON (+ optional markdown body)."""
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    payload = dict(payload)
    payload.setdefault("system", "GCIS")
    payload["written_at"] = _utc_now()
    path = REVIEWS_DIR / f"{slug}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path
