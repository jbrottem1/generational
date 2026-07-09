"""ExecutiveGoals — strategic objectives for the company OS layer."""

from __future__ import annotations

from services.executive.memory import ExecutiveMemory, get_executive_memory
from services.executive.models import ExecutiveGoal, GoalStatus, new_id


class ExecutiveGoals:
    """Track, score, and persist company goals."""

    def __init__(self, memory: "ExecutiveMemory | None" = None) -> None:
        self._memory = memory or get_executive_memory()
        self._goals: list[ExecutiveGoal] = []

    def load(self) -> list[dict]:
        stored = self._memory.load_snapshot("goals")
        self._goals = [
            ExecutiveGoal(**{k: v for k, v in item.items() if k in ExecutiveGoal.__dataclass_fields__})
            for item in stored.get("items", [])
        ]
        return [g.to_dict() for g in self._goals]

    def save(self) -> None:
        self._memory.snapshot("goals", {"items": [g.to_dict() for g in self._goals]})

    def ensure_defaults(self, context: dict) -> list[dict]:
        if not self._goals:
            self._goals = [
                ExecutiveGoal(
                    goal_id=new_id("goal"),
                    title="Grow audience reach",
                    description="Increase total views across primary platforms",
                    target_metric="views",
                    target_value=100_000,
                    current_value=int(context.get("analytics_summary", {}).get("total_views", 0) or 0),
                    priority=90,
                ),
                ExecutiveGoal(
                    goal_id=new_id("goal"),
                    title="Improve retention",
                    description="Raise average audience retention on flagship content",
                    target_metric="retention",
                    target_value=65,
                    current_value=int(context.get("analytics_summary", {}).get("average_retention", 0) or 0),
                    priority=80,
                ),
            ]
        self._refresh_statuses()
        self.save()
        return [g.to_dict() for g in self._goals]

    def _refresh_statuses(self) -> None:
        for goal in self._goals:
            if goal.target_value <= 0:
                continue
            progress = goal.current_value / goal.target_value
            if progress >= 1.0:
                goal.status = GoalStatus.ACHIEVED
            elif progress >= 0.7:
                goal.status = GoalStatus.ON_TRACK
            elif progress >= 0.4:
                goal.status = GoalStatus.ACTIVE
            else:
                goal.status = GoalStatus.AT_RISK

    def active_count(self) -> int:
        return len([g for g in self._goals if g.status != GoalStatus.ACHIEVED])
