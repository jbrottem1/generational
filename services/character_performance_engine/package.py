"""Build / attach Character Performance Engine packages (pre-render)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.character_performance_engine.blocking import plan_blocking
from services.character_performance_engine.body_performance import build_body_performance
from services.character_performance_engine.camera_follow import plan_camera_follow
from services.character_performance_engine.environment_life import plan_environment_life
from services.character_performance_engine.interactions import plan_interactions
from services.character_performance_engine.locomotion import build_locomotion
from services.character_performance_engine.models import (
    ENGINE_ID,
    PACKAGE_TYPE,
    PACKAGE_VERSION,
)
from services.character_performance_engine.objectives import infer_objective
from services.character_performance_engine.simulate import simulate_performance
from services.character_performance_engine.true_motion_bridge import package_true_motion_fields
from services.character_performance_engine.validation import (
    rendered_performance_inspection_template,
    validate_character_performance,
)

ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = ROOT / "data" / "character_performance_engine" / "packages"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_character_performance(
    *,
    character_id: str,
    scene: dict[str, Any],
    scene_index: int = 0,
    host: dict[str, Any] | None = None,
    location: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
    """Full pre-render performance: objective → blocking → simulate → validate."""
    cid = str(character_id or (host or {}).get("id") or "DOCTOR_001").upper()
    narration = str(scene.get("narration") or scene.get("dialogue") or "")
    expression = str(scene.get("studio_expression") or "focus")
    duration = float(scene.get("length_sec") or scene.get("duration_sec") or 3.0)
    shot_size = str(
        scene.get("shot_size")
        or (scene.get("cinematic_intent") or {}).get("shot_size")
        or "dynamic_medium"
    )
    emotion = str(
        scene.get("studio_emotion")
        or ((scene.get("performance_plan") or {}).get("emotion") or {}).get("primary")
        or "confidence"
    )
    walking = str(
        scene.get("studio_walking_style")
        or (scene.get("performance_plan") or {}).get("walking_style")
        or (host or {}).get("movement_style")
        or "grounded_walk_explain"
    )

    loc_hint = _location_hint(location, scene)
    ambient = []
    if isinstance(location, dict):
        ambient = list(location.get("environmental_animation") or location.get("ambient_life") or [])

    objective = infer_objective(narration, expression=expression, scene=scene)
    # Honor Human Realism plan objective when present
    if (scene.get("performance_plan") or {}).get("objective"):
        objective = {
            **objective,
            "statement": scene["performance_plan"]["objective"],
        }

    blocking = plan_blocking(
        duration_sec=duration,
        objective=objective,
        scene_index=scene_index,
        shot_size=shot_size,
    )
    locomotion = build_locomotion(blocking, duration_sec=duration, walking_style=walking)
    body = build_body_performance(
        duration_sec=duration,
        objective=objective,
        blocking=blocking,
        locomotion=locomotion,
        emotion=emotion,
    )
    interactions = plan_interactions(
        objective=objective,
        blocking=blocking,
        duration_sec=duration,
        location_hint=loc_hint,
    )
    env_life = plan_environment_life(
        location_hint=loc_hint,
        ambient_from_location=ambient,
        duration_sec=duration,
    )
    camera_follow = plan_camera_follow(
        locomotion=locomotion,
        objective=objective,
        scene_index=scene_index,
        shot_size=shot_size,
    )
    simulation = simulate_performance(
        locomotion=locomotion,
        body=body,
        interactions=interactions,
        camera_follow=camera_follow,
        duration_sec=duration,
        emotion=emotion,
    )

    scene_id = str(
        scene.get("scene_id")
        or scene.get("id")
        or f"scene_{int(scene.get('scene_number') or scene_index + 1):03d}"
    )

    package: dict[str, Any] = {
        "package_type": PACKAGE_TYPE,
        "package_version": PACKAGE_VERSION,
        "engine_id": ENGINE_ID,
        "created_at": _now(),
        "character_id": cid,
        "scene_id": scene_id,
        "scene_number": int(scene.get("scene_number") or scene_index + 1),
        "duration_sec": duration,
        "philosophy": {
            "not_a_renderer": True,
            "not_an_image_generator": True,
            "not_an_animation_filter": True,
            "pipeline": [
                "build_environment",
                "place_character",
                "assign_objectives",
                "simulate_performance",
                "animate_performance",
                "then_render",
            ],
            "rule": "Every second must contain genuine character animation.",
            "reject_if": "motion could be recreated by moving a still photograph",
        },
        "objective": objective,
        "blocking": blocking,
        "locomotion": locomotion,
        "body_performance": body,
        "interactions": interactions,
        "environment_life": env_life,
        "camera_follow": camera_follow,
        "simulation": simulation,
        "ken_burns": False,
        "motion_class": "actor_performance",
        "inherits_facial_plan": bool(scene.get("facial_performance_plan")),
        "inherits_human_realism_plan": bool(scene.get("performance_plan")),
        "architecture": {
            "frozen": True,
            "no_new_renderer": True,
            "no_pipeline_redesign": True,
            "feeds": ["animation_engine", "true_motion", "character_world_studio", "shot_assembly"],
        },
    }
    package["true_motion"] = package_true_motion_fields(package)
    package["validation"] = validate_character_performance(package)
    package["rendered_inspection"] = rendered_performance_inspection_template()
    return package


def attach_character_performances(
    scenes: list[dict[str, Any]],
    *,
    hosts_by_id: dict[str, dict[str, Any]] | None = None,
    location: dict[str, Any] | str | None = None,
) -> list[dict[str, Any]]:
    """Soft-attach a character_performance_package onto every scene binding."""
    hosts_by_id = hosts_by_id or {}
    out: list[dict[str, Any]] = []
    for i, scene in enumerate(scenes):
        row = dict(scene)
        cid = str(row.get("studio_character_id") or "DOCTOR_001")
        host = hosts_by_id.get(cid.upper())
        if not row.get("character_performance_package"):
            row["character_performance_package"] = build_character_performance(
                character_id=cid,
                scene=row,
                scene_index=i,
                host=host,
                location=location,
            )
        pkg = row["character_performance_package"]
        # Convenience mirrors for Animation Engine / true_motion
        row["character_blocking"] = pkg.get("blocking")
        row["actor_locomotion"] = pkg.get("locomotion")
        row["actor_interactions"] = pkg.get("interactions")
        row["environment_life_plan"] = pkg.get("environment_life")
        row["camera_follow"] = pkg.get("camera_follow")
        row["performance_simulation"] = pkg.get("simulation")
        tm = pkg.get("true_motion") or {}
        if tm:
            existing = dict(row.get("true_motion") or {})
            existing.update(tm)
            row["true_motion"] = existing
            row["studio_performance"] = tm.get("performance") or row.get("studio_performance")
        out.append(row)
    return out


def build_episode_performance_package(
    scenes: list[dict[str, Any]],
    *,
    topic: str = "",
    production_id: str = "",
    write: bool = False,
    out_dir: str | Path | None = None,
) -> dict[str, Any]:
    packages = [s.get("character_performance_package") for s in scenes if s.get("character_performance_package")]
    gate_ok = all((p or {}).get("validation", {}).get("ok") for p in packages) if packages else False
    episode = {
        "package_type": "EPISODE_CHARACTER_PERFORMANCE",
        "package_version": PACKAGE_VERSION,
        "engine_id": ENGINE_ID,
        "created_at": _now(),
        "topic": topic,
        "production_id": production_id,
        "scene_count": len(packages),
        "scenes": packages,
        "quality_gate": {
            "ok": gate_ok,
            "all_scenes_validated": gate_ok,
            "mp4_inspection_required": True,
        },
        "architecture": {
            "frozen": True,
            "no_new_renderer": True,
        },
    }
    if write:
        base = Path(out_dir) if out_dir else OUT_ROOT / (production_id or "local")
        base.mkdir(parents=True, exist_ok=True)
        path = base / "CHARACTER_PERFORMANCE_PACKAGE.json"
        path.write_text(json.dumps(episode, indent=2, default=str) + "\n", encoding="utf-8")
        episode["path"] = str(path)
    return episode


def _location_hint(location: dict[str, Any] | str | None, scene: dict[str, Any]) -> str:
    if isinstance(location, str) and location.strip():
        return location
    if isinstance(location, dict):
        return str(location.get("id") or location.get("name") or location.get("type") or "lab")
    return str(
        scene.get("studio_location_id")
        or scene.get("location")
        or scene.get("world_type")
        or "lab"
    )
