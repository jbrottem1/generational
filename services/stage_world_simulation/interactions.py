"""Interaction points — every prop advertises usable actions."""

from __future__ import annotations

from typing import Any

from services.stage_world_simulation.models import PROP_INTERACTIONS


def build_interaction_points(geometry: dict[str, Any], *, world_id: str) -> dict[str, Any]:
    points: list[dict[str, Any]] = []

    for item in list(geometry.get("furniture") or []) + list(geometry.get("props") or []):
        ptype = str(item.get("type") or "prop")
        verbs = list(PROP_INTERACTIONS.get(ptype) or ("inspect", "approach"))
        pos = item.get("position") or [0, 0, 0]
        points.append(
            {
                "id": f"interact_{item.get('id')}",
                "target_id": item.get("id"),
                "target_type": ptype,
                "position": pos,
                "actions": verbs,
                "approach_radius_m": 0.9,
                "requires_navigation": True,
            }
        )

    # Always include door interactions from geometry doors
    for door in geometry.get("doors") or []:
        points.append(
            {
                "id": f"interact_{door.get('id')}",
                "target_id": door.get("id"),
                "target_type": "door",
                "position": door.get("position") or [0, 0, 0],
                "actions": list(PROP_INTERACTIONS["door"]),
                "approach_radius_m": 0.8,
                "requires_navigation": True,
            }
        )

    # Ensure mission-critical prop types exist conceptually even if geometry sparse
    present_types = {p["target_type"] for p in points}
    for required in ("chair", "desk", "microscope", "whiteboard", "door"):
        if required not in present_types and required in PROP_INTERACTIONS:
            # Virtual catalog entry for reserved stages that haven't dressed yet
            if required == "door":
                continue
            points.append(
                {
                    "id": f"interact_virtual_{required}",
                    "target_id": f"virtual_{required}",
                    "target_type": required,
                    "position": [0.0, 0.0, 0.0],
                    "actions": list(PROP_INTERACTIONS[required]),
                    "approach_radius_m": 0.9,
                    "requires_navigation": True,
                    "virtual_until_dressed": True,
                }
            )

    catalog = {
        ptype: list(verbs) for ptype, verbs in PROP_INTERACTIONS.items()
    }
    return {
        "world_id": world_id,
        "points": points,
        "count": len(points),
        "action_catalog": catalog,
        "every_prop_advertises_interactions": True,
        "forbid_non_interactive_set_dressing_as_primary": True,
    }
