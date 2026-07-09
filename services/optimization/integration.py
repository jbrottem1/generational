"""Pipeline integration — how the laboratory joins the full pipeline.

The `optimization` stage is registered in `STAGE_GROUPS` (manual runs via
`get_orchestrator().run_stage("optimization", context)` always work). One
call to `enable_optimization_stage()` additionally schedules it inside
`run_full_pipeline()` right after the quality gate — the designed
`register_stage()` plugin route, zero orchestrator code changes
(Architecture Directive #1).
"""

from __future__ import annotations

from core.log import get_logger, log_event
from services.orchestrator.stages import STAGE_GROUPS, register_stage, unregister_stage

logger = get_logger(__name__)

OPTIMIZATION_STAGE = "optimization"
OPTIMIZATION_ENGINE_KEYS = ["optimization_lab"]

_scheduled = False


def enable_optimization_stage(after: str = "quality") -> None:
    """Schedule the optimization stage inside the full pipeline (idempotent)."""
    global _scheduled
    if _scheduled:
        return
    register_stage(OPTIMIZATION_STAGE, OPTIMIZATION_ENGINE_KEYS, after=after)
    _scheduled = True
    log_event(logger, "optimization.stage_enabled", after=after)


def disable_optimization_stage() -> None:
    """Remove the scheduled stage (tests / hot-swaps); the manual stage
    group is restored so on-demand runs keep working."""
    global _scheduled
    unregister_stage(OPTIMIZATION_STAGE)
    STAGE_GROUPS[OPTIMIZATION_STAGE] = list(OPTIMIZATION_ENGINE_KEYS)
    _scheduled = False
