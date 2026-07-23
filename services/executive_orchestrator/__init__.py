"""Executive Orchestrator — one-command Generational Media OS entry point."""

from __future__ import annotations

from services.executive_orchestrator.jobs import (
    EXECUTIVE_JOB_TYPE,
    ensure_executive_handler,
    submit_executive_job,
)
from services.executive_orchestrator.orchestrator import (
    ExecutiveOrchestrator,
    create_video,
    get_executive_orchestrator,
)
from services.executive_orchestrator.request_parser import ProductionBrief, parse_production_request
from services.executive_orchestrator.stages import EXECUTIVE_STAGES, STAGE_LABELS, stage_plan
from services.executive_orchestrator.state import ProductionRun, get_run_registry

__all__ = [
    "EXECUTIVE_JOB_TYPE",
    "EXECUTIVE_STAGES",
    "STAGE_LABELS",
    "ExecutiveOrchestrator",
    "ProductionBrief",
    "ProductionRun",
    "create_video",
    "ensure_executive_handler",
    "get_executive_orchestrator",
    "get_run_registry",
    "parse_production_request",
    "stage_plan",
    "submit_executive_job",
]
