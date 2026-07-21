"""Persist Executive Orchestrator run logs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.log import get_logger, log_event

logger = get_logger(__name__)

ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT / "data" / "generational_os" / "executive_runs"


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def persist_run_log(run: dict[str, Any], *, log_dir: Path | None = None) -> Path:
    """Write one run JSON + append to rolling index.

    Logged fields: topic, runtime, engines, generation time, QA score,
    export size, output paths, publish status.
    """
    log_dir = Path(log_dir or LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    run_id = str(run.get("id") or "run")
    path = log_dir / f"run_{run_id}_{_stamp()}.json"

    record = {
        "id": run.get("id"),
        "topic": run.get("topic"),
        "command": run.get("command"),
        "runtime_sec": run.get("runtime_sec"),
        "platforms": run.get("platforms"),
        "engines_used": run.get("engines_used"),
        "generation_time_ms": run.get("generation_time_ms"),
        "qa_score": run.get("qa_score"),
        "qa_decision": run.get("qa_decision"),
        "revision_rounds": run.get("revision_rounds"),
        "export_size_bytes": run.get("export_size_bytes"),
        "export_paths": run.get("export_paths"),
        "publish_status": run.get("publish_status"),
        "status": run.get("status"),
        "error": run.get("error"),
        "created_at": run.get("created_at"),
        "finished_at": run.get("finished_at"),
        "stages": run.get("stages"),
        "artifacts": run.get("artifacts"),
    }
    path.write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")

    index_path = log_dir / "index.json"
    index: list[dict] = []
    if index_path.is_file():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
            if not isinstance(index, list):
                index = []
        except Exception:
            index = []
    index.append(
        {
            "path": str(path.relative_to(ROOT)) if str(path).startswith(str(ROOT)) else str(path),
            "id": record["id"],
            "topic": record["topic"],
            "status": record["status"],
            "qa_score": record["qa_score"],
            "generation_time_ms": record["generation_time_ms"],
            "finished_at": record["finished_at"],
        }
    )
    index_path.write_text(json.dumps(index[-500:], indent=2), encoding="utf-8")
    log_event(logger, "executive.run_logged", path=str(path), status=record["status"])
    return path
