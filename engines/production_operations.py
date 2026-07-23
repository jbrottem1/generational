"""Production Operations Engine — thin Agent 0 command-center adapter."""

from __future__ import annotations

from engines.contracts import ContractEngine


class ProductionOperationsEngine(ContractEngine):
    key = "production_operations"
    label = "Production Operations"
    icon = "🎬"
    description = (
        "AI Studio command center — prompt → 16 monitored stages → export "
        "validation → production report → history (never aborts on stage failure)."
    )
    version = "1.0.0"
    input_contract = ["command"]
    output_contract = ["production_operations_summary", "production_report"]
    dependencies = []
    capabilities = [
        "studio-ops",
        "orchestration",
        "monitoring",
        "auto-recovery",
        "production-report",
        "production-queue",
        "export-validation",
    ]

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        # Lazy import avoids engines ↔ workflows circular import at registry load.
        from services.production_operations.orchestrator import run_studio_ops
        from services.production_operations.queue import ensure_ops_queue_handler

        ensure_ops_queue_handler()
        brief = context.get("studio_brief") if isinstance(context.get("studio_brief"), dict) else {}
        command = str(context.get("command") or brief.get("command") or "").strip()
        topic = str(context.get("topic") or brief.get("topic") or "")
        if not command and not topic:
            return {
                "production_operations_summary": {
                    "status": "no_input",
                    "reason": "command or topic required",
                    "version": self.version,
                },
                "production_report": {},
            }

        result = run_studio_ops(
            topic=topic or "",
            platform=str(context.get("platform") or brief.get("platform") or "youtube_shorts"),
            length_sec=int(context.get("video_length_sec") or brief.get("length_sec") or 60),
            style=str(context.get("style") or brief.get("style") or "educational"),
            narrator=str(context.get("narration_style") or brief.get("narrator") or "professor"),
            voice=str(context.get("voice_preference") or brief.get("voice") or "default"),
            quality_target=float(context.get("quality_target") or brief.get("quality_target") or 98),
            constraints=context.get("ops_constraints") if isinstance(context.get("ops_constraints"), dict) else {},
            command=command,
            production_id=str(context.get("production_id") or ""),
            context=context,
        )
        updates = dict(result.get("context") or {})
        updates["production_operations_summary"] = {
            "status": "succeeded",
            "production_id": result.get("production_id"),
            "elapsed_ms": result.get("elapsed_ms"),
            "recommendation": result.get("recommendation"),
            "report_path": result.get("report_path"),
            "version": self.version,
        }
        updates["production_report"] = result.get("report") or {}
        updates["production_ops_dashboard"] = result.get("dashboard") or {}
        updates["pipeline_status"] = result.get("status") or {}
        return updates
