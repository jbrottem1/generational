"""Production Queue — single / batch / scheduled / priority / resume.

Thin façade over core.jobs — does not invent a second queue system.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.jobs import JobStatus, get_queue
from services.production_operations.status import OPS_ROOT

OPS_JOB_TYPE = "production_operations_run"
QUEUE_INDEX = OPS_ROOT / "PRODUCTION_QUEUE.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _index_load() -> dict:
    if not QUEUE_INDEX.exists():
        return {"jobs": [], "updated_at": _now()}
    try:
        return json.loads(QUEUE_INDEX.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {"jobs": [], "updated_at": _now()}


def _index_save(data: dict) -> None:
    OPS_ROOT.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _now()
    QUEUE_INDEX.write_text(json.dumps(data, indent=2), encoding="utf-8")


def ensure_ops_queue_handler() -> None:
    """Register the ops job handler on the shared app queue (idempotent)."""
    queue = get_queue()
    if queue.has_handler(OPS_JOB_TYPE):
        return

    def _handler(payload: dict) -> dict:
        from services.production_operations.orchestrator import run_studio_ops

        return run_studio_ops(**{k: v for k, v in payload.items() if k != "_meta"})

    queue.register_handler(OPS_JOB_TYPE, _handler)


def _track(job_id: str, meta: dict) -> None:
    data = _index_load()
    jobs = [j for j in data.get("jobs") or [] if j.get("job_id") != job_id]
    jobs.append({"job_id": job_id, **meta, "updated_at": _now()})
    # Priority: sort pending by priority desc
    jobs.sort(key=lambda j: (-int(j.get("priority") or 0), j.get("created_at") or ""))
    data["jobs"] = jobs[-200:]
    _index_save(data)


def enqueue_production(
    *,
    topic: str = "",
    platform: str = "youtube_shorts",
    length_sec: int = 60,
    style: str = "educational",
    narrator: str = "professor",
    voice: str = "default",
    quality_target: float = 98.0,
    constraints: dict | None = None,
    command: str = "",
    priority: int = 0,
    scheduled_at: str = "",
    batch_id: str = "",
    resume_production_id: str = "",
    run_immediately: bool = True,
) -> dict[str, Any]:
    """Queue one production. Optionally run immediately (Streamlit sync model)."""
    ensure_ops_queue_handler()
    queue = get_queue()
    payload = {
        "topic": topic,
        "platform": platform,
        "length_sec": length_sec,
        "style": style,
        "narrator": narrator,
        "voice": voice,
        "quality_target": quality_target,
        "constraints": constraints or {},
        "command": command,
        "production_id": resume_production_id or "",
        "resume": bool(resume_production_id),
        "_meta": {
            "priority": priority,
            "scheduled_at": scheduled_at,
            "batch_id": batch_id,
        },
    }
    job = queue.submit(OPS_JOB_TYPE, payload)
    _track(
        job.id,
        {
            "status": JobStatus.PENDING,
            "priority": priority,
            "scheduled_at": scheduled_at,
            "batch_id": batch_id,
            "topic": topic or command[:80],
            "platform": platform,
            "created_at": _now(),
            "resume_production_id": resume_production_id,
        },
    )
    # Scheduled jobs stay pending until caller drains after scheduled_at
    if scheduled_at and scheduled_at > _now():
        return {"job_id": job.id, "status": "scheduled", "scheduled_at": scheduled_at, "result": None}

    if run_immediately:
        finished = queue.run(job.id)
        _track(
            job.id,
            {
                "status": finished.status,
                "priority": priority,
                "scheduled_at": scheduled_at,
                "batch_id": batch_id,
                "topic": topic or command[:80],
                "platform": platform,
                "created_at": job.created_at,
                "error": finished.error,
                "production_id": (finished.result or {}).get("production_id"),
            },
        )
        return {
            "job_id": job.id,
            "status": finished.status,
            "result": finished.result,
            "error": finished.error,
        }
    return {"job_id": job.id, "status": JobStatus.PENDING, "result": None}


def enqueue_batch(items: list[dict], *, batch_id: str = "", priority: int = 0) -> dict[str, Any]:
    """Enqueue many productions (sequential run_immediately for reliability)."""
    import uuid

    bid = batch_id or f"batch_{uuid.uuid4().hex[:8]}"
    results = []
    for item in items:
        results.append(
            enqueue_production(
                **{k: v for k, v in item.items() if k != "priority"},
                priority=int(item.get("priority") or priority),
                batch_id=bid,
                run_immediately=True,
            )
        )
    return {"batch_id": bid, "count": len(results), "jobs": results}


def recover_failed_jobs(*, run_immediately: bool = True) -> list[dict]:
    """Re-queue jobs marked failed for recovery."""
    data = _index_load()
    recovered = []
    for row in data.get("jobs") or []:
        if row.get("status") != JobStatus.FAILED:
            continue
        recovered.append(
            enqueue_production(
                topic=str(row.get("topic") or ""),
                platform=str(row.get("platform") or "youtube_shorts"),
                priority=int(row.get("priority") or 5),
                resume_production_id=str(row.get("production_id") or ""),
                run_immediately=run_immediately,
            )
        )
    return recovered


def queue_summary() -> dict[str, Any]:
    data = _index_load()
    jobs = data.get("jobs") or []
    return {
        "pending": sum(1 for j in jobs if j.get("status") == JobStatus.PENDING),
        "running": sum(1 for j in jobs if j.get("status") == JobStatus.RUNNING),
        "succeeded": sum(1 for j in jobs if j.get("status") == JobStatus.SUCCEEDED),
        "failed": sum(1 for j in jobs if j.get("status") == JobStatus.FAILED),
        "scheduled": sum(1 for j in jobs if j.get("status") == "scheduled"),
        "recent": jobs[-10:],
    }
