"""ExecutiveRoadmap — items, dependencies, priority queue, calendar, milestones."""

from __future__ import annotations

from services.executive.models import _now_iso, new_id


class ExecutiveRoadmap:
    """Build a strategic roadmap from executive decisions."""

    def build(self, decisions: list, context: dict) -> dict:
        items = []
        for idx, decision in enumerate(decisions[:20]):
            items.append({
                "item_id": new_id("road"),
                "decision_id": decision.get("decision_id"),
                "title": decision.get("title"),
                "priority": decision.get("priority", 0),
                "dependencies": self._dependencies(idx, decisions),
                "stage": decision.get("delegated_stage", "research"),
                "status": "queued",
            })

        calendar = self._calendar(items, context)
        milestones = self._milestones(decisions)

        return {
            "items": items,
            "priority_queue": sorted(items, key=lambda i: i["priority"], reverse=True),
            "dependencies": {i["item_id"]: i["dependencies"] for i in items},
            "calendar": calendar,
            "milestones": milestones,
            "generated_at": _now_iso(),
        }

    def slice_for_item(self, roadmap: dict, decision_id: str) -> dict:
        item = next((i for i in roadmap.get("items", []) if i.get("decision_id") == decision_id), {})
        return {
            "item": item,
            "queue_position": next(
                (idx + 1 for idx, q in enumerate(roadmap.get("priority_queue", []))
                 if q.get("decision_id") == decision_id),
                0,
            ),
        }

    def _dependencies(self, idx: int, decisions: list) -> list:
        if idx == 0:
            return []
        prev = decisions[idx - 1].get("decision_id")
        return [prev] if prev else []

    def _calendar(self, items: list, context: dict) -> list:
        base = context.get("market_roadmap", {}).get("calendar") or []
        if base:
            return base[:14]
        return [
            {"day": day + 1, "item_id": item.get("item_id"), "title": item.get("title")}
            for day, item in enumerate(items[:7])
        ]

    def _milestones(self, decisions: list) -> list:
        if not decisions:
            return [{"milestone_id": new_id("ms"), "title": "Establish baseline metrics", "target": 30}]
        top = decisions[0]
        return [
            {
                "milestone_id": new_id("ms"),
                "title": f"Launch: {top.get('title', 'flagship')[:60]}",
                "target_priority": top.get("priority", 0),
            },
            {
                "milestone_id": new_id("ms"),
                "title": "Review portfolio ROI",
                "target_priority": 70,
            },
        ]
