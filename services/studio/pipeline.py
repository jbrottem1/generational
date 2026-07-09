"""Pipeline visualization — maps orchestrator stage reports to studio stages."""

from __future__ import annotations

from services.studio.models import STUDIO_PIPELINE_STAGES

STAGE_STATUS_MAP = {
    "SUCCESS": "completed",
    "WARNING": "completed",
    "FAILED": "failed",
    "SKIPPED": "pending",
    "PENDING": "pending",
    "RUNNING": "running",
}


def map_stage_status(orchestrator_status: str) -> str:
    return STAGE_STATUS_MAP.get(orchestrator_status.upper(), "pending")


def _match_report(stage_def: dict, report: dict) -> bool:
    stage_key = report.get("stage", "").lower()
    for key in stage_def.get("orchestrator_keys", ()):
        if key in stage_key:
            return True
    return stage_key == stage_def["key"]


def _estimate_remaining(stages: list[dict]) -> int:
    """Rough ETA in seconds based on completed stage durations."""
    completed = [s for s in stages if s["status"] == "completed" and s["elapsed_sec"] > 0]
    pending = [s for s in stages if s["status"] in ("pending", "running")]
    if not completed or not pending:
        return 0
    avg = sum(s["elapsed_sec"] for s in completed) / len(completed)
    return int(avg * len(pending))


def build_pipeline_view(
    stage_reports: "list[dict] | None" = None,
    production_dashboard: "list[dict] | None" = None,
    pipeline_steps: "list[dict] | None" = None,
) -> list[dict]:
    """Build the 12-stage studio pipeline view from orchestrator diagnostics."""
    reports = list(stage_reports or [])
    dashboard = {item.get("key", ""): item for item in (production_dashboard or [])}
    steps = {step.get("engine", "").lower(): step for step in (pipeline_steps or [])}

    stages = []
    for stage_def in STUDIO_PIPELINE_STAGES:
        matched_report = next((r for r in reports if _match_report(stage_def, r)), None)
        dash = dashboard.get(stage_def["key"], {})

        if matched_report:
            status = map_stage_status(matched_report.get("status", "PENDING"))
            elapsed_ms = matched_report.get("duration_ms", 0)
            errors = matched_report.get("errors", [])
            warnings = matched_report.get("warnings", [])
        elif dash:
            status = dash.get("state", "waiting")
            if status == "completed":
                status = "completed"
            elif status == "running":
                status = "running"
            elif status == "failed":
                status = "failed"
            elif status == "retrying":
                status = "retry"
            else:
                status = "pending"
            elapsed_ms = dash.get("duration_ms", 0)
            errors = [dash.get("error")] if dash.get("error") else []
            warnings = []
        else:
            step = next(
                (steps[k] for k in steps if any(ok in k for ok in stage_def.get("orchestrator_keys", ()))),
                None,
            )
            if step:
                step_status = step.get("status", "pending")
                status = "completed" if step_status == "succeeded" else (
                    "failed" if step_status == "failed" else "pending"
                )
            else:
                status = "pending"
            elapsed_ms = 0
            errors = []
            warnings = []

        stages.append({
            "key": stage_def["key"],
            "label": stage_def["label"],
            "icon": stage_def["icon"],
            "status": status,
            "elapsed_sec": round(elapsed_ms / 1000, 1),
            "estimated_remaining_sec": 0,
            "errors": errors,
            "warnings": warnings,
            "can_retry": status in ("failed", "retry"),
        })

    remaining = _estimate_remaining(stages)
    for stage in stages:
        if stage["status"] in ("pending", "running"):
            stage["estimated_remaining_sec"] = remaining

    return stages
