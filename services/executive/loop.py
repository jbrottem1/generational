"""ExecutiveLoop — observe→analyze→prioritize→plan→delegate→execute→review→learn→optimize→repeat.

The execute phase DELEGATES to the orchestrator only — never runs engines.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from services.executive.memory import ExecutiveMemory, get_executive_memory
from services.executive.models import EXECUTIVE_ENGINE_VERSION, LOOP_PHASES, _now_iso
from services.executive.planner import ExecutivePlanner
from services.executive.scheduler import ExecutiveScheduler

logger = get_logger(__name__)


class ExecutiveLoop:
    """One full executive operating cycle."""

    def __init__(self, memory: "ExecutiveMemory | None" = None) -> None:
        self._planner = ExecutivePlanner()
        self._scheduler = ExecutiveScheduler()
        self._memory = memory or get_executive_memory()
        self._phases_completed: list = []

    def run(self, context: dict, orchestrator=None) -> dict:
        plan = None
        delegations: list = []
        learnings: list = []

        for phase in LOOP_PHASES:
            self._phases_completed.append(phase)
            if phase == "observe":
                observations = self._planner.observe(context)
                context["_executive_observations"] = observations
            elif phase == "analyze":
                context["_executive_analysis"] = {
                    "signals": len(context.get("market_opportunities") or []),
                }
            elif phase == "prioritize":
                pass  # handled in plan
            elif phase == "plan":
                plan = self._planner.plan(context)
            elif phase == "delegate":
                schedule = self._scheduler.schedule(plan.get("roadmap", {}), context)
                context["executive_schedule"] = schedule
            elif phase == "execute":
                delegations = self._delegate(context, plan, orchestrator)
            elif phase == "review":
                context["_executive_review"] = {"delegations": len(delegations)}
            elif phase == "learn":
                learnings = self._learn(plan, delegations)
                for item in learnings:
                    self._memory.remember("loop_learning", item)
            elif phase == "optimize":
                self._memory.snapshot("last_plan", plan or {})
            elif phase == "repeat":
                break

        current_phase = self._phases_completed[-1] if self._phases_completed else "observe"
        loop_result = {
            "engine_version": EXECUTIVE_ENGINE_VERSION,
            "phase": current_phase,
            "phases_completed": list(self._phases_completed),
            "delegations": delegations,
            "observations": context.get("_executive_observations", {}),
            "learnings": learnings,
            "generated_at": _now_iso(),
        }

        log_event(
            logger, "executive.loop_completed",
            phase=current_phase, delegations=len(delegations),
        )
        return loop_result

    def _delegate(self, context: dict, plan: dict, orchestrator) -> list:
        """Delegate to orchestrator stage runners — never invoke engines directly."""
        if orchestrator is None:
            return []

        delegations = []
        decisions = (plan or {}).get("decisions") or []
        stages_seen: set = set()

        for decision in decisions[:3]:
            stage = decision.get("delegated_stage") or ""
            if not stage or stage in stages_seen:
                continue
            stages_seen.add(stage)
            method = f"run_{stage}_stage"
            runner = getattr(orchestrator, method, None)
            if not callable(runner):
                delegations.append({"stage": stage, "status": "skipped", "reason": "no runner"})
                continue
            try:
                report = runner(context)
                delegations.append({
                    "stage": stage,
                    "status": getattr(report, "status", "unknown"),
                    "decision_id": decision.get("decision_id"),
                })
            except Exception as exc:  # noqa: BLE001 - delegation must not crash loop
                delegations.append({"stage": stage, "status": "failed", "error": str(exc)[:120]})
                log_event(logger, "executive.delegate_failed", stage=stage, error=str(exc)[:120])

        return delegations

    def _learn(self, plan: dict, delegations: list) -> list:
        learnings = []
        if plan:
            learnings.append({
                "type": "plan_snapshot",
                "decisions": len(plan.get("decisions") or []),
                "vision": plan.get("vision", "")[:120],
            })
        for delegation in delegations:
            learnings.append({"type": "delegation", **delegation})
        return learnings
