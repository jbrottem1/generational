"""Data contracts for the Executive Intelligence Engine (Agent 24).

Field tuples are the testable contract. Everything emitted is JSON-safe dicts.
Additive-only from 1.0 on (DATA_CONTRACTS.md).
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

EXECUTIVE_ENGINE_VERSION = "1.0.0"
EXECUTIVE_PACKAGE_VERSION = "1.0"


class DecisionStatus:
    """Lifecycle of one executive decision."""

    PROPOSED = "proposed"
    APPROVED = "approved"
    DEFERRED = "deferred"
    REJECTED = "rejected"
    COMPLETED = "completed"

    ALL = (PROPOSED, APPROVED, DEFERRED, REJECTED, COMPLETED)


class GoalStatus:
    """Lifecycle of one executive goal."""

    ACTIVE = "active"
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    ACHIEVED = "achieved"
    PAUSED = "paused"

    ALL = (ACTIVE, ON_TRACK, AT_RISK, ACHIEVED, PAUSED)


class HealthLevel:
    """Company health signal bands."""

    CRITICAL = "critical"
    WARNING = "warning"
    STABLE = "stable"
    GROWING = "growing"
    THRIVING = "thriving"

    ALL = (CRITICAL, WARNING, STABLE, GROWING, THRIVING)


class ReportKind:
    """Executive report types."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    CAMPAIGN = "campaign"
    GROWTH = "growth"
    EXECUTIVE_SUMMARY = "executive_summary"
    PRODUCTION = "production"
    FINANCIAL = "financial"

    ALL = (
        DAILY, WEEKLY, MONTHLY, QUARTERLY, ANNUAL,
        CAMPAIGN, GROWTH, EXECUTIVE_SUMMARY, PRODUCTION, FINANCIAL,
    )


LOOP_PHASES = (
    "observe",
    "analyze",
    "prioritize",
    "plan",
    "delegate",
    "execute",
    "review",
    "learn",
    "optimize",
    "repeat",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str = "exec") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


EXECUTIVE_DECISION_FIELDS = (
    "decision_id",
    "title",
    "topic",
    "platform",
    "status",              # DecisionStatus value
    "roi_score",           # 0-100 expected return
    "views_estimate",      # projected views
    "retention_estimate",  # 0-100 projected retention
    "cost_estimate",       # relative cost units
    "revenue_estimate",    # relative revenue units
    "risk_score",          # 0-100 (higher = riskier)
    "confidence",          # 0-100
    "priority",            # 0-100
    "rationale",
    "delegated_stage",     # orchestrator stage to invoke (never an engine key)
    "generated_at",
)

EXECUTIVE_GOAL_FIELDS = (
    "goal_id",
    "title",
    "description",
    "status",              # GoalStatus value
    "target_metric",
    "target_value",
    "current_value",
    "deadline",
    "priority",
    "owner",
    "generated_at",
)

EXECUTIVE_PACKAGE_FIELDS = (
    "executive_package_version",
    "engine_version",
    "project_id",
    "decisions",           # list of EXECUTIVE_DECISION_FIELDS dicts
    "goals",               # list of EXECUTIVE_GOAL_FIELDS dicts
    "strategy_snapshot",
    "risk_summary",
    "resource_allocation",
    "roadmap_slice",
    "health_snapshot",
    "validation",
    "generated_at",
)

EXECUTIVE_SUMMARY_FIELDS = (
    "engine_version",
    "status",              # planned | no_context | active | degraded
    "items",
    "packages",
    "decisions",
    "goals_active",
    "health_level",
    "average_priority",
    "average_confidence",
    "engines_discovered",
    "generated_at",
)

EXECUTIVE_PLAN_FIELDS = (
    "engine_version",
    "vision",
    "priorities",
    "decisions",
    "roadmap",
    "resource_plan",
    "generated_at",
)

EXECUTIVE_DASHBOARD_FIELDS = (
    "engine_version",
    "health",
    "kpis",
    "decisions_queue",
    "goals",
    "engine_inventory",
    "generated_at",
)

EXECUTIVE_REPORTS_FIELDS = (
    "engine_version",
    "reports",             # ReportKind → report dict
    "generated_at",
)

EXECUTIVE_LOOP_FIELDS = (
    "engine_version",
    "phase",               # current LOOP_PHASES value
    "phases_completed",
    "delegations",         # stage names delegated to orchestrator
    "observations",
    "learnings",
    "generated_at",
)


@dataclass
class ExecutiveDecision:
    """What the company should produce next — scored for ROI and risk."""

    decision_id: str = field(default_factory=lambda: new_id("dec"))
    title: str = ""
    topic: str = ""
    platform: str = ""
    status: str = DecisionStatus.PROPOSED
    roi_score: int = 0
    views_estimate: int = 0
    retention_estimate: int = 0
    cost_estimate: int = 0
    revenue_estimate: int = 0
    risk_score: int = 0
    confidence: int = 0
    priority: int = 0
    rationale: str = ""
    delegated_stage: str = ""
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ExecutiveGoal:
    """Strategic objective tracked by the executive layer."""

    goal_id: str = field(default_factory=lambda: new_id("goal"))
    title: str = ""
    description: str = ""
    status: str = GoalStatus.ACTIVE
    target_metric: str = ""
    target_value: int = 0
    current_value: int = 0
    deadline: str = ""
    priority: int = 0
    owner: str = "executive"
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return asdict(self)
