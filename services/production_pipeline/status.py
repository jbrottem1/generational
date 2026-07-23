"""PIPELINE_STATUS.json writer — live status during production pipeline runs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.production_pipeline.stages import PRODUCTION_STAGES, STAGE_KEYS

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DIR = ROOT / "data" / "productions"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def production_dir(production_id: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in production_id)[:80]
    path = DEFAULT_DIR / safe
    path.mkdir(parents=True, exist_ok=True)
    return path


def status_path(production_id: str) -> Path:
    return production_dir(production_id) / "PIPELINE_STATUS.json"


def new_status(production_id: str, *, command: str = "", platform: str = "") -> dict[str, Any]:
    stages = []
    for spec in PRODUCTION_STAGES:
        stages.append(
            {
                "key": spec["key"],
                "label": spec["label"],
                "engines": list(spec["engines"]),
                "status": "pending",
                "elapsed_ms": 0,
                "started_at": None,
                "finished_at": None,
                "success": None,
                "error": "",
                "output_location": "",
                "validation_score": 0,
                "engine_results": [],
            }
        )
    return {
        "schema_version": "1.0",
        "production_id": production_id,
        "command": command,
        "platform": platform,
        "current_stage": None,
        "overall_status": "pending",
        "started_at": _now(),
        "finished_at": None,
        "elapsed_ms": 0,
        "success": None,
        "output_location": str(production_dir(production_id)),
        "validation_score": 0,
        "stages": stages,
        "updated_at": _now(),
    }


def write_status(production_id: str, payload: dict) -> Path:
    path = status_path(production_id)
    payload = dict(payload)
    payload["updated_at"] = _now()
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_status(production_id: str) -> dict | None:
    path = status_path(production_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def mark_stage_running(status: dict, stage_key: str) -> dict:
    status = dict(status)
    status["current_stage"] = stage_key
    status["overall_status"] = "running"
    for stage in status.get("stages") or []:
        if stage["key"] == stage_key:
            stage["status"] = "running"
            stage["started_at"] = _now()
            stage["success"] = None
            break
    return status


def mark_stage_finished(
    status: dict,
    stage_key: str,
    *,
    success: bool,
    elapsed_ms: int,
    output_location: str = "",
    validation_score: float = 0,
    error: str = "",
    engine_results: list | None = None,
) -> dict:
    status = dict(status)
    for stage in status.get("stages") or []:
        if stage["key"] != stage_key:
            continue
        stage["status"] = "succeeded" if success else "failed"
        stage["finished_at"] = _now()
        stage["elapsed_ms"] = int(elapsed_ms)
        stage["success"] = bool(success)
        stage["error"] = error or ""
        stage["output_location"] = output_location or status.get("output_location") or ""
        stage["validation_score"] = float(validation_score)
        stage["engine_results"] = list(engine_results or [])
        break
    # Roll-up
    stages = status.get("stages") or []
    done = [s for s in stages if s.get("status") in ("succeeded", "failed", "skipped")]
    status["elapsed_ms"] = sum(int(s.get("elapsed_ms") or 0) for s in stages)
    scores = [float(s.get("validation_score") or 0) for s in done if s.get("success")]
    status["validation_score"] = round(sum(scores) / len(scores), 1) if scores else 0
    if any(s.get("status") == "failed" for s in stages):
        status["overall_status"] = "failed"
        status["success"] = False
        status["finished_at"] = _now()
        status["current_stage"] = stage_key
    elif all(s.get("status") in ("succeeded", "skipped") for s in stages):
        status["overall_status"] = "succeeded"
        status["success"] = True
        status["finished_at"] = _now()
        status["current_stage"] = STAGE_KEYS[-1] if STAGE_KEYS else stage_key
    else:
        status["overall_status"] = "running"
        status["success"] = None
    return status


def mark_stage_skipped(status: dict, stage_key: str, reason: str = "") -> dict:
    status = dict(status)
    for stage in status.get("stages") or []:
        if stage["key"] != stage_key:
            continue
        stage["status"] = "skipped"
        stage["finished_at"] = _now()
        stage["success"] = True
        stage["error"] = reason
        break
    return status
