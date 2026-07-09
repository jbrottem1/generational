"""Retry, degrade, and resume policy helpers (Agent 21)."""

from __future__ import annotations

from services.orchestrator.models import StageStatus
from services.orchestrator.stages import DISTRIBUTION_STAGES
from services.workflow_executor.models import (
    FailureReport,
    RetryPolicy,
    WorkflowStatus,
    WorkflowStep,
)

DISTRIBUTION_SET = frozenset(DISTRIBUTION_STAGES) | {"analytics", "learning", "brand_management"}


def map_orchestrator_status(status: str, optional: bool = False) -> str:
    """Map Orchestrator StageStatus → WorkflowStatus."""
    if status == StageStatus.SUCCESS:
        return WorkflowStatus.COMPLETED
    if status == StageStatus.SKIPPED:
        return WorkflowStatus.SKIPPED
    if status == StageStatus.WARNING:
        return WorkflowStatus.COMPLETED if optional else WorkflowStatus.COMPLETED
    if status == StageStatus.FAILED:
        return WorkflowStatus.FAILED
    return status or WorkflowStatus.FAILED


def should_retry(step: WorkflowStep, policy: RetryPolicy) -> bool:
    if not policy.retry_on_failed:
        return False
    if step.status != WorkflowStatus.FAILED:
        return False
    return step.attempt < step.max_attempts


def should_stop_run(
    step: WorkflowStep,
    policy: RetryPolicy,
    *,
    exhausted_retries: bool,
) -> bool:
    """Whether a failed step should abort the remaining plan."""
    if step.status != WorkflowStatus.FAILED:
        return False
    if not exhausted_retries and should_retry(step, policy):
        return False
    if step.optional and policy.skip_optional_on_fail:
        return False
    if step.stage in DISTRIBUTION_SET and policy.degrade_distribution_failures:
        return False
    return step.required


def degrade_failed_optional(step: WorkflowStep, policy: RetryPolicy) -> bool:
    """Mark a failed optional/distribution step as skipped and continue."""
    if step.status != WorkflowStatus.FAILED:
        return False
    if step.optional and policy.skip_optional_on_fail:
        step.status = WorkflowStatus.SKIPPED
        step.warnings.append("Optional stage failed — skipped for graceful degradation.")
        return True
    if step.stage in DISTRIBUTION_SET and policy.degrade_distribution_failures:
        step.status = WorkflowStatus.SKIPPED
        step.warnings.append("Distribution stage failed — degraded; continuing pipeline.")
        return True
    return False


def build_failure_report(step: WorkflowStep, recoverable: bool = True) -> FailureReport:
    return FailureReport(
        stage=step.stage,
        status=step.status,
        message="; ".join(step.errors) or f"Stage {step.stage} failed",
        errors=list(step.errors),
        attempt=step.attempt,
        recoverable=recoverable,
        partial_outputs=dict(step.partial_outputs),
    )


def progress_percent(steps: list[WorkflowStep]) -> float:
    if not steps:
        return 0.0
    done = sum(
        1
        for s in steps
        if s.status
        in (
            WorkflowStatus.COMPLETED,
            WorkflowStatus.SKIPPED,
            WorkflowStatus.CANCELLED,
        )
    )
    return round(100.0 * done / len(steps), 1)


def estimate_completion_iso(
    started_at: str,
    progress_pct: float,
    *,
    longform: bool = False,
) -> str:
    """Rough ETA from elapsed progress (Studio UI hint only)."""
    from datetime import datetime, timedelta, timezone

    if not started_at or progress_pct <= 0:
        return ""
    try:
        started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    except ValueError:
        return ""
    now = datetime.now(timezone.utc)
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    elapsed = (now - started).total_seconds()
    if progress_pct >= 100:
        return now.isoformat()
    remaining_ratio = (100.0 - progress_pct) / progress_pct
    remaining = elapsed * remaining_ratio
    if longform:
        remaining = max(remaining, 60.0)
    return (now + timedelta(seconds=remaining)).isoformat()
