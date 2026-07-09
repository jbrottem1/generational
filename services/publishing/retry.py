"""RetryManager — configurable retry policies with exponential backoff.

The default policy is DEFAULT_RETRY_POLICY; each provider adapter can
override any field via `PublishingProvider.retry_policy()` (rate-limited
platforms back off harder, for example). Failure recovery is always safe:
a job that exhausts its retries is marked failed with its full error
history preserved — nothing raises, nothing is lost.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from core.log import get_logger, log_event
from services.publishing.models import DEFAULT_RETRY_POLICY, JobStatus

logger = get_logger(__name__)


class RetryManager:
    def __init__(self, policy: "dict | None" = None) -> None:
        self._base_policy = {**DEFAULT_RETRY_POLICY, **(policy or {})}

    def policy_for(self, provider) -> dict:
        """The effective policy: defaults ← constructor ← provider overrides."""
        overrides = provider.retry_policy() if provider is not None else {}
        return {**self._base_policy, **overrides}

    def delay_sec(self, attempts: int, policy: dict) -> float:
        """Exponential backoff delay before the next attempt."""
        delay = policy["base_delay_sec"] * (policy["backoff_multiplier"] ** max(attempts - 1, 0))
        return min(delay, policy["max_delay_sec"])

    def should_retry(self, job: dict, policy: dict) -> bool:
        return (
            job.get("status") not in (JobStatus.PUBLISHED, JobStatus.CANCELLED)
            and job.get("attempts", 0) < policy["max_retries"]
        )

    def record_failure(self, job: dict, error: str, provider=None) -> dict:
        """Fold one failed attempt into the job; schedule a retry or fail it.

        Returns the updated job. Safe recovery: exhausted jobs become
        JobStatus.FAILED with `last_error` and full history intact.
        """
        policy = self.policy_for(provider)
        job["attempts"] = job.get("attempts", 0) + 1
        job["last_error"] = error
        job["updated_at"] = datetime.now(timezone.utc).isoformat()

        if self.should_retry(job, policy):
            delay = self.delay_sec(job["attempts"], policy)
            job["status"] = JobStatus.QUEUED
            job["next_retry_at"] = (
                datetime.now(timezone.utc) + timedelta(seconds=delay)
            ).isoformat()
            log_event(
                logger, "publishing.retry_scheduled", level=30,
                job_id=job.get("job_id", ""), attempt=job["attempts"],
                delay_sec=int(delay), error=error[:120],
            )
        else:
            job["status"] = JobStatus.FAILED
            job["next_retry_at"] = ""
            log_event(
                logger, "publishing.job_failed", level=40,
                job_id=job.get("job_id", ""), attempts=job["attempts"],
                error=error[:120],
            )
        return job
