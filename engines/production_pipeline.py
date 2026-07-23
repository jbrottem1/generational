"""Production Pipeline Integration Engine — thin adapter over the integration layer.

Does not reimplement research/script/render agents. Runs the 10-stage
integrated workflow and writes PIPELINE_STATUS.json.
"""

from __future__ import annotations

from engines.contracts import ContractEngine


class ProductionPipelineEngine(ContractEngine):
    key = "production_pipeline"
    label = "Production Pipeline"
    icon = "🔗"
    description = (
        "Integration layer — Research → Psychology → Studio Director → Script → "
        "Scenes → Media → Voice → Assembly → QC → Export with PIPELINE_STATUS.json."
    )
    version = "1.0.0"
    input_contract = ["command"]
    output_contract = ["production_pipeline_summary", "pipeline_status"]
    dependencies = []
    capabilities = [
        "pipeline-integration",
        "orchestration",
        "structured-logging",
        "pipeline-status",
        "contract-bridging",
    ]

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        # Lazy import avoids engines ↔ workflows circular import at registry load.
        from services.production_pipeline.orchestrator import run_production_pipeline

        command = str(context.get("command") or context.get("subject") or "").strip()
        if not command:
            return {
                "production_pipeline_summary": {
                    "status": "no_command",
                    "reason": "command required",
                    "version": self.version,
                },
                "pipeline_status": {},
            }

        result = run_production_pipeline(
            command,
            production_id=str(context.get("production_id") or context.get("project_id") or ""),
            platform=str(context.get("platform") or "youtube_shorts"),
            context=context,
            stop_on_failure=bool(context.get("stop_on_failure", True)),
        )
        summary = {
            "status": "succeeded" if result.get("succeeded") else "failed",
            "production_id": result.get("production_id"),
            "elapsed_ms": result.get("elapsed_ms"),
            "validation_score": result.get("validation_score"),
            "current_stage": result.get("current_stage"),
            "status_path": result.get("status_path"),
            "stages": len(result.get("stage_summaries") or []),
            "version": self.version,
            "agent_verification_ok": (result.get("agent_verification") or {}).get("ok"),
        }
        updates = dict(result.get("context") or {})
        updates["production_pipeline_summary"] = summary
        updates["pipeline_status"] = result.get("pipeline_status") or {}
        updates["production_pipeline_result"] = {
            "production_id": result.get("production_id"),
            "status_path": result.get("status_path"),
            "stage_summaries": result.get("stage_summaries"),
            "succeeded": result.get("succeeded"),
        }
        return updates
