"""Clothing physics — fabric responds to body, gravity, wind."""

from __future__ import annotations

from typing import Any

from services.physics_interaction.models import CLOTHING_FORCES


def build_clothing_physics(character_id: str = "DOCTOR_001") -> dict[str, Any]:
    return {
        "character_id": str(character_id).upper(),
        "forces": list(CLOTHING_FORCES),
        "simulate_as_fabric": True,
        "layers": [
            {"id": "base", "stiffness": 0.7, "damping": 0.5},
            {"id": "coat", "stiffness": 0.45, "damping": 0.4, "wind_response": 0.65},
            {"id": "sleeves", "stiffness": 0.5, "damping": 0.45, "follows": "arms"},
        ],
        "responds_to": ["walk", "run", "turn", "sit", "wind", "gravity", "body_collision"],
        "body_collision": True,
        "forbid": ["frozen_fabric", "fabric_leads_body", "clipping_into_limbs"],
        "compose_wardrobe_profile": True,
    }
