"""Hair physics — gravity, wind, head motion, secondary movement."""

from __future__ import annotations

from typing import Any

from services.physics_interaction.models import HAIR_FORCES


def build_hair_physics(character_id: str = "DOCTOR_001") -> dict[str, Any]:
    # DOCTOR_001 is often a cyborg with styled/limited hair — still contract-ready
    return {
        "character_id": str(character_id).upper(),
        "forces": list(HAIR_FORCES),
        "enabled": True,
        "strands_or_guides": True,
        "responds_to": ["gravity", "wind", "head_yaw", "head_pitch", "locomotion"],
        "secondary_movement": True,
        "damping": 0.55,
        "stiffness": 0.4,
        "forbid": ["static_helmet_hair", "clipping_into_skull"],
        "compose_hair_profile": True,
    }
