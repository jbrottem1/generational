"""Foot physics — plant, heel-toe, stairs, friction."""

from __future__ import annotations

from typing import Any

from services.physics_interaction.models import FOOT_CAPABILITIES


def build_foot_physics(character_id: str = "DOCTOR_001") -> dict[str, Any]:
    return {
        "character_id": str(character_id).upper(),
        "capabilities": list(FOOT_CAPABILITIES),
        "gait_cycle": {
            "heel_strike": True,
            "midstance": True,
            "toe_roll": True,
            "push_off": True,
        },
        "planting": {
            "required": True,
            "no_slide": True,
            "no_float": True,
            "ik_to_floor": True,
        },
        "terrain": {
            "flat": True,
            "stairs": True,
            "uneven": True,
            "slope_max_deg": 28.0,
        },
        "friction": {
            "static": 0.75,
            "kinetic": 0.55,
            "forbid_ice_slide_default": True,
        },
        "balance": {
            "com_over_support_polygon": True,
            "correction_enabled": True,
        },
        "forbid": ["sliding_feet", "feet_below_floor", "teleport_steps"],
    }
