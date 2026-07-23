"""Thin engine adapter — exposes Executive Orchestrator in the registry."""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.base import Engine

logger = get_logger(__name__)


class ExecutiveOrchestratorEngine(Engine):
    key = "executive_orchestrator"
    label = "Executive Orchestrator"
    icon = "🎬"
    description = (
        "One-command AI production studio — parse request, coordinate every subsystem, "
        "run Production QA with auto-revision, export artifacts, and queue publishing."
    )
    version = "1.0.0"

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        # Lazy imports avoid circular load: engines → executive → workflows → engines
        from services.executive_orchestrator.jobs import ensure_executive_handler
        from services.executive_orchestrator.orchestrator import get_executive_orchestrator

        ensure_executive_handler()
        command = str(
            context.get("command")
            or context.get("subject")
            or context.get("topic")
            or ""
        )
        if not command:
            return {"error": "executive_orchestrator requires command/subject"}

        orch = get_executive_orchestrator(
            max_revision_rounds=int(context.get("max_revision_rounds") or 2),
            max_parallel=int(context.get("max_parallel") or 2),
        )
        result = orch.create_video(
            command,
            category=str(context.get("category") or context.get("niche") or "science"),
            max_revision_rounds=context.get("max_revision_rounds"),
            publish_mode=str(context.get("publish_mode") or "scheduled"),
            plan_only=bool(context.get("plan_only") or context.get("executive_plan_only")),
            skip_publishing=bool(context.get("skip_publishing")),
            context_extra={
                k: v
                for k, v in context.items()
                if k
                not in {
                    "command",
                    "subject",
                    "topic",
                    "category",
                    "niche",
                    "max_revision_rounds",
                    "max_parallel",
                    "publish_mode",
                    "plan_only",
                    "executive_plan_only",
                    "skip_publishing",
                }
            },
        )
        log_event(
            logger,
            "executive_orchestrator.engine_completed",
            run_id=result.get("id"),
            status=result.get("status"),
            qa=result.get("qa_score"),
        )
        return {
            "executive_run": result,
            "executive_dashboard": orch.dashboard(),
            "executive_run_id": result.get("id"),
            "executive_status": result.get("status"),
        }
