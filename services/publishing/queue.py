"""Publishing job queue + history — the durable state of the Publishing Engine.

Distinct from the pre-render metadata queue in `services/assets.py`
(`queue.json`): this queue holds full PublishingJob records for the
post-optimization publish stage, persisted to
`data/publishing_queue/jobs.json`, with every attempt appended to
`data/publishing_queue/history.json` (PublishingHistory) for the future
Analytics Engine to correlate against.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

from core.log import get_logger, log_event
from services.publishing.models import JobStatus

logger = get_logger(__name__)

_DEFAULT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "publishing_queue",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_publishing_job(
    package: dict,
    platform: str,
    provider: str,
    scheduled_time: str,
    tz: str = "UTC+00:00",
    brand_id: str = "",
    channel_id: str = "",
    max_retries: int = 3,
    status: str = JobStatus.QUEUED,
) -> dict:
    """One PublishingJob record (see PUBLISHING_JOB_FIELDS)."""
    job_id = f"pub_{uuid.uuid4().hex[:10]}"
    return {
        "job_id": job_id,
        "project_id": package.get("project_id", ""),
        "brand_id": brand_id,
        "channel_id": channel_id,
        "platform": platform,
        "provider": provider,
        "package": package,
        "status": status,
        "attempts": 0,
        "max_retries": max_retries,
        "scheduled_time": scheduled_time,
        "timezone": tz,
        "next_retry_at": "",
        "last_error": "",
        "history": [],
        "analytics_ref": f"an_{job_id}",   # future Analytics Engine correlation id
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }


class _JsonFileStore:
    """Minimal list-of-dicts JSON persistence (same pattern as services/assets.py)."""

    def __init__(self, directory: str, filename: str) -> None:
        self._directory = directory
        self._path = os.path.join(directory, filename)

    def load(self) -> list:
        if not os.path.exists(self._path):
            return []
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    def save(self, items: list) -> None:
        os.makedirs(self._directory, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)


class PublishingQueue:
    """Durable FIFO of PublishingJob records with status transitions."""

    def __init__(self, directory: "str | None" = None) -> None:
        self._store = _JsonFileStore(directory or _DEFAULT_DIR, "jobs.json")

    # ------------------------------------------------------------ lifecycle

    def enqueue(self, job: dict) -> dict:
        jobs = self._store.load()
        jobs.append(job)
        self._store.save(jobs)
        log_event(
            logger, "publishing.job_enqueued",
            job_id=job["job_id"], platform=job["platform"],
            status=job["status"], scheduled=job["scheduled_time"],
        )
        return job

    def update(self, job: dict) -> dict:
        job["updated_at"] = _now_iso()
        jobs = self._store.load()
        for index, existing in enumerate(jobs):
            if existing.get("job_id") == job["job_id"]:
                jobs[index] = job
                break
        else:
            jobs.append(job)
        self._store.save(jobs)
        return job

    def cancel(self, job_id: str) -> "dict | None":
        job = self.get(job_id)
        if job is None or job.get("status") in JobStatus.TERMINAL:
            return None
        job["status"] = JobStatus.CANCELLED
        self.update(job)
        log_event(logger, "publishing.job_cancelled", job_id=job_id)
        return job

    # -------------------------------------------------------------- queries

    def get(self, job_id: str) -> "dict | None":
        return next((j for j in self._store.load() if j.get("job_id") == job_id), None)

    def list_jobs(self, status: str = "") -> list:
        jobs = self._store.load()
        if status:
            jobs = [j for j in jobs if j.get("status") == status]
        return jobs

    def due_jobs(self, now: "str | None" = None) -> list:
        """Queued/scheduled jobs whose publish (or retry) time has arrived."""
        now = now or _now_iso()
        due = []
        for job in self._store.load():
            if job.get("status") not in (JobStatus.QUEUED, JobStatus.SCHEDULED):
                continue
            gate = job.get("next_retry_at") or job.get("scheduled_time") or ""
            if gate <= now:
                due.append(job)
        return due

    def count(self, status: str = "") -> int:
        return len(self.list_jobs(status))


class PublishingHistory:
    """Append-only log of every publish attempt — the audit trail the
    future Analytics Engine reads back via `analytics_ref`."""

    def __init__(self, directory: "str | None" = None) -> None:
        self._store = _JsonFileStore(directory or _DEFAULT_DIR, "history.json")

    def record(self, job: dict, attempt: dict) -> dict:
        entry = {
            "job_id": job.get("job_id", ""),
            "project_id": job.get("project_id", ""),
            "brand_id": job.get("brand_id", ""),
            "channel_id": job.get("channel_id", ""),
            "analytics_ref": job.get("analytics_ref", ""),
            **attempt,
        }
        entries = self._store.load()
        entries.append(entry)
        self._store.save(entries)
        return entry

    def for_job(self, job_id: str) -> list:
        return [e for e in self._store.load() if e.get("job_id") == job_id]

    def all(self) -> list:
        return self._store.load()
