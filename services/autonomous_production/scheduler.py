"""Production scheduling for Autonomous Production Executor (Agent 23).

Schedules ProductionJobs onto the shared JobQueue without bypassing
WorkflowExecutor / Orchestrator.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from core.log import get_logger, log_event

if TYPE_CHECKING:
    from services.autonomous_production.models import ProductionJob

logger = get_logger(__name__)

PRODUCTION_JOB_TYPE = "autonomous_production"


def schedule_job(
    job: "ProductionJob",
    *,
    queue=None,
    run_at: str = "",
    store_dir: str = "",
) -> dict:
    """Enqueue a production job for async execution."""
    from core.jobs import get_queue
    from services.autonomous_production.executor import ensure_production_handler
    from services.autonomous_production.models import ExecutionState

    q = queue or get_queue()
    ensure_production_handler(q)
    job.state = ExecutionState.SCHEDULED
    job.scheduled_at = run_at or datetime.now(timezone.utc).isoformat()
    job.append_log("job.scheduled", run_at=job.scheduled_at)
    payload = {
        "job_id": job.job_id,
        "command": job.command,
        "config": {
            "production_mode": job.production_mode,
            **job.context.options,
            "budget_usd": job.context.budget_usd,
            "quality_level": job.context.quality_level,
            "platform_targets": list(job.context.platform_targets),
            "provider_preferences": dict(job.context.provider_preferences),
            "workflow_config": dict(job.context.workflow_config),
        },
        "resume_job_id": "",
        "store_dir": store_dir,
        "run_at": job.scheduled_at,
    }
    queued = q.submit(PRODUCTION_JOB_TYPE, payload)
    log_event(
        logger,
        "autonomous_production.scheduled",
        job_id=job.job_id,
        queue_job_id=getattr(queued, "id", ""),
    )
    return {
        "job_id": job.job_id,
        "queue_job_id": getattr(queued, "id", ""),
        "state": job.state,
        "scheduled_at": job.scheduled_at,
    }
