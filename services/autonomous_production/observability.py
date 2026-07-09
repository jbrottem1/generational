"""Observability helpers for Autonomous Production Executor (Agent 23)."""

from __future__ import annotations

from datetime import datetime, timezone

from services.autonomous_production.estimates import remaining_runtime_sec
from services.autonomous_production.models import ProductionJob


def _elapsed_sec(started_at: str, finished_at: str = "") -> float:
    if not started_at:
        return 0.0
    try:
        started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        end_s = finished_at or datetime.now(timezone.utc).isoformat()
        ended = datetime.fromisoformat(end_s.replace("Z", "+00:00"))
    except ValueError:
        return 0.0
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    if ended.tzinfo is None:
        ended = ended.replace(tzinfo=timezone.utc)
    return max(0.0, (ended - started).total_seconds())


def execution_log(job: ProductionJob) -> dict:
    """Detailed execution log for operators / Studio / automation."""
    remaining = job.remaining_sec
    if remaining <= 0 and job.context.estimated_runtime_sec:
        remaining = remaining_runtime_sec(
            job.context.estimated_runtime_sec, job.progress_pct
        )
    return {
        "job_id": job.job_id,
        "command": job.command,
        "production_mode": job.production_mode,
        "state": job.state,
        "current_stage": job.current_stage,
        "progress_pct": job.progress_pct,
        "elapsed_sec": round(_elapsed_sec(job.started_at, job.finished_at), 2),
        "remaining_sec": remaining,
        "estimated_runtime_sec": job.context.estimated_runtime_sec,
        "provider_usage": dict(job.summary.provider_usage or {}),
        "costs": {
            "estimated_usd": job.summary.estimated_cost_usd
            or job.context.estimated_cost_usd,
            "actual_usd": job.summary.actual_cost_usd,
            "budget_usd": job.context.budget_usd,
        },
        "failures": list(job.summary.failures or []),
        "warnings": list(job.summary.warnings or []),
        "quality_score": job.summary.quality_score,
        "workflow_run_id": job.workflow_run_id,
        "child_job_ids": list(job.child_job_ids),
        "log": list(job.log),
        "checkpoint": job.checkpoint.to_dict() if job.checkpoint else None,
    }


def progress_snapshot(job: ProductionJob) -> dict:
    return {
        "job_id": job.job_id,
        "state": job.state,
        "current_stage": job.current_stage,
        "progress_pct": job.progress_pct,
        "remaining_sec": job.remaining_sec,
        "quality_score": job.summary.quality_score,
    }
