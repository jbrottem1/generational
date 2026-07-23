"""Per-scene Environment Packages — World Builder output contract.

Does NOT include final camera movement, framing, lighting treatment, or edit transitions.
Those belong to AI Cinematic Director.
"""

from __future__ import annotations

from typing import Any

from services.world_builder.assets import build_asset_requirements
from services.world_builder.models import PACKAGE_VERSION, WORLD_SCHEMA_VERSION
from services.world_builder.state import continuity_snapshot


def build_environment_package(
    world: dict[str, Any],
    *,
    scene: dict[str, Any] | None = None,
    zone_id: str = "",
    state: dict[str, Any] | None = None,
    request: dict[str, Any] | None = None,
    temporary_objects: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Structured Environment Package for one scene."""
    scene = dict(scene or {})
    request = dict(request or {})
    zones = [z for z in (world.get("zones") or []) if isinstance(z, dict)]
    zone = None
    if zone_id:
        zone = next((z for z in zones if z.get("id") == zone_id), None)
    if zone is None and zones:
        zone = zones[0]
    zone = zone or {
        "id": "main",
        "name": "Primary zone",
        "description": (world.get("environment") or {}).get("description") or world.get("name"),
    }

    persistent: list[dict[str, Any]] = []
    for obj in list(world.get("objects") or []) + list(world.get("furniture") or []):
        if not isinstance(obj, dict):
            continue
        if obj.get("temporary"):
            continue
        if (
            zone.get("id")
            and obj.get("zone")
            and obj.get("zone") not in ("", None, zone.get("id"))
            and not obj.get("global")
        ):
            continue
        row = dict(obj)
        if state and row.get("object_id") in (state.get("object_positions") or {}):
            st = state["object_positions"][row["object_id"]]
            row["position"] = st.get("position") or row.get("position")
            row["zone"] = st.get("zone") or row.get("zone")
        persistent.append(row)

    temps = list(temporary_objects or [])
    for name in request.get("required_objects") or []:
        if not any(str(p.get("name")).lower() == str(name).lower() for p in persistent + temps):
            temps.append(
                {
                    "name": name,
                    "temporary": True,
                    "surface": "floor",
                    "anchored": True,
                    "zone": zone.get("id"),
                }
            )

    layout = {
        "zone_id": zone.get("id"),
        "zone_name": zone.get("name"),
        "description": zone.get("description") or zone.get("name"),
        "landmarks": zone.get("landmarks") or world.get("landmarks") or [],
        "entrances": zone.get("entrances") or [],
        "exits": zone.get("exits") or [],
        "connections": zone.get("connections") or [],
        "scale": world.get("scale"),
    }

    next_zones = zone.get("connections") or []
    recommended = next_zones[0] if next_zones else (zones[1]["id"] if len(zones) > 1 else zone.get("id"))

    assets = build_asset_requirements(world, zone_id=str(zone.get("id") or ""), topic=str(request.get("topic") or ""))

    aesthetic = {
        "base_palette": world.get("color_palette") or (world.get("aesthetic") or {}).get("palette"),
        "materials": (world.get("aesthetic") or {}).get("materials") or world.get("materials") or [],
        "textures": (world.get("aesthetic") or {}).get("textures") or [],
        "era": ((world.get("aesthetic") or {}).get("era") or ((world.get("time_periods") or [""])[0])),
        "design_language": (world.get("aesthetic") or {}).get("design_language") or world.get("theme") or "",
        "brand_compatibility": (world.get("aesthetic") or {}).get("brand_compatibility")
        or world.get("channel_identity")
        or "",
        "ambient_practicals": world.get("ambient_practicals") or [],
        "note": "Context for Cinematic Director — final lighting/camera owned elsewhere",
    }

    ambience = {
        "labels": world.get("sound_ambience") or world.get("ambience") or [],
        "zone_ambience": zone.get("ambience") or [],
        "handoff_to": "sound_design",
        "note": "Environmental context only — not final audio mix",
    }

    return {
        "package_version": PACKAGE_VERSION,
        "package_type": "environment",
        "world_id": world.get("world_id"),
        "world_version": str(world.get("schema_version") or world.get("version") or WORLD_SCHEMA_VERSION),
        "environment_name": world.get("name"),
        "selected_zone": zone.get("id"),
        "zone": zone,
        "scene_id": scene.get("scene_id") or request.get("scene_id") or "",
        "spatial_layout": layout,
        "required_persistent_objects": persistent,
        "required_temporary_objects": temps,
        "background_activity": zone.get("ambient_activity") or world.get("background_animations") or [],
        "environmental_ambience": ambience,
        "scale": world.get("scale"),
        "continuity_state": continuity_snapshot(state) if state else {},
        "scientific_constraints": world.get("scientific_constraints") or request.get("scientific_constraints") or [],
        "historical_constraints": world.get("historical_constraints") or request.get("historical_constraints") or [],
        "accuracy": world.get("accuracy") or {},
        "allowed_subject_positions": zone.get("allowed_subject_positions")
        or world.get("allowed_subject_positions")
        or [],
        "restricted_areas": zone.get("restricted_areas") or world.get("restricted_areas") or [],
        "recommended_transition_destination": recommended,
        "asset_requirements": assets,
        "aesthetic_context": aesthetic,
        "cinematic_prescriptions": None,
        "ownership": {
            "world_builder": "environment_continuity_spatial_objects",
            "scene_builder": "scene_purpose_subjects_actions_duration",
            "cinematic_director": "camera_framing_lighting_treatment_motion_pacing",
            "renderer": "technical_render",
        },
    }
