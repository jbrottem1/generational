"""Executive Intelligence — Agent 24's company OS layer.

Observes shared context, plans strategy, allocates resources, and delegates
execution to the orchestrator. Never imports or calls peer engines directly.
"""

from services.executive.hook import (
    ExecutiveOrchestratorHook,
    attach_executive_hook,
    detach_executive_hook,
)
from services.executive.models import (
    EXECUTIVE_DECISION_FIELDS,
    EXECUTIVE_ENGINE_VERSION,
    EXECUTIVE_GOAL_FIELDS,
    EXECUTIVE_PACKAGE_FIELDS,
    EXECUTIVE_PACKAGE_VERSION,
    EXECUTIVE_SUMMARY_FIELDS,
    DecisionStatus,
    ExecutiveDecision,
    ExecutiveGoal,
    GoalStatus,
    HealthLevel,
    LOOP_PHASES,
    ReportKind,
)
from services.executive.package import (
    build_executive_package,
    collect_executive_items,
    run_executive_engine,
)

__all__ = [
    "EXECUTIVE_DECISION_FIELDS",
    "EXECUTIVE_ENGINE_VERSION",
    "EXECUTIVE_GOAL_FIELDS",
    "EXECUTIVE_PACKAGE_FIELDS",
    "EXECUTIVE_PACKAGE_VERSION",
    "EXECUTIVE_SUMMARY_FIELDS",
    "DecisionStatus",
    "ExecutiveDecision",
    "ExecutiveGoal",
    "ExecutiveOrchestratorHook",
    "GoalStatus",
    "HealthLevel",
    "LOOP_PHASES",
    "ReportKind",
    "attach_executive_hook",
    "build_executive_package",
    "collect_executive_items",
    "detach_executive_hook",
    "run_executive_engine",
]
