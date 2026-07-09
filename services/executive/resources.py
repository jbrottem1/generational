"""ExecutiveResourceAllocator — discover engines and plan budgets.

Uses registry.describe_all() via lazy import. NEVER executes engines.
"""

from __future__ import annotations

from services.executive.models import _now_iso


class ExecutiveResourceAllocator:
    """Map available engines to budget allocations for the executive plan."""

    def discover(self) -> list:
        """Lazy registry discovery — no peer engine imports."""
        from engines import registry  # noqa: WPS433 - lazy import by design

        return registry.describe_all()

    def allocate(self, context: dict, decisions: list) -> dict:
        engines = self.discover()
        ready = [e for e in engines if e.get("ready")]
        budget_total = int(context.get("executive_budget", 100) or 100)

        by_capability: dict = {}
        for info in ready:
            for cap in info.get("capabilities", []):
                by_capability.setdefault(cap, []).append(info["engine_id"])

        allocations = []
        per_decision = max(1, budget_total // max(len(decisions), 1))
        for decision in decisions[:10]:
            stage = decision.get("delegated_stage") or "research"
            allocations.append({
                "decision_id": decision.get("decision_id"),
                "stage": stage,
                "budget_units": per_decision,
                "engines_available": self._engines_for_stage(stage, ready),
            })

        return {
            "budget_total": budget_total,
            "engines_discovered": len(engines),
            "engines_ready": len(ready),
            "capability_index_sample": {
                k: v[:5] for k, v in list(sorted(by_capability.items()))[:8]
            },
            "allocations": allocations,
            "generated_at": _now_iso(),
        }

    def _engines_for_stage(self, stage: str, ready: list) -> list:
        from services.orchestrator.stages import get_stage

        keys = set(get_stage(stage))
        return sorted(info["engine_id"] for info in ready if info["engine_id"] in keys)
