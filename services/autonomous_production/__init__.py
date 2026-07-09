"""Autonomous Production Executor (Agent 23).

Coordinates complete media productions from a single user request via
WorkflowExecutor → Orchestrator. Does not call engines or providers directly.

    from services.autonomous_production import get_production_executor

    executor = get_production_executor()
    job = executor.execute("Create a 45-second YouTube Short about black holes.")
    status = executor.get_status(job.job_id)
"""

from services.autonomous_production.executor import (
    PRODUCTION_JOB_TYPE,
    AutonomousProductionExecutor,
    ensure_production_handler,
    execute_production,
    get_production_executor,
    reset_production_executor,
)
from services.autonomous_production.models import (
    Checkpoint,
    ExecutionContext,
    ExecutionState,
    ProductionJob,
    ProductionManifest,
    ProductionSummary,
    StageResult,
)
from services.autonomous_production.modes import (
    PRODUCTION_MODES,
    resolve_production_mode,
)
from services.autonomous_production.observability import execution_log, progress_snapshot
from services.autonomous_production.scheduler import schedule_job
from services.autonomous_production.store import (
    ProductionJobStore,
    get_production_store,
    reset_production_store,
)

__all__ = [
    "PRODUCTION_JOB_TYPE",
    "PRODUCTION_MODES",
    "AutonomousProductionExecutor",
    "Checkpoint",
    "ExecutionContext",
    "ExecutionState",
    "ProductionJob",
    "ProductionJobStore",
    "ProductionManifest",
    "ProductionSummary",
    "StageResult",
    "ensure_production_handler",
    "execute_production",
    "execution_log",
    "get_production_executor",
    "get_production_store",
    "progress_snapshot",
    "reset_production_executor",
    "reset_production_store",
    "resolve_production_mode",
    "schedule_job",
]
