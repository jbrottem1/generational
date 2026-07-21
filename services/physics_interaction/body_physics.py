"""Body physics — CoG, weight, momentum, balance, secondary motion."""

from __future__ import annotations

from typing import Any

from services.physics_interaction.models import BODY_CAPABILITIES


def build_body_physics(
    character_id: str = "DOCTOR_001",
    *,
    mass_kg: float = 82.0,
    height_cm: float = 185.0,
) -> dict[str, Any]:
    return {
        "character_id": str(character_id).upper(),
        "capabilities": list(BODY_CAPABILITIES),
        "mass_kg": float(mass_kg),
        "height_cm": float(height_cm),
        "center_of_gravity": {
            "default_offset_m": [0.0, height_cm / 200.0, 0.0],
            "shifts_with_pose": True,
        },
        "locomotion": {
            "weight_transfer": True,
            "momentum": True,
            "acceleration": True,
            "deceleration": True,
            "max_walk_mps": 1.4,
            "max_run_mps": 3.2,
            "turn_rate_deg_s": 120.0,
        },
        "balance": {
            "correction": True,
            "recovery_from_lean": True,
            "forbid_weightless": True,
        },
        "rotation": {
            "hip_leads": True,
            "spine_follows": True,
            "head_stabilizes": True,
        },
        "secondary_motion": [
            "soft_tissue",
            "coat_lag",
            "hair_lag",
            "arm_swing_inertia",
        ],
        "forbid": ["float", "teleport_pose", "weightless_movement", "broken_joints"],
        "compose_character_rig_mechanics": True,
    }
