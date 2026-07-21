"""Object physics — mass, CoG, collision, friction, interaction zones."""

from __future__ import annotations

from typing import Any

from services.physics_interaction.models import OBJECT_PROPERTIES

_OBJECT_PRESETS: dict[str, dict[str, Any]] = {
    "microscope": {"mass_kg": 4.5, "material": "metal_glass", "friction": 0.65, "holdable": False},
    "book": {"mass_kg": 0.45, "material": "paper_board", "friction": 0.55, "holdable": True},
    "tool": {"mass_kg": 0.35, "material": "metal_polymer", "friction": 0.6, "holdable": True},
    "stylus": {"mass_kg": 0.02, "material": "polymer", "friction": 0.4, "holdable": True},
    "door": {"mass_kg": 35.0, "material": "wood_metal", "friction": 0.5, "holdable": False},
    "chair": {"mass_kg": 8.0, "material": "wood_fabric", "friction": 0.7, "holdable": False},
    "desk": {"mass_kg": 40.0, "material": "wood_metal", "friction": 0.75, "holdable": False},
    "whiteboard": {"mass_kg": 18.0, "material": "composite", "friction": 0.5, "holdable": False},
    "hologram": {"mass_kg": 0.0, "material": "volumetric_light", "friction": 0.0, "holdable": False, "collision": False},
    "console": {"mass_kg": 12.0, "material": "metal_glass", "friction": 0.6, "holdable": False},
    "screen": {"mass_kg": 3.0, "material": "glass_polymer", "friction": 0.45, "holdable": False},
    "button": {"mass_kg": 0.05, "material": "polymer", "friction": 0.5, "holdable": False},
    "default": {"mass_kg": 1.0, "material": "generic", "friction": 0.5, "holdable": True},
}


def build_object_physics(
    object_id: str,
    *,
    object_type: str = "default",
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    preset = dict(_OBJECT_PRESETS.get(object_type, _OBJECT_PRESETS["default"]))
    if overrides:
        preset.update(overrides)
    collides = preset.get("collision", True)
    return {
        "object_id": object_id,
        "object_type": object_type,
        "properties_required": list(OBJECT_PROPERTIES),
        "mass_kg": float(preset["mass_kg"]),
        "center_of_gravity": [0.0, 0.1, 0.0],
        "collision_volume": {
            "shape": "box" if collides else "none",
            "enabled": bool(collides),
        },
        "material": preset["material"],
        "friction": float(preset["friction"]),
        "interaction_zones": [
            {"id": "primary", "radius_m": 0.15, "actions": ["touch", "grasp", "use"]},
            {"id": "approach", "radius_m": 0.9, "actions": ["approach"]},
        ],
        "holdable": bool(preset.get("holdable")),
        "forbid_float": collides,
        "forbid_clip_through": collides,
    }


def build_objects_from_stage(stage_world: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Derive object physics from stage geometry props/furniture."""
    stage = stage_world or {}
    # Accept full WORLD_PACKAGE or slim stage_world_package
    geom = stage.get("geometry") or {}
    points = (stage.get("interaction_points") or {}).get("points") or []
    objects: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in list(geom.get("furniture") or []) + list(geom.get("props") or []):
        oid = str(item.get("id") or item.get("type"))
        if oid in seen:
            continue
        seen.add(oid)
        objects.append(
            build_object_physics(
                oid,
                object_type=str(item.get("type") or "default"),
                overrides={"collision": bool(item.get("collision", True))},
            )
        )

    for pt in points:
        oid = str(pt.get("target_id") or pt.get("id"))
        if oid in seen:
            continue
        seen.add(oid)
        objects.append(
            build_object_physics(oid, object_type=str(pt.get("target_type") or "default"))
        )

    if not objects:
        for t in ("microscope", "door", "whiteboard", "chair", "desk"):
            objects.append(build_object_physics(f"default_{t}", object_type=t))
    return objects
