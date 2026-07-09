"""Quality control for Autonomous Production Executor (Agent 23)."""

from __future__ import annotations

from services.autonomous_production.models import ExecutionState, ProductionJob, StageResult


PACKAGE_SLOTS = (
    "director_package",
    "creative_package",
    "asset_package",
    "animation_package",
    "post_production_package",
    "render_package",
    "publishing_package",
    "analytics_package",
)


def validate_job(job: ProductionJob) -> dict:
    """Validate a finished (or partial) job for QC issues."""
    issues: list[dict] = []
    warnings: list[str] = []
    score = 100.0

    # Pipeline / stage failures
    for sr in job.summary.stage_results:
        if isinstance(sr, dict):
            status = sr.get("status", "")
            stage = sr.get("stage", "")
            errors = sr.get("errors") or []
        else:
            status = sr.status
            stage = sr.stage
            errors = sr.errors
        if status == ExecutionState.FAILED or status == "failed":
            issues.append(
                {
                    "code": "pipeline_failure",
                    "stage": stage,
                    "message": "; ".join(errors) or f"Stage {stage} failed",
                }
            )
            score -= 15
        elif errors:
            warnings.append(f"{stage}: {'; '.join(errors)}")
            score -= 3

    # Budget overrun
    budget = float(job.context.budget_usd or 0)
    actual = float(job.summary.actual_cost_usd or job.summary.estimated_cost_usd or 0)
    if budget > 0 and actual > budget:
        issues.append(
            {
                "code": "budget_overrun",
                "stage": "",
                "message": f"Cost {actual:.4f} USD exceeds budget {budget:.4f} USD",
            }
        )
        score -= 10

    # Missing assets / invalid outputs on packages
    packages = job.summary.packages or []
    if job.state in (ExecutionState.COMPLETED, ExecutionState.PARTIAL) and not packages:
        issues.append(
            {
                "code": "invalid_outputs",
                "stage": "packaging",
                "message": "No ContentPackage outputs produced",
            }
        )
        score -= 20
    else:
        for pkg in packages:
            if not isinstance(pkg, dict):
                continue
            # Stage mismatch: publish-ready without render
            if pkg.get("publishing_package") and not (
                pkg.get("render_package") or pkg.get("post_production_package")
            ):
                warnings.append("Publishing package present without render/post package")
                score -= 5
            missing = [
                slot
                for slot in ("render_package",)
                if job.production_mode not in ("podcast", "audiobook")
                and not pkg.get(slot)
                and job.state == ExecutionState.COMPLETED
            ]
            for slot in missing:
                # Soft — many stages optional / stubbed.
                warnings.append(f"Missing optional package slot: {slot}")
                score -= 2

    # Provider failures surfaced in summary
    for fail in job.summary.failures or []:
        if isinstance(fail, dict) and "provider" in (fail.get("code") or fail.get("message") or "").lower():
            issues.append(
                {
                    "code": "provider_failure",
                    "stage": fail.get("stage", ""),
                    "message": fail.get("message", "Provider failure"),
                }
            )
            score -= 8

    score = max(0.0, min(100.0, round(score, 1)))
    status = "pass"
    if any(i["code"] in ("pipeline_failure", "invalid_outputs") for i in issues):
        status = "fail"
    elif issues or score < 70:
        status = "warn"

    return {
        "status": status,
        "quality_score": score,
        "issues": issues,
        "warnings": warnings,
        "checked_at": job.updated_at,
    }


def stage_results_from_workflow(run) -> list[StageResult]:
    """Project WorkflowStep outcomes into StageResult list."""
    results: list[StageResult] = []
    for step in getattr(getattr(run, "workflow", None), "steps", []) or []:
        status = step.status
        if status == "completed":
            mapped = ExecutionState.COMPLETED
        elif status == "failed":
            mapped = ExecutionState.FAILED
        elif status == "cancelled":
            mapped = ExecutionState.CANCELLED
        elif status == "skipped":
            mapped = "skipped"
        elif status in ("running", "retrying"):
            mapped = ExecutionState.RUNNING
        else:
            mapped = ExecutionState.PENDING
        results.append(
            StageResult(
                stage=step.stage,
                status=mapped,
                duration_ms=int(getattr(step, "duration_ms", 0) or 0),
                confidence=int(getattr(step, "confidence", 0) or 0),
                errors=list(getattr(step, "errors", []) or []),
                warnings=list(getattr(step, "warnings", []) or []),
                attempt=int(getattr(step, "attempt", 0) or 0),
                started_at=getattr(step, "started_at", "") or "",
                finished_at=getattr(step, "finished_at", "") or "",
                outputs=dict(getattr(step, "partial_outputs", {}) or {}),
            )
        )
    return results
