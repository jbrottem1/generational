"""PublishingEngine — Agent 7's entry point (key: publishing).

Consumes finished content (RenderPackage from Agent 6 inside each item,
optimization PublishingPackages from Agent 8 via the `publishing_packages`
context key) and prepares it for the supported publishing providers:
platform-fitted publish packages, timezone-aware scheduling, a durable
retry-capable job queue, mock publish execution, and a standardized
PublishingResult back to the orchestrator.

Failure policy: publishing NEVER crashes the pipeline. Empty context →
SKIPPED result; unsupported platforms and provider failures degrade to
warnings/failed jobs with full diagnostics. Real platform APIs swap in
behind `providers/publishing/` adapters — nothing here changes.

Ownership rules honored:
- Writes the ContentPackage `publishing_package` slot (Agent 7's slot) and
  advances `status` to "scheduled" / "published". Add-only, never renames.
- Never mutates `render_package` (Agent 6) or the `publishing_packages`
  handover key (Agent 8).
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.contracts import ContractEngine
from engines.publishing.scheduler_engine import collect_publish_items, pair_with_optimization
from services.publishing.models import JobStatus, PUBLISHING_ENGINE_VERSION

logger = get_logger(__name__)


def _manager():
    from services.publishing.manager import PublishingManager
    return PublishingManager


def _publishing_package_of(jobs: list) -> dict:
    """The per-item `publishing_package` slot value from its queued jobs."""
    statuses = {job.get("status") for job in jobs}
    if JobStatus.PUBLISHED in statuses and statuses <= {JobStatus.PUBLISHED}:
        status = "published"
    elif JobStatus.PUBLISHED in statuses:
        status = "partially_published"
    elif statuses & {JobStatus.SCHEDULED, JobStatus.QUEUED}:
        status = "scheduled"
    elif JobStatus.FAILED in statuses:
        status = "failed"
    else:
        status = "cancelled"
    return {
        "engine_version": PUBLISHING_ENGINE_VERSION,
        "status": status,
        "jobs": [
            {
                "job_id": job.get("job_id", ""),
                "platform": job.get("platform", ""),
                "provider": job.get("provider", ""),
                "status": job.get("status", ""),
                "scheduled_time": job.get("scheduled_time", ""),
                "timezone": job.get("timezone", ""),
                "post_id": (job.get("history") or [{}])[-1].get("post_id", ""),
                "post_url": (job.get("history") or [{}])[-1].get("post_url", ""),
                "published_at": (job.get("history") or [{}])[-1].get("published_at", ""),
                "analytics_ref": job.get("analytics_ref", ""),
            }
            for job in jobs
        ],
    }


def publish_content(context: dict, manager=None) -> dict:
    """Prepare, queue, and (for immediate mode) execute every publish job."""
    manager = manager or _manager()()
    items, source_key = collect_publish_items(context)
    mode = context.get("publish_mode", "immediate")

    if not items:
        result = manager.build_result([], items=0, publish_mode=mode)
        result["reason"] = "No publish-eligible items in context — nothing to publish."
        return {"publishing_result": result}

    all_jobs, warnings = [], []
    for item, optimization in pair_with_optimization(items, context):
        if not optimization:
            warnings.append(
                f"no optimization package for item: {item.get('title', item.get('project_id', '?'))}"
            )
        jobs, item_warnings = manager.prepare_jobs(
            item,
            optimization,
            mode=mode,
            brand_id=item.get("brand_id", "") or context.get("brand_id", ""),
            channel_id=item.get("channel_id", "") or context.get("channel_id", ""),
            visibility=context.get("visibility", "public"),
        )
        warnings.extend(item_warnings)

        if mode == "immediate":
            jobs = [manager.execute_job(job) for job in jobs]

        item["publishing_package"] = _publishing_package_of(jobs) if jobs else {
            "engine_version": PUBLISHING_ENGINE_VERSION,
            "status": "skipped",
            "jobs": [],
        }
        if jobs:
            item_status = item["publishing_package"]["status"]
            if item_status in ("published", "partially_published"):
                item["status"] = "published"
            elif item_status == "scheduled":
                item["status"] = "scheduled"
        all_jobs.extend(jobs)

    result = manager.build_result(all_jobs, items=len(items), publish_mode=mode, warnings=warnings)
    log_event(
        logger, "publishing.completed",
        items=len(items), jobs=len(all_jobs),
        published=result["published"], scheduled=result["scheduled"],
        failed=result["failed"], status=result["status"], mode=mode,
    )

    updates = {
        "publishing_result": result,
        "publishing_jobs": all_jobs,
    }
    if source_key:
        updates[source_key] = context.get(source_key, [])
    return updates


class PublishingEngine(ContractEngine):
    """Agent 7 — Publishing & Distribution (provider-based, mock adapters)."""

    key = "publishing"
    label = "Publishing & Distribution"
    icon = "📤"
    description = (
        "Prepare optimized content for every supported platform: provider "
        "adapters, timezone-aware scheduling, retry-capable publish queue, "
        "and publish tracking — real platform APIs swap in behind providers."
    )
    version = PUBLISHING_ENGINE_VERSION
    input_contract = ["publishing_packages"]
    output_contract = ["publishing_result"]
    dependencies = ["render", "seo_optimization", "scheduler"]
    capabilities = [
        "publishing", "distribution", "scheduling", "retry",
        "multi-platform", "multi-brand", "multi-country", "queue",
    ]

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        return publish_content(context)
