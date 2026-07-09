"""ExecutiveScheduler — calendar and queue scheduling for executive actions."""

from __future__ import annotations

from services.executive.models import _now_iso


class ExecutiveScheduler:
    """Schedule roadmap items without executing pipeline stages."""

    def schedule(self, roadmap: dict, context: dict) -> dict:
        queue = roadmap.get("priority_queue") or roadmap.get("items") or []
        calendar = roadmap.get("calendar") or []

        scheduled = []
        for idx, item in enumerate(queue[:10]):
            scheduled.append({
                "item_id": item.get("item_id"),
                "decision_id": item.get("decision_id"),
                "title": item.get("title"),
                "slot": idx + 1,
                "stage": item.get("stage", "research"),
                "mode": context.get("publish_mode", "scheduled"),
            })

        return {
            "scheduled_items": scheduled,
            "calendar_entries": len(calendar),
            "next_action": scheduled[0] if scheduled else {},
            "generated_at": _now_iso(),
        }
