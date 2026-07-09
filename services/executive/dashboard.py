"""ExecutiveDashboard — operational view for the company OS layer."""

from __future__ import annotations

from services.executive.models import EXECUTIVE_ENGINE_VERSION, _now_iso


class ExecutiveDashboard:
    """Aggregate plan, health, decisions, and engine inventory."""

    def build(self, plan: dict, health: dict, resource_plan: dict) -> dict:
        decisions = plan.get("decisions") or []
        goals = plan.get("goals") or []

        return {
            "engine_version": EXECUTIVE_ENGINE_VERSION,
            "health": health,
            "kpis": health.get("kpis", {}),
            "decisions_queue": decisions[:10],
            "goals": goals,
            "engine_inventory": {
                "discovered": resource_plan.get("engines_discovered", 0),
                "ready": resource_plan.get("engines_ready", 0),
            },
            "vision": plan.get("vision", ""),
            "top_priorities": plan.get("priorities", [])[:5],
            "generated_at": _now_iso(),
        }
