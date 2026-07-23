"""Build DIRECTOR_PACKAGE — intentional direction before render."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.cinematic_direction_studio.actor_direction import plan_actor_direction
from services.cinematic_direction_studio.camera_language import choose_camera_language
from services.cinematic_direction_studio.editing_plan import plan_editing
from services.cinematic_direction_studio.emotional_timeline import (
    build_emotional_timeline,
    infer_scene_emotion,
)
from services.cinematic_direction_studio.lighting_intent import plan_lighting_intent
from services.cinematic_direction_studio.models import (
    ENGINE_ID,
    EPISODE_PACKAGE_TYPE,
    PACKAGE_TYPE,
    PACKAGE_VERSION,
)
from services.cinematic_direction_studio.pacing import plan_pacing
from services.cinematic_direction_studio.shot_design import choose_shot_type, shot_purpose
from services.cinematic_direction_studio.validation import (
    validate_director_package,
    validate_episode_direction,
)

ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = ROOT / "data" / "cinematic_direction_studio" / "packages"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_director_package(
    *,
    scene: dict[str, Any],
    scene_index: int = 0,
    total_scenes: int = 1,
    used_shots: set[str] | None = None,
    topic: str = "",
    location: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
    used = used_shots if used_shots is not None else set()
    narration = str(scene.get("narration") or scene.get("dialogue") or "")
    purpose = str(scene.get("purpose") or scene.get("segment_type") or "story_beat")
    duration = float(scene.get("length_sec") or scene.get("duration_sec") or 3.0)
    character_id = str(scene.get("studio_character_id") or "DOCTOR_001")

    vfd = scene.get("vfd_seed") if isinstance(scene.get("vfd_seed"), dict) else {}
    vfd_shot = scene.get("vfd_shot") if isinstance(scene.get("vfd_shot"), dict) else {}
    emotion = infer_scene_emotion(
        scene_index=scene_index,
        total=total_scenes,
        purpose=purpose,
        narration=narration,
        prior_emotion=str(scene.get("director_emotion") or vfd.get("emotion") or ""),
    )
    # Prefer explicit seeds when present; map VFD beats → audience arc
    if scene.get("director_emotion"):
        emotion = _map_emotion(str(scene["director_emotion"]))
    elif vfd.get("emotional_beat") or vfd.get("emotion"):
        emotion = _map_emotion(str(vfd.get("emotional_beat") or vfd.get("emotion")))

    shot_type = choose_shot_type(
        scene_index=scene_index,
        total=total_scenes,
        purpose=purpose,
        emotion=emotion,
        used=used,
        vfd_language=str(scene.get("shot_language") or vfd_shot.get("shot_language") or ""),
    )
    used.add(shot_type)

    camera = choose_camera_language(
        emotion=emotion,
        shot_type=shot_type,
        vfd_seed=vfd or None,
    )
    actor = plan_actor_direction(
        character_id=character_id,
        narration=narration,
        emotion=emotion,
        duration_sec=duration,
        scene_index=scene_index,
        cpe=scene.get("character_performance_package"),
    )
    pacing = plan_pacing(
        duration_sec=duration,
        emotion=emotion,
        shot_type=shot_type,
        actor_beats=actor.get("beats"),
    )
    loc_hint = ""
    if isinstance(location, dict):
        loc_hint = str(location.get("id") or location.get("name") or "")
    elif location:
        loc_hint = str(location)
    loc_hint = loc_hint or str(scene.get("studio_location_id") or scene.get("world_id") or "")

    lighting = plan_lighting_intent(
        emotion=emotion,
        location_hint=loc_hint,
        vfd_mood=str(scene.get("lighting_mood") or vfd.get("lighting_mood") or "") or None,
    )
    editing = plan_editing(
        scene_index=scene_index,
        total=total_scenes,
        emotion=emotion,
        duration_sec=duration,
        purpose=purpose,
    )

    story_objective = narration.split(".")[0].strip() if narration else f"Advance {purpose}"
    if len(story_objective) > 120:
        story_objective = story_objective[:117] + "..."

    package: dict[str, Any] = {
        "package_type": PACKAGE_TYPE,
        "package_version": PACKAGE_VERSION,
        "engine_id": ENGINE_ID,
        "created_at": _now(),
        "scene_number": int(scene.get("scene_number") or scene_index + 1),
        "scene_id": str(
            scene.get("scene_id")
            or scene.get("id")
            or f"scene_{scene_index + 1:03d}"
        ),
        "topic": topic,
        "philosophy": {
            "not_an_animation_engine": True,
            "not_a_renderer": True,
            "rule": "Every shot has a purpose. Every movement supports the story.",
        },
        "story_objective": story_objective or f"Serve {purpose}",
        "emotional_objective": emotion,
        "actor_objective": actor.get("objective"),
        "camera_objective": camera.get("purpose"),
        "lighting_objective": lighting.get("purpose"),
        "editing_objective": f"Transition {editing.get('transition_out')} with ending beat {editing.get('ending_beat')}",
        "music_objective": (
            f"Music {((editing.get('music_timing') or {}).get('enter'))}; "
            f"exit {(editing.get('music_timing') or {}).get('exit')}"
        ),
        "shot_type": shot_type,
        "shot_purpose": shot_purpose(shot_type, emotion, narration),
        "camera_language": camera,
        "actor_direction": actor,
        "pacing": pacing,
        "lighting_intent": lighting,
        "editing_plan": editing,
        "compose_vfd": bool(vfd or vfd_shot or scene.get("shot_language")),
        "architecture": {
            "frozen": True,
            "no_new_renderer": True,
            "not_animation_engine": True,
            "feeds": [
                "virtual_film_director",
                "animation_engine",
                "character_performance_engine",
                "true_motion",
                "shot_assembly",
            ],
        },
        "animation_seed": {
            "emotion": emotion,
            "shot_size": _shot_size(shot_type),
            "lighting_mood": lighting.get("lighting_mood"),
            "true_motion_camera": camera.get("true_motion_camera"),
            "shot_language": shot_type,
            "transition_style": editing.get("transition_style"),
            "director_emotion": emotion,
            "motivated": True,
            "source": "cinematic_direction_studio",
        },
    }
    package["validation"] = validate_director_package(package)
    return package


def build_episode_director_package(
    scenes: list[dict[str, Any]],
    *,
    topic: str = "",
    production_id: str = "",
    location: dict[str, Any] | str | None = None,
    write: bool = False,
    out_dir: str | Path | None = None,
) -> dict[str, Any]:
    used: set[str] = set()
    plans: list[dict[str, Any]] = []
    total = max(len(scenes), 1)
    for i, scene in enumerate(scenes):
        plan = build_director_package(
            scene=scene,
            scene_index=i,
            total_scenes=total,
            used_shots=used,
            topic=topic,
            location=location,
        )
        plans.append(plan)

    timeline = build_emotional_timeline(plans)
    episode = {
        "package_type": EPISODE_PACKAGE_TYPE,
        "package_version": PACKAGE_VERSION,
        "engine_id": ENGINE_ID,
        "created_at": _now(),
        "topic": topic,
        "production_id": production_id,
        "scene_count": len(plans),
        "scenes": plans,
        "emotional_timeline": timeline,
        "philosophy": {
            "not_an_animation_engine": True,
            "not_a_renderer": True,
            "rule": "Every scene must feel intentionally directed.",
        },
        "architecture": {
            "frozen": True,
            "composes_virtual_film_director": True,
        },
    }
    episode["validation"] = validate_episode_direction(episode)

    if write:
        if out_dir:
            base = Path(out_dir)
        else:
            slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in topic)[:48] or "topic"
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            base = OUT_ROOT / f"{slug}_{stamp}"
        base.mkdir(parents=True, exist_ok=True)
        path = base / "DIRECTOR_PACKAGE.json"
        path.write_text(json.dumps(episode, indent=2, default=str) + "\n", encoding="utf-8")
        notes = base / "DIRECTOR_NOTES.md"
        notes.write_text(_markdown(episode), encoding="utf-8")
        episode["path"] = str(path)
        episode["out_dir"] = str(base)
    return episode


def _map_emotion(raw: str) -> str:
    from services.cinematic_direction_studio.models import EMOTIONAL_ARC

    e = str(raw or "").lower().strip()
    aliases = {
        "explanation": "understanding",
        "discovery": "curiosity",
        "payoff": "resolution",
        "surprise": "wonder",
        "relief": "resolution",
        "scale": "wonder",
        "tension": "urgency",
        "awe": "wonder",
        "warmth": "inspiration",
        "clarity": "understanding",
        "focus": "understanding",
        "hope": "inspiration",
        "joy": "inspiration",
        "teaching": "understanding",
        "scientific": "understanding",
        "conversation": "understanding",
        "comfort": "reflection",
        "mystery": "wonder",
        "urgency": "curiosity",
    }
    if e in EMOTIONAL_ARC:
        return e
    if e in aliases:
        mapped = aliases[e]
        return mapped if mapped in EMOTIONAL_ARC else "curiosity"
    return "curiosity"


def _shot_size(shot_type: str) -> str:
    return {
        "establishing": "establishing_wide",
        "wide": "establishing_wide",
        "medium": "dynamic_medium",
        "close_up": "intimate_close_up",
        "extreme_close_up": "intimate_close_up",
        "tracking": "dynamic_medium",
        "follow": "dynamic_medium",
        "orbit": "dynamic_medium",
        "over_the_shoulder": "dynamic_medium",
        "pov": "dynamic_medium",
        "reaction": "intimate_close_up",
        "cutaway": "dynamic_medium",
        "insert": "intimate_close_up",
    }.get(shot_type, "dynamic_medium")


def _markdown(episode: dict[str, Any]) -> str:
    lines = [
        f"# Director Notes — {episode.get('topic') or 'Episode'}",
        "",
        "Intentionally directed before render. Not an animation engine.",
        "",
    ]
    for s in episode.get("scenes") or []:
        lines.append(
            f"## Scene {s.get('scene_number')} — `{s.get('shot_type')}` / {s.get('emotional_objective')}"
        )
        lines.append(f"- Story: {s.get('story_objective')}")
        lines.append(f"- Camera: {s.get('camera_objective')}")
        lines.append(f"- Actor: {s.get('actor_objective')}")
        lines.append(f"- Lighting: {s.get('lighting_objective')}")
        lines.append("")
    return "\n".join(lines) + "\n"
