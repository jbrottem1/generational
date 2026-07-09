"""ExecutivePlanner — observe context and build the executive plan."""

from __future__ import annotations

from services.executive.decisions import ExecutiveDecisionEngine
from services.executive.goals import ExecutiveGoals
from services.executive.models import EXECUTIVE_ENGINE_VERSION, _now_iso
from services.executive.resources import ExecutiveResourceAllocator
from services.executive.risk import ExecutiveRiskEngine
from services.executive.roadmap import ExecutiveRoadmap
from services.executive.strategy import ExecutiveStrategy


class ExecutivePlanner:
    """Observe signals and assemble the company operating plan."""

    def __init__(self) -> None:
        self._decisions = ExecutiveDecisionEngine()
        self._strategy = ExecutiveStrategy()
        self._roadmap = ExecutiveRoadmap()
        self._risk = ExecutiveRiskEngine()
        self._resources = ExecutiveResourceAllocator()
        self._goals = ExecutiveGoals()

    def observe(self, context: dict) -> dict:
        """Collect signals available in shared context — never call engines."""
        return {
            "market_opportunities": len(context.get("market_opportunities") or []),
            "unified_packages": len(context.get("unified_packages") or []),
            "analytics_summary": bool(context.get("analytics_summary")),
            "learning_report": bool(context.get("learning_report")),
            "market_roadmap": bool(context.get("market_roadmap")),
            "topic": context.get("topic") or context.get("trend_subject") or "",
        }

    def plan(self, context: dict) -> dict:
        observations = self.observe(context)
        decisions = self._decisions.build_decisions(context)
        strategy = self._strategy.build(context)
        roadmap = self._roadmap.build(decisions, context)
        risk = self._risk.assess(context, decisions)
        resources = self._resources.allocate(context, decisions)
        goals = self._goals.ensure_defaults(context)

        return {
            "engine_version": EXECUTIVE_ENGINE_VERSION,
            "observations": observations,
            "vision": strategy["vision"],
            "priorities": [d["title"] for d in decisions[:5]],
            "decisions": decisions,
            "strategy": strategy,
            "roadmap": roadmap,
            "risk": risk,
            "resource_plan": resources,
            "goals": goals,
            "generated_at": _now_iso(),
        }
