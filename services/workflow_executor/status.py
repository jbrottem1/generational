"""Studio UI status projection for Agent 20 / Studio surfaces (Agent 21)."""

from __future__ import annotations

from services.workflow_executor.models import ProjectRun, WorkflowStatus
from services.workflow_executor.policy import estimate_completion_iso, progress_percent


def studio_status(run: ProjectRun) -> dict:
    """Compact status payload the Studio UI can poll.

    Fields:
      current_stage, progress, errors, outputs, estimated_completion,
      provider_usage, costs, logs
    """
    steps = run.workflow.steps
    current = ""
    for step in steps:
        if step.status in (WorkflowStatus.RUNNING, WorkflowStatus.RETRYING, WorkflowStatus.WAITING):
            current = step.stage
            break
    if not current:
        for step in steps:
            if step.status == WorkflowStatus.PENDING:
                current = step.stage
                break
    if not current and steps:
        current = steps[-1].stage

    progress = run.workflow.progress_pct or progress_percent(steps)
    errors = []
    for step in steps:
        for err in step.errors:
            errors.append({"stage": step.stage, "error": err, "status": step.status})
    for failure in run.result.failure_reports:
        if hasattr(failure, "to_dict"):
            errors.append(failure.to_dict())
        elif isinstance(failure, dict):
            errors.append(failure)

    outputs = {
        "packages": len(run.result.packages),
        "production_package": bool(run.result.production_package),
        "asset_package": bool(run.result.asset_package),
        "animation_package": bool(run.result.animation_package),
        "post_production_package": bool(run.result.post_production_package),
        "render_package": bool(run.result.render_package),
        "publishing_package": bool(run.result.publishing_package),
        "analytics_package": bool(run.result.analytics_package),
        "learning_context": bool(run.result.learning_context),
        "partial": run.result.partial,
    }

    eta = run.estimated_completion_at or estimate_completion_iso(
        run.started_at,
        progress,
        longform=run.config.longform_mode,
    )

    return {
        "run_id": run.run_id,
        "command": run.command,
        "production_type": run.production_type,
        "status": run.status,
        "current_stage": current,
        "progress": progress,
        "progress_pct": progress,
        "errors": errors,
        "outputs": outputs,
        "estimated_completion": eta,
        "provider_usage": dict(run.provider_usage or run.result.provider_usage),
        "costs": {
            "estimated_cost_usd": run.estimated_cost_usd or run.result.estimated_cost_usd,
            "budget_usd": run.config.budget_usd,
        },
        "logs": list(run.log.entries[-100:]),
        "steps": [
            {
                "stage": s.stage,
                "status": s.status,
                "attempt": s.attempt,
                "required": s.required,
                "optional": s.optional,
                "duration_ms": s.duration_ms,
                "confidence": s.confidence,
                "errors": list(s.errors),
                "warnings": list(s.warnings),
            }
            for s in steps
        ],
        "longform_mode": run.config.longform_mode,
        "template": run.config.template,
        "created_at": run.created_at,
        "updated_at": run.updated_at,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
    }
