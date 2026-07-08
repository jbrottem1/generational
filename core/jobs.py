"""Central job queue for asynchronous content-generation tasks.

Any unit of work (run a workflow, generate a batch, publish a video) is
submitted as a Job with a type and a payload. Handlers are registered per
job type, so new task kinds plug in without changing the queue.

Execution is currently synchronous and in-process (Streamlit's model), but
callers only depend on submit/run semantics — a background worker thread or
external worker process can later drain the queue via `run_next()` in a
loop without any caller changes.
"""

from __future__ import annotations

import threading
import uuid
from collections import OrderedDict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone

from core.log import get_logger, log_event

logger = get_logger(__name__)


class JobStatus:
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Job:
    type: str
    payload: dict
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    status: str = JobStatus.PENDING
    result: dict = field(default_factory=dict)
    error: str = ""
    created_at: str = field(default_factory=_now)
    started_at: str = ""
    finished_at: str = ""


class JobQueue:
    """FIFO job queue with per-type handlers. Thread-safe."""

    def __init__(self) -> None:
        self._jobs: "OrderedDict[str, Job]" = OrderedDict()
        self._pending: "deque[str]" = deque()
        self._handlers: dict = {}
        self._lock = threading.Lock()

    def register_handler(self, job_type: str, handler) -> None:
        """`handler(payload: dict) -> dict` — its return value becomes job.result."""
        with self._lock:
            self._handlers[job_type] = handler
        log_event(logger, "jobqueue.handler_registered", job_type=job_type)

    def has_handler(self, job_type: str) -> bool:
        return job_type in self._handlers

    def submit(self, job_type: str, payload: dict) -> Job:
        job = Job(type=job_type, payload=payload)
        with self._lock:
            self._jobs[job.id] = job
            self._pending.append(job.id)
        log_event(logger, "jobqueue.submitted", job_id=job.id, job_type=job_type)
        return job

    def run(self, job_id: str) -> Job:
        """Execute one specific job synchronously."""
        with self._lock:
            job = self._jobs[job_id]
            if job_id in self._pending:
                self._pending.remove(job_id)
        return self._execute(job)

    def run_next(self) -> "Job | None":
        """Execute the oldest pending job; the loop a background worker would run."""
        with self._lock:
            if not self._pending:
                return None
            job = self._jobs[self._pending.popleft()]
        return self._execute(job)

    def _execute(self, job: Job) -> Job:
        handler = self._handlers.get(job.type)
        if handler is None:
            job.status = JobStatus.FAILED
            job.error = f"No handler registered for job type '{job.type}'"
            job.finished_at = _now()
            log_event(logger, "jobqueue.failed", job_id=job.id, job_type=job.type, error=job.error)
            return job

        job.status = JobStatus.RUNNING
        job.started_at = _now()
        log_event(logger, "jobqueue.started", job_id=job.id, job_type=job.type)
        try:
            job.result = handler(job.payload) or {}
            job.status = JobStatus.SUCCEEDED
            log_event(logger, "jobqueue.succeeded", job_id=job.id, job_type=job.type)
        except Exception as exc:  # noqa: BLE001 - a job must never crash the app
            job.status = JobStatus.FAILED
            job.error = str(exc)
            log_event(logger, "jobqueue.failed", job_id=job.id, job_type=job.type, error=job.error)
        job.finished_at = _now()
        return job

    def get(self, job_id: str) -> "Job | None":
        return self._jobs.get(job_id)

    def jobs(self) -> list:
        return list(self._jobs.values())

    def pending_count(self) -> int:
        return len(self._pending)

    def stats(self) -> dict:
        counts = {
            JobStatus.PENDING: 0,
            JobStatus.RUNNING: 0,
            JobStatus.SUCCEEDED: 0,
            JobStatus.FAILED: 0,
        }
        for job in self._jobs.values():
            counts[job.status] = counts.get(job.status, 0) + 1
        counts["total"] = len(self._jobs)
        return counts


_queue = JobQueue()


def get_queue() -> JobQueue:
    """The app-wide job queue singleton."""
    return _queue
