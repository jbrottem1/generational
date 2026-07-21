"""Collision contracts — nothing clips, floats, or walks through geometry."""

from __future__ import annotations

from typing import Any

from services.physics_interaction.models import COLLISION_FORBID


def build_collision_system(*, world_id: str | None = None) -> dict[str, Any]:
    return {
        "world_id": world_id,
        "enabled": True,
        "forbid": list(COLLISION_FORBID),
        "layers": {
            "static_world": ["walls", "floors", "ceilings", "furniture"],
            "dynamic_props": ["holdables", "doors"],
            "characters": ["body", "hands", "feet"],
            "cloth_hair": ["coat", "hair"],
        },
        "rules": [
            "characters_collide_with_static_world",
            "hands_collide_with_interactables",
            "feet_constrained_to_floor_plane",
            "props_do_not_interpenetrate",
            "no_body_self_clip_hard",
        ],
        "floor_clamp": True,
        "wall_block": True,
        "hand_penetration_max_m": 0.0,
        "foot_penetration_max_m": 0.0,
    }
