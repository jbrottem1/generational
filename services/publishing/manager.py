"""PublishingManager — the coordination core of the Publishing Engine.

Takes publish-ready items (with render packages and Agent 8 optimization
packages), builds one platform publish package per (item × platform),
schedules each through the PublishingScheduler, enqueues PublishingJobs,
and executes due jobs through the provider adapters with RetryManager
failure handling. Every attempt is logged (structured events) and recorded
in PublishingHistory with an `analytics_ref` for the Analytics Engine.

Extension points (interfaces only today — see extensions.py):
- approval workflows / human review gates run before `execute_due_jobs`,
- analytics callbacks fire after each attempt,
- rollback handlers fire when a published post must be withdrawn.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from core.log import get_logger, log_event
from providers.publishing import get_publishing_provider, resolve_platform_key
from services.publishing.accounts import get_account_registry
from services.publishing.extensions import notify_publish_listeners, run_pre_publish_gates
from services.publishing.models import JobStatus, PUBLISHING_ENGINE_VERSION
from services.publishing.package import build_platform_publish_package
from services.publishing.queue import PublishingHistory, PublishingQueue, build_publishing_job
from services.publishing.retry import RetryManager
from services.publishing.scheduler import PublishingScheduler

logger = get_logger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PublishingManager:
    def __init__(
        self,
        queue: "PublishingQueue | None" = None,
        history: "PublishingHistory | None" = None,
        scheduler: "PublishingScheduler | None" = None,
        retry_manager: "RetryManager | None" = None,
    ) -> None:
        self.queue = queue or PublishingQueue()
        self.history = history or PublishingHistory()
        self.scheduler = scheduler or PublishingScheduler()
        self.retry_manager = retry_manager or RetryManager()
        self.accounts = get_account_registry()

    # ---------------------------------------------------------- preparation

    def prepare_jobs(
        self,
        item: dict,
        optimization: dict,
        mode: str = "immediate",
        brand_id: str = "",
        channel_id: str = "",
        visibility: str = "public",
    ) -> "tuple[list, list]":
        """Publish packages + queued jobs for one item across its platforms.

        Returns (jobs, warnings). Unsupported platforms are skipped with a
        warning — never an error, so future providers slot in additively.
        """
        platforms = (
            optimization.get("platforms")
            or item.get("target_platforms")
            or item.get("platforms")
            or []
        )
        jobs, warnings = [], []
        seen = set()
        for platform in platforms:
            canonical = resolve_platform_key(platform)
            if canonical in seen:
                continue
            seen.add(canonical)
            provider = get_publishing_provider(canonical)
            if provider is None:
                warnings.append(f"no publishing provider for platform: {platform}")
                continue

            schedule = self.scheduler.schedule(
                {**optimization, "project_id": optimization.get("project_id") or item.get("project_id", "")},
                canonical,
                mode=mode,
            )
            account = self.accounts.account_for(brand_id, channel_id, canonical)
            package = build_platform_publish_package(
                item, optimization, provider, schedule,
                account={"account_id": account["account_id"], "status": account["status"]},
                visibility=visibility,
            )
            policy = self.retry_manager.policy_for(provider)
            status = JobStatus.QUEUED if schedule["mode"] == "immediate" else JobStatus.SCHEDULED
            job = build_publishing_job(
                package,
                platform=canonical,
                provider=provider.name or canonical,
                scheduled_time=schedule["publish_time"],
                tz=schedule["timezone"],
                brand_id=brand_id,
                channel_id=channel_id,
                max_retries=policy["max_retries"],
                status=status,
            )
            warnings.extend(package["diagnostics"]["format_warnings"])
            jobs.append(self.queue.enqueue(job))
        return jobs, warnings

    # ------------------------------------------------------------ execution

    def execute_due_jobs(self, now: "str | None" = None) -> list:
        """Publish every due job through its provider; returns updated jobs."""
        executed = []
        for job in self.queue.due_jobs(now=now):
            executed.append(self.execute_job(job))
        return executed

    def execute_job(self, job: dict) -> dict:
        """One publish attempt for one job — never raises."""
        gate_problems = run_pre_publish_gates(job)
        if gate_problems:
            job["status"] = JobStatus.CANCELLED
            job["last_error"] = "; ".join(gate_problems)
            self.queue.update(job)
            log_event(logger, "publishing.job_gated", job_id=job["job_id"], problems=len(gate_problems))
            return job

        provider = get_publishing_provider(job["platform"])
        if provider is None:
            self.retry_manager.record_failure(job, f"provider unavailable: {job['platform']}")
            return self.queue.update(job)

        blocked = job["package"]["diagnostics"].get("provider_problems") or []
        if blocked:
            self.retry_manager.record_failure(job, f"package blocked: {'; '.join(blocked)}", provider)
            return self.queue.update(job)

        job["status"] = JobStatus.PUBLISHING
        started = time.time()
        started_at = _now_iso()
        try:
            result = provider.publish(job["package"])
        except Exception as exc:  # noqa: BLE001 - publish failures degrade, never crash
            result = {"status": "failed", "error": str(exc), "post_id": "", "post_url": "", "published_at": ""}

        attempt = {
            "attempt": job.get("attempts", 0) + 1,
            "provider": job["provider"],
            "platform": job["platform"],
            "status": result.get("status", "failed"),
            "scheduled_time": job.get("scheduled_time", ""),
            "started_at": started_at,
            "published_at": result.get("published_at", ""),
            "duration_ms": int((time.time() - started) * 1000),
            "post_id": result.get("post_id", ""),
            "post_url": result.get("post_url", ""),
            "warnings": job["package"]["diagnostics"].get("format_warnings", []),
            "error": result.get("error", ""),
            "analytics_ref": job.get("analytics_ref", ""),
        }
        job.setdefault("history", []).append(attempt)
        self.history.record(job, attempt)

        if result.get("status") == "published":
            job["attempts"] = job.get("attempts", 0) + 1
            job["status"] = JobStatus.PUBLISHED
            job["package"]["status"] = "published"
            job["last_error"] = ""
            log_event(
                logger, "publishing.published",
                job_id=job["job_id"], platform=job["platform"],
                provider=job["provider"], post_id=attempt["post_id"],
                duration_ms=attempt["duration_ms"],
                scheduled=job.get("scheduled_time", ""), actual=attempt["published_at"],
            )
        else:
            self.retry_manager.record_failure(job, result.get("error", "publish failed"), provider)

        self.queue.update(job)
        notify_publish_listeners(job, attempt)
        return job

    # -------------------------------------------------------------- summary

    def build_result(
        self,
        jobs: list,
        items: int,
        publish_mode: str,
        warnings: "list | None" = None,
        errors: "list | None" = None,
    ) -> dict:
        """The standardized PublishingResult (see PUBLISHING_RESULT_FIELDS)."""
        warnings = list(warnings or [])
        errors = list(errors or [])
        by_status = {status: 0 for status in JobStatus.ALL}
        for job in jobs:
            by_status[job.get("status", JobStatus.QUEUED)] = by_status.get(job.get("status"), 0) + 1

        if not jobs and not errors:
            status = "SKIPPED"
        elif errors or (by_status[JobStatus.FAILED] and by_status[JobStatus.FAILED] == len(jobs)):
            status = "FAILED"
        elif warnings or by_status[JobStatus.FAILED]:
            status = "WARNING"
        else:
            status = "SUCCESS"

        return {
            "engine_version": PUBLISHING_ENGINE_VERSION,
            "status": status,
            "items": items,
            "jobs_created": len(jobs),
            "published": by_status[JobStatus.PUBLISHED],
            "scheduled": by_status[JobStatus.SCHEDULED],
            "failed": by_status[JobStatus.FAILED],
            "cancelled": by_status[JobStatus.CANCELLED],
            "platforms": sorted({job.get("platform", "") for job in jobs}),
            "queue_size": self.queue.count(),
            "publish_mode": publish_mode,
            "warnings": warnings,
            "errors": errors,
            "results": [
                {
                    "job_id": job.get("job_id", ""),
                    "project_id": job.get("project_id", ""),
                    "platform": job.get("platform", ""),
                    "provider": job.get("provider", ""),
                    "status": job.get("status", ""),
                    "scheduled_time": job.get("scheduled_time", ""),
                    "published_at": (job.get("history") or [{}])[-1].get("published_at", ""),
                    "post_url": (job.get("history") or [{}])[-1].get("post_url", ""),
                    "attempts": job.get("attempts", 0),
                    "analytics_ref": job.get("analytics_ref", ""),
                }
                for job in jobs
            ],
            "generated_at": _now_iso(),
        }
