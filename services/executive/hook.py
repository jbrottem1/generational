"""Executive orchestrator hook — runs executive stage after pipeline completion."""

from __future__ import annotations

from core.log import get_logger, log_event
from services.orchestrator.hooks import OrchestratorHook

logger = get_logger(__name__)

_hooks: list = []


class ExecutiveOrchestratorHook(OrchestratorHook):
    """Agent 24 — company OS layer triggered after pipeline runs."""

    kind = "learning"
    name = "agent24-executive"

    def on_pipeline_complete(self, result) -> None:
        from services.orchestrator import get_orchestrator

        report = get_orchestrator().run_executive_stage(result.context)
        log_event(
            logger, "executive.hook_ran",
            status=report.status,
            decisions=result.context.get("executive_summary", {}).get("decisions", 0),
        )


def attach_executive_hook() -> dict:
    """Attach the executive hook (idempotent)."""
    from services.orchestrator import attach_hook

    if not _hooks:
        hook = ExecutiveOrchestratorHook()
        attach_hook(hook)
        _hooks.append(hook)
        log_event(logger, "executive.hook_attached", name=hook.name)
    return {"hooks": [hook.name for hook in _hooks]}


def detach_executive_hook() -> None:
    from services.orchestrator import detach_hook

    while _hooks:
        detach_hook(_hooks.pop())
