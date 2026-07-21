"""Job-queue integration for Executive Orchestrator."""

from __future__ import annotations

from core.jobs import get_queue
from core.log import get_logger, log_event

logger = get_logger(__name__)

EXECUTIVE_JOB_TYPE = "run_executive"


def _run_executive_job(payload: dict) -> dict:
    from services.executive_orchestrator.orchestrator import get_executive_orchestrator

    command = str(payload.get("command") or payload.get("topic") or "")
    options = dict(payload.get("options") or {})
    # Strip keys that are not create_video kwargs
    options.pop("async", None)
    return get_executive_orchestrator().create_video(command, **options)


def ensure_executive_handler(queue=None) -> None:
    queue = queue or get_queue()
    if not queue.has_handler(EXECUTIVE_JOB_TYPE):
        queue.register_handler(EXECUTIVE_JOB_TYPE, _run_executive_job)
        log_event(logger, "executive.job_handler_registered", job_type=EXECUTIVE_JOB_TYPE)


def submit_executive_job(command: str, *, options: dict | None = None, queue=None):
    queue = queue or get_queue()
    ensure_executive_handler(queue)
    return queue.submit(EXECUTIVE_JOB_TYPE, {"command": command, "options": options or {}})
