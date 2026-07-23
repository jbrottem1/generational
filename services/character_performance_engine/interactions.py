"""Prop and environment interactions — characters use the world."""

from __future__ import annotations

from typing import Any

from services.character_performance_engine.models import INTERACTION_VERBS


def plan_interactions(
    *,
    objective: dict[str, Any],
    blocking: dict[str, Any],
    duration_sec: float,
    location_hint: str = "lab",
) -> dict[str, Any]:
    touches = list(blocking.get("what_touching") or [])
    oid = str(objective.get("id") or "")
    events: list[dict[str, Any]] = []

    for touch in touches:
        events.append(
            {
                "t": float(touch.get("t") or 1.0),
                "verb": str(touch.get("verb") or "touch"),
                "target": str(touch.get("target") or "prop"),
                "hand": "right",
                "requires_reach": True,
                "requires_body_turn": True,
            }
        )

    # Guarantee at least one physical world use
    if not events:
        events.append(
            {
                "t": min(1.5, max(0.8, duration_sec * 0.4)),
                "verb": "point",
                "target": "hologram" if "lab" in location_hint else "environment_landmark",
                "hand": "right",
                "requires_reach": True,
                "requires_body_turn": True,
            }
        )

    if "equipment" in oid or "lab" in location_hint:
        events.append(
            {
                "t": min(duration_sec * 0.65, duration_sec - 0.4),
                "verb": "look_through_microscope",
                "target": "microscope",
                "hand": "both",
                "requires_reach": True,
                "requires_body_turn": True,
            }
        )
    if "open" in oid:
        events.insert(
            0,
            {
                "t": 0.6,
                "verb": "open_door",
                "target": "lab_door",
                "hand": "left",
                "requires_reach": True,
                "requires_body_turn": True,
            },
        )

    return {
        "events": events,
        "allowed_verbs": list(INTERACTION_VERBS),
        "forbid_talking_head_only": True,
        "must_use_world": True,
        "count": len(events),
    }
