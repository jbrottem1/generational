"""Hand physics — fingers, grasp, grip, dual-hand."""

from __future__ import annotations

from typing import Any

from services.physics_interaction.models import HAND_CAPABILITIES


def build_hand_physics(character_id: str = "DOCTOR_001") -> dict[str, Any]:
    return {
        "character_id": str(character_id).upper(),
        "capabilities": list(HAND_CAPABILITIES),
        "fingers": {
            "per_hand": 5,
            "joints_per_finger": 3,
            "independent_articulation": True,
        },
        "grasp": {
            "detection": True,
            "presets": [
                "relaxed",
                "precision_pinch",
                "power_grip",
                "tool_grip",
                "book_cradle",
                "stylus",
                "handshake",
            ],
            "pressure_range": [0.0, 1.0],
            "release_required": True,
        },
        "alignment": {
            "hand_object_snap": True,
            "max_miss_m": 0.02,
            "forbid_missing_targets": True,
        },
        "dual_hand": {
            "enabled": True,
            "modes": ["symmetric", "lead_support", "stabilize_manipulate"],
        },
        "forbid": ["mitten_hands", "clipping_into_mesh", "floating_grip"],
    }
