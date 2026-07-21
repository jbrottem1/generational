"""Build actor PHYSICS_PROFILE and scene physics bundles."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.physics_interaction.body_physics import build_body_physics
from services.physics_interaction.clothing_physics import build_clothing_physics
from services.physics_interaction.collision import build_collision_system
from services.physics_interaction.environmental_physics import build_environmental_physics
from services.physics_interaction.foot_physics import build_foot_physics
from services.physics_interaction.hair_physics import build_hair_physics
from services.physics_interaction.hand_physics import build_hand_physics
from services.physics_interaction.interaction import plan_interactions_from_scene
from services.physics_interaction.models import (
    ENGINE_ID,
    PACKAGE_VERSION,
    PHYSICS_PROFILE_TYPE,
    SUPPORTED_INTERACTIONS,
)
from services.physics_interaction.object_physics import build_objects_from_stage
from services.physics_interaction.validation import (
    validate_interaction_package,
    validate_physics_profile,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_physics_profile(
    character_id: str = "DOCTOR_001",
    *,
    world_id: str | None = None,
    stage_world: dict[str, Any] | None = None,
    weather: str = "interior_climate",
    outdoor: bool = False,
    mass_kg: float = 82.0,
    height_cm: float = 185.0,
    interactions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Full physics contract for an actor inside a world."""
    cid = str(character_id).upper()
    objects = build_objects_from_stage(stage_world)
    profile: dict[str, Any] = {
        "package_type": PHYSICS_PROFILE_TYPE,
        "package_version": PACKAGE_VERSION,
        "engine_id": ENGINE_ID,
        "created_at": _now(),
        "character_id": cid,
        "world_id": world_id,
        "philosophy": {
            "not_a_renderer": True,
            "not_an_image_generator": True,
            "not_a_world_builder": True,
            "rule": "Nothing floats. Nothing clips. Nothing teleports.",
            "mission": (
                "Everything has physical behavior. Actors obey physics. "
                "Objects obey physics. Interactions feel believable."
            ),
        },
        "supported_interactions": list(SUPPORTED_INTERACTIONS),
        "hand_physics": build_hand_physics(cid),
        "foot_physics": build_foot_physics(cid),
        "body_physics": build_body_physics(cid, mass_kg=mass_kg, height_cm=height_cm),
        "objects": objects,
        "collision": build_collision_system(world_id=world_id),
        "clothing_physics": build_clothing_physics(cid),
        "hair_physics": build_hair_physics(cid),
        "environmental_physics": build_environmental_physics(
            weather=weather, outdoor=outdoor
        ),
        "interactions": list(interactions or []),
        "architecture": {
            "frozen": True,
            "no_new_renderer": True,
            "no_pipeline_redesign": True,
            "feeds": [
                "character_performance_engine",
                "character_rig_studio",
                "stage_world_simulation",
                "shot_assembly",
                "true_motion",
            ],
        },
        "scene_ref": {
            "character_id": cid,
            "physics_profile_ref": (
                f"data/physics_interaction/profiles/{cid}/PHYSICS_PROFILE.json"
            ),
            "do_not_float": True,
            "do_not_clip": True,
            "do_not_teleport": True,
        },
    }
    if interactions:
        profile["interaction_validations"] = [
            validate_interaction_package(ix) for ix in interactions
        ]
    profile["validation"] = validate_physics_profile(profile)
    return profile


def build_scene_physics(
    *,
    character_id: str,
    scene: dict[str, Any],
    scene_index: int = 0,
    stage_world: dict[str, Any] | None = None,
    location: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
    """Per-scene physics bundle: profile + planned INTERACTION_PACKAGEs."""
    cid = str(character_id).upper()
    stage = stage_world or scene.get("stage_world_package")
    world_id = None
    weather = "interior_climate"
    outdoor = False

    if isinstance(location, dict):
        weather = str(location.get("weather") or weather)
        world_id = location.get("id")
    if stage:
        world_id = stage.get("world_id") or world_id
        living = stage.get("living_world") or {}
        weather = str(living.get("weather") or weather)
        # Resolve full world if only slim package present
        if not stage.get("geometry"):
            try:
                from services.stage_world_simulation import resolve_world_package

                full = resolve_world_package(world_id or location)
                stage = full
                world_id = full.get("world_id")
                weather = str((full.get("living_world") or {}).get("weather") or weather)
                wid = str(world_id or "")
                outdoor = any(k in wid for k in ("FOREST", "PARK", "CITY-PARK"))
                try:
                    from services.stage_world_simulation.location_catalog import (
                        get_location_definition,
                    )

                    defn = get_location_definition(wid) or {}
                    outdoor = bool(defn.get("outdoor", outdoor))
                except Exception:  # noqa: BLE001
                    pass
            except Exception:  # noqa: BLE001
                pass

    # Mass/height from character rig if available
    mass_kg, height_cm = 82.0, 185.0
    try:
        from services.character_rig_studio import resolve_character_rig

        rig = resolve_character_rig(cid)
        height_cm = float((rig.get("identity") or {}).get("height_cm") or height_cm)
        body = rig.get("body_rig") or {}
        if body.get("height_cm"):
            height_cm = float(body["height_cm"])
    except Exception:  # noqa: BLE001
        pass

    interactions = plan_interactions_from_scene(
        actor=cid,
        scene=scene,
        stage_world=stage if isinstance(stage, dict) else None,
        scene_index=scene_index,
    )
    profile = build_physics_profile(
        cid,
        world_id=str(world_id) if world_id else None,
        stage_world=stage if isinstance(stage, dict) else None,
        weather=weather,
        outdoor=outdoor,
        mass_kg=mass_kg,
        height_cm=height_cm,
        interactions=interactions,
    )
    return {
        "character_id": cid,
        "world_id": world_id,
        "physics_profile": profile,
        "interactions": interactions,
        "interaction_count": len(interactions),
        "validation": profile.get("validation"),
        "scene_ref": profile.get("scene_ref"),
    }
