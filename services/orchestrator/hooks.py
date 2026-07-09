"""Autonomy hooks — the attachment points for future autonomous agents.

Scheduling, publishing, analytics ingestion, and the learning loop are NOT
built yet. These interfaces exist so future agents attach to the orchestrator
without modifying it: implement `OrchestratorHook`, call `attach_hook()`,
and the orchestrator notifies you after every pipeline run.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from core.log import get_logger, log_event

if TYPE_CHECKING:
    from services.orchestrator.models import PipelineResult

logger = get_logger(__name__)

# Recognized hook kinds. Future agents: Scheduler triggers runs, Publisher
# consumes publish-ready packages, Analytics ingests post-publish data,
# Learning retunes weights from outcomes.
HOOK_KINDS = ("scheduler", "publisher", "analytics", "learning")


class OrchestratorHook(ABC):
    """Contract for anything that reacts to completed pipeline runs."""

    kind: str = ""   # one of HOOK_KINDS
    name: str = ""

    @abstractmethod
    def on_pipeline_complete(self, result: "PipelineResult") -> None:
        """Called after every orchestrated run, success or failure."""
        raise NotImplementedError


_hooks: "dict[str, list[OrchestratorHook]]" = {kind: [] for kind in HOOK_KINDS}


def attach_hook(hook: OrchestratorHook) -> None:
    if hook.kind not in _hooks:
        raise ValueError(f"Unknown hook kind: {hook.kind!r} (expected one of {HOOK_KINDS})")
    _hooks[hook.kind].append(hook)
    log_event(logger, "orchestrator.hook_attached", kind=hook.kind, name=hook.name)


def detach_hook(hook: OrchestratorHook) -> None:
    if hook in _hooks.get(hook.kind, []):
        _hooks[hook.kind].remove(hook)


def notify_hooks(result: "PipelineResult") -> None:
    """Fan out a completed run to every attached hook; hooks never crash the pipeline."""
    for kind in HOOK_KINDS:
        for hook in _hooks[kind]:
            try:
                hook.on_pipeline_complete(result)
            except Exception as exc:
                log_event(
                    logger, "orchestrator.hook_failed", level=30,
                    kind=kind, name=hook.name, error=str(exc),
                )
