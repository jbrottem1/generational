"""Complete shot input — facial performance + environment + camera contract."""

from __future__ import annotations

from typing import Any

from services.character_performance import (
    build_facial_performance_plan,
    rendered_facial_inspection_template,
    validate_facial_performance_plan,
)
from services.environment_department import (
    build_environment_package,
    rendered_environment_inspection_template,
    validate_environment_package,
)

try:
    from services.character_performance_engine import (
        build_character_performance,
        rendered_performance_inspection_template,
        validate_character_performance,
    )
except Exception:  # noqa: BLE001
    build_character_performance = None  # type: ignore
    rendered_performance_inspection_template = None  # type: ignore
    validate_character_performance = None  # type: ignore


def build_complete_shot(
    *,
    shot_id: str,
    story_objective: str,
    scene: dict[str, Any],
    character_id: str,
    host: dict[str, Any] | None = None,
    location: dict[str, Any] | str | None = None,
    camera: dict[str, Any] | None = None,
    scene_index: int = 0,
) -> dict[str, Any]:
    facial = build_facial_performance_plan(
        character_id=character_id,
        scene=scene,
        host=host,
        scene_index=scene_index,
        audio_path=str(scene.get("narration_audio_path") or ""),
    )
    env = build_environment_package(
        location,
        owner=character_id,
        lighting_mood=str((camera or {}).get("lighting_mood") or "clinical_warm"),
    )
    body_perf = None
    if build_character_performance is not None:
        body_perf = scene.get("character_performance_package") or build_character_performance(
            character_id=character_id,
            scene=scene,
            scene_index=scene_index,
            host=host,
            location=location,
        )
    character_rig = scene.get("character_rig_package")
    if not character_rig:
        try:
            from services.character_rig_studio import resolve_character_rig

            full_rig = resolve_character_rig(character_id)
            character_rig = {
                "character_id": character_id,
                "continuity_version": (full_rig.get("identity") or {}).get("continuity_version"),
                "scene_ref": full_rig.get("scene_ref"),
                "validation": full_rig.get("validation"),
                "do_not_regenerate": True,
            }
        except Exception:  # noqa: BLE001
            character_rig = None
    stage_world = scene.get("stage_world_package")
    if not stage_world:
        try:
            from services.stage_world_simulation import resolve_world_package

            full_world = resolve_world_package(location)
            stage_world = {
                "world_id": full_world.get("world_id"),
                "display_name": full_world.get("display_name"),
                "scene_ref": full_world.get("scene_ref"),
                "validation": full_world.get("validation"),
                "persistent": True,
                "flat_image_background": False,
            }
        except Exception:  # noqa: BLE001
            stage_world = None
    physics_bundle = scene.get("physics_bundle")
    if not physics_bundle:
        try:
            from services.physics_interaction import build_scene_physics

            physics_bundle = build_scene_physics(
                character_id=character_id,
                scene=scene,
                scene_index=scene_index,
                stage_world=stage_world,
                location=location,
            )
        except Exception:  # noqa: BLE001
            physics_bundle = None
    attention = facial.get("attention_target") or {}
    cam = camera or {
        "shot_size": "medium_close_up",
        "lens_mm": 50,
        "movement": (body_perf or {}).get("camera_follow", {}).get("mode") or "tracking",
        "focus_target": f"{character_id}_eyes",
        "follows_actor": True,
    }
    shot = {
        "shot_id": shot_id,
        "story_objective": story_objective,
        "character_performance": {
            "character_id": character_id,
            "emotion": f"{facial.get('primary_emotion')}_with_{facial.get('secondary_emotion')}",
            "attention_target": attention.get("attention_target_id"),
            "facial_performance_plan": facial,
            "gaze_plan": facial.get("gaze_events"),
            "blink_plan": facial.get("blink_plan"),
            "expression_plan": facial.get("expression_curve"),
            "speech_plan": facial.get("speech_performance"),
            "body_performance_package": body_perf,
            "character_rig": character_rig,
            "blocking": (body_perf or {}).get("blocking"),
            "locomotion": (body_perf or {}).get("locomotion"),
            "interactions": (body_perf or {}).get("interactions"),
            "simulation": (body_perf or {}).get("simulation"),
        },
        "environment": {
            "environment_id": env.get("environment_id"),
            "package": env,
            "foreground_elements": [x.get("id") for x in (env.get("foreground") or [])],
            "midground_elements": [x.get("id") for x in (env.get("midground") or [])],
            "background_elements": [x.get("id") for x in (env.get("background") or [])],
            "weather": (env.get("weather") or {}).get("type"),
            "lighting_mood": (env.get("lighting") or {}).get("mood"),
            "ambient_motion": env.get("ambient_motion"),
            "environment_life": (body_perf or {}).get("environment_life"),
            "stage_world": stage_world,
        },
        "camera": {
            **cam,
            "camera_follow": (body_perf or {}).get("camera_follow"),
            "follows_performance": True,
            "camera_replaces_actor_motion": False,
        },
        "stage_world": stage_world,
        "physics": {
            "bundle": physics_bundle,
            "constraints": {
                "no_float": True,
                "no_clip": True,
                "no_teleport": True,
            },
            "interaction_packages": (physics_bundle or {}).get("interactions"),
        },
        "direction": {
            "director_package": scene.get("director_package"),
            "story_objective": (scene.get("director_package") or {}).get("story_objective"),
            "emotional_objective": (scene.get("director_package") or {}).get(
                "emotional_objective"
            ),
            "actor_direction": scene.get("actor_direction")
            or (scene.get("director_package") or {}).get("actor_direction"),
            "shot_type": (scene.get("director_package") or {}).get("shot_type"),
        },
        "validation": {
            "facial_plan": validate_facial_performance_plan(facial),
            "environment_plan": validate_environment_package(env),
            "body_performance": (
                validate_character_performance(body_perf)
                if validate_character_performance and body_perf
                else {"ok": False, "failures": ["engine_unavailable"]}
            ),
            "stage_world": (stage_world or {}).get("validation"),
            "physics": (physics_bundle or {}).get("validation"),
            "rendered_facial_inspection": rendered_facial_inspection_template(),
            "rendered_environment_inspection": rendered_environment_inspection_template(),
            "rendered_performance_inspection": (
                rendered_performance_inspection_template()
                if rendered_performance_inspection_template
                else {"inspect_mp4": True}
            ),
            "final_standard": (
                "Not 'the character moved inside a background' — "
                "a believable character delivered an emotionally readable performance "
                "inside a coherent, living world. "
                "Viewer believes: animated television show — not animated pictures. "
                "Filmed on a persistent stage — not assembled from disconnected images. "
                "Actors behave like physical beings — nothing floats, clips, or teleports."
            ),
            "quality_rule": (
                "JSON plans and checklist templates are not proof of quality. "
                "Inspect the final MP4 for gaze, face, body locomotion, interactions, "
                "navigation through space, living environment, foot plant, hand contact, "
                "collision integrity, depth, materials, weather, lighting, and continuity. "
                "Reject flat photo backdrops, floating actors, sliding feet, and missed grips."
            ),
        },
        "architecture": {
            "no_new_renderer": True,
            "no_pipeline_redesign": True,
            "feeds_existing_animation_world_lighting_camera_systems": True,
            "character_performance_engine": True,
            "character_rig_studio": True,
            "stage_world_simulation": True,
            "physics_interaction": True,
            "cinematic_direction_studio": True,
            "scenes_reference_actors_never_recreate": True,
            "scenes_reference_persistent_worlds": True,
        },
    }
    return shot


def attach_complete_shots(
    scenes: list[dict[str, Any]],
    *,
    hosts_by_id: dict[str, dict[str, Any]] | None = None,
    location: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    hosts_by_id = hosts_by_id or {}
    out: list[dict[str, Any]] = []
    for i, scene in enumerate(scenes):
        row = dict(scene)
        cid = str(row.get("studio_character_id") or "DOCTOR_001")
        host = hosts_by_id.get(cid.upper())
        shot_id = f"scene_{int(row.get('scene_number') or i + 1):03d}_shot_01"
        if not row.get("complete_shot"):
            row["complete_shot"] = build_complete_shot(
                shot_id=shot_id,
                story_objective=str(row.get("narration") or row.get("purpose") or "story_beat")[:160],
                scene=row,
                character_id=cid,
                host=host,
                location=location,
                scene_index=i,
            )
        # Convenience mirrors
        if row.get("complete_shot"):
            row["facial_performance_plan"] = row["complete_shot"]["character_performance"][
                "facial_performance_plan"
            ]
            row["environment_package"] = row["complete_shot"]["environment"]["package"]
        out.append(row)
    return out
