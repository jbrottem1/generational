"""Orchestration layer — one interface over the whole AI Content Operating System.

Public surface:
    from services.orchestrator import get_orchestrator, run_full_pipeline
    from services.orchestrator import ProductionPackage, PipelineResult, StageReport
    from services.orchestrator import register_stage, attach_hook
"""

from services.orchestrator.hooks import HOOK_KINDS, OrchestratorHook, attach_hook, detach_hook
from services.orchestrator.models import (
    CONTENT_PACKAGE_FIELDS,
    PRODUCTION_PACKAGE_FIELDS,
    ContentPackage,
    PipelineResult,
    ProductionPackage,
    StageReport,
    StageStatus,
)
from services.orchestrator.orchestrator import (
    ORCHESTRATOR_JOB_TYPE,
    Orchestrator,
    ensure_orchestrator_handler,
    get_orchestrator,
    run_full_pipeline,
)
from services.orchestrator.stages import (
    STAGE_GROUPS,
    build_pipeline_plan,
    get_stage,
    pipeline_stage_names,
    register_stage,
    unregister_stage,
)

__all__ = [
    "Orchestrator",
    "get_orchestrator",
    "run_full_pipeline",
    "ProductionPackage",
    "ContentPackage",
    "PipelineResult",
    "StageReport",
    "StageStatus",
    "PRODUCTION_PACKAGE_FIELDS",
    "CONTENT_PACKAGE_FIELDS",
    "STAGE_GROUPS",
    "build_pipeline_plan",
    "pipeline_stage_names",
    "register_stage",
    "unregister_stage",
    "get_stage",
    "OrchestratorHook",
    "attach_hook",
    "detach_hook",
    "HOOK_KINDS",
    "ORCHESTRATOR_JOB_TYPE",
    "ensure_orchestrator_handler",
]
