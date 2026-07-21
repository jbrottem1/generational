"""Live Production Operations status + dashboard JSON."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.production_operations.stages import OPERATIONS_STAGES, STAGE_KEYS

ROOT = Path(__file__).resolve().parents[2]
OPS_ROOT = ROOT / "data" / "productions" / "_ops"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ops_dir(production_id: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in production_id)[:80]
    path = OPS_ROOT / safe
    path.mkdir(parents=True, exist_ok=True)
    return path


def status_path(production_id: str) -> Path:
    return ops_dir(production_id) / "PRODUCTION_OPS_STATUS.json"


def dashboard_path() -> Path:
    OPS_ROOT.mkdir(parents=True, exist_ok=True)
    return OPS_ROOT / "PRODUCTION_DASHBOARD.json"


def new_ops_status(production_id: str, brief: dict) -> dict[str, Any]:
    stages = []
    for spec in OPERATIONS_STAGES:
        stages.append(
            {
                "key": spec["key"],
                "label": spec["label"],
                "engines": list(spec.get("engines") or []),
                "status": "pending",
                "start_time": None,
                "end_time": None,
                "duration_ms": 0,
                "warnings": [],
                "errors": [],
                "retry_attempts": 0,
                "quality_score": 0,
                "output_files": [],
                "current_agent": None,
            }
        )
    return {
        "schema_version": "1.0",
        "production_id": production_id,
        "brief": brief,
        "current_stage": None,
        "current_agent": None,
        "overall_progress_pct": 0,
        "elapsed_ms": 0,
        "eta_ms": None,
        "overall_status": "pending",
        "pipeline_health": "healthy",
        "warnings": [],
        "retry_count": 0,
        "quality_scores": {},
        "current_files": [],
        "started_at": _now(),
        "finished_at": None,
        "stages": stages,
        "updated_at": _now(),
    }


def write_ops_status(production_id: str, status: dict) -> Path:
    status = dict(status)
    status["updated_at"] = _now()
    path = status_path(production_id)
    path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    return path


def load_ops_status(production_id: str) -> dict | None:
    path = status_path(production_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _progress(status: dict) -> int:
    stages = status.get("stages") or []
    if not stages:
        return 0
    done = sum(1 for s in stages if s.get("status") in ("succeeded", "skipped", "degraded", "partial", "failed"))
    return int(round(100 * done / len(stages)))


def update_stage(
    status: dict,
    stage_key: str,
    *,
    phase: str,
    duration_ms: int = 0,
    warnings: list | None = None,
    errors: list | None = None,
    retries: int = 0,
    quality_score: float = 0,
    output_files: list | None = None,
    current_agent: str | None = None,
    stage_status: str | None = None,
    engine_results: list | None = None,
    artifacts: list | None = None,
    failure_reason: str = "",
    inputs_received: list | None = None,
    outputs_produced: list | None = None,
    dependency_health: dict | None = None,
) -> dict:
    status = dict(status)
    status["current_stage"] = stage_key
    status["current_agent"] = current_agent
    for stage in status.get("stages") or []:
        if stage["key"] != stage_key:
            continue
        if phase == "start":
            stage["status"] = "running"
            stage["start_time"] = _now()
            stage["current_agent"] = current_agent
            status["overall_status"] = "running"
            if inputs_received is not None:
                stage["inputs_received"] = list(inputs_received)
        else:
            stage["status"] = stage_status or "succeeded"
            stage["end_time"] = _now()
            stage["duration_ms"] = int(duration_ms)
            stage["warnings"] = list(warnings or [])
            stage["errors"] = list(errors or [])
            stage["retry_attempts"] = int(retries)
            stage["quality_score"] = float(quality_score)
            stage["output_files"] = list(output_files or [])
            stage["current_agent"] = current_agent
            if engine_results is not None:
                stage["engine_results"] = list(engine_results)
            if artifacts is not None:
                stage["artifacts"] = list(artifacts)
            if outputs_produced is not None:
                stage["outputs_produced"] = list(outputs_produced)
            if failure_reason:
                stage["failure_reason"] = failure_reason
            if dependency_health is not None:
                stage["dependency_health"] = dict(dependency_health)
        break

    status["overall_progress_pct"] = _progress(status)
    status["elapsed_ms"] = sum(int(s.get("duration_ms") or 0) for s in (status.get("stages") or []))
    status["retry_count"] = sum(int(s.get("retry_attempts") or 0) for s in (status.get("stages") or []))
    all_warnings = []
    for s in status.get("stages") or []:
        all_warnings.extend(s.get("warnings") or [])
    status["warnings"] = all_warnings[-50:]
    # ETA: remaining stages × rolling avg
    stages = status.get("stages") or []
    done = [s for s in stages if s.get("duration_ms")]
    pending = [s for s in stages if s.get("status") in ("pending", "running")]
    if done and pending:
        avg = sum(int(s["duration_ms"]) for s in done) / len(done)
        status["eta_ms"] = int(avg * len(pending))
    else:
        status["eta_ms"] = None

    # Health
    failish = sum(1 for s in stages if s.get("status") in ("failed", "degraded") or s.get("errors"))
    if failish >= 4:
        status["pipeline_health"] = "critical"
    elif failish >= 1:
        status["pipeline_health"] = "degraded"
    else:
        status["pipeline_health"] = "healthy"
    return status


def build_live_dashboard(status: dict | None = None, *, queue_summary: dict | None = None) -> dict[str, Any]:
    """Dashboard payload for the Production Operations command center."""
    status = status or {}
    stages = status.get("stages") or []
    current = next((s for s in stages if s.get("status") == "running"), None)
    if not current and status.get("current_stage"):
        current = next((s for s in stages if s.get("key") == status["current_stage"]), None)

    dash = {
        "generated_at": _now(),
        "production_id": status.get("production_id"),
        "current_stage": (current or {}).get("label") or status.get("current_stage"),
        "current_stage_key": status.get("current_stage"),
        "overall_progress_pct": status.get("overall_progress_pct") or 0,
        "elapsed_ms": status.get("elapsed_ms") or 0,
        "estimated_time_remaining_ms": status.get("eta_ms"),
        "current_agent_working": status.get("current_agent") or (current or {}).get("current_agent"),
        "current_files": status.get("current_files") or [],
        "quality_scores": status.get("quality_scores") or {},
        "warnings": status.get("warnings") or [],
        "retry_count": status.get("retry_count") or 0,
        "pipeline_health": status.get("pipeline_health") or "unknown",
        "overall_status": status.get("overall_status"),
        "stages": [
            {
                "key": s.get("key"),
                "label": s.get("label"),
                "status": s.get("status"),
                "duration_ms": s.get("duration_ms"),
                "quality_score": s.get("quality_score"),
                "retries": s.get("retry_attempts"),
                "warnings": s.get("warnings"),
                "errors": s.get("errors"),
            }
            for s in stages
        ],
        "queue": queue_summary or {},
        "stage_count": len(STAGE_KEYS),
    }
    path = dashboard_path()
    path.write_text(json.dumps(dash, indent=2), encoding="utf-8")
    return dash
