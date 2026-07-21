"""Hand system — fingers, grips, gesture libraries."""

from __future__ import annotations

from typing import Any

from services.character_rig_studio.models import HAND_CAPABILITIES

GESTURE_LIBRARY = (
    "open_palm_teach",
    "point_index",
    "ok_precision",
    "hold_tool",
    "hold_book",
    "hologram_touch",
    "writing_grip",
    "medical_demo_pinch",
    "reassure_rest",
    "typing_home_row",
)


def build_hand_system(
    character_id: str,
    *,
    existing_gestures: dict[str, Any] | list | None = None,
) -> dict[str, Any]:
    cid = str(character_id).upper()
    gestures = list(GESTURE_LIBRARY)
    if isinstance(existing_gestures, dict):
        for g in existing_gestures.get("gestures") or existing_gestures.get("favorites") or []:
            if g not in gestures:
                gestures.append(str(g))
    elif isinstance(existing_gestures, list):
        for g in existing_gestures:
            if g not in gestures:
                gestures.append(str(g))

    return {
        "character_id": cid,
        "capabilities": list(HAND_CAPABILITIES),
        "fingers_per_hand": 5,
        "joints_per_finger": 3,
        "grip_presets": [
            "relaxed",
            "precision_pinch",
            "power_grip",
            "tool_grip",
            "book_cradle",
            "hologram_point",
            "writing",
        ],
        "gesture_library": gestures,
        "object_interaction": True,
        "left_right_independent": True,
        "forbid_mitten_hands": True,
        "forbid_floating_props": True,
        "reusable": True,
        "existing_ref": "HAND_POSE_LIBRARY.json" if existing_gestures else None,
    }
