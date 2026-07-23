"""Quality gates — reject purposeless, mechanical, random direction."""

from __future__ import annotations

from typing import Any

from services.cinematic_direction_studio.models import (
    EMOTIONAL_ARC,
    REJECT_REASONS,
    SHOT_TYPES,
)


def validate_director_package(package: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(package, dict) or not package:
        return {
            "ok": False,
            "score": 0,
            "failures": ["missing_director_package"],
            "rejects": list(REJECT_REASONS),
        }

    failures: list[str] = []
    rejects: list[str] = []

    for field in (
        "story_objective",
        "emotional_objective",
        "actor_objective",
        "camera_objective",
        "lighting_objective",
        "editing_objective",
        "music_objective",
    ):
        if not package.get(field):
            failures.append(f"missing_{field}")

    if package.get("emotional_objective") not in EMOTIONAL_ARC and package.get(
        "emotional_objective"
    ) not in {
        "hope",
        "discovery",
        "conversation",
        "teaching",
        "joy",
        "awe",
        "focus",
        "scientific",
        "urgency",
        "mystery",
        "comfort",
    }:
        # Allow extended emotions but require clarity
        if not package.get("emotional_objective"):
            failures.append("emotion_unclear")
            rejects.append("emotion_unclear")

    shot = package.get("shot_type")
    if shot not in SHOT_TYPES:
        failures.append("invalid_shot_type")

    cam = package.get("camera_language") or {}
    if not cam.get("motivated") or not cam.get("purpose"):
        failures.append("camera_unmotivated")
        rejects.append("camera_moves_without_purpose")
    if cam.get("camera_replaces_actor_motion") is True:
        failures.append("camera_replaces_acting")
        rejects.append("camera_moves_without_purpose")

    actor = package.get("actor_direction") or {}
    beats = actor.get("beats") or []
    if len(beats) < 3:
        failures.append("actor_direction_too_thin")
        rejects.append("actors_move_mechanically")
    if actor.get("forbid_mechanical_loop") is not True:
        failures.append("mechanical_loop_allowed")
        rejects.append("actors_move_mechanically")

    editing = package.get("editing_plan") or {}
    if not editing.get("motivated_only") and not editing.get("forbid_random_cuts"):
        failures.append("editing_unmotivated")
        rejects.append("editing_feels_random")

    pacing = package.get("pacing") or {}
    if not pacing.get("shot_duration_sec"):
        failures.append("pacing_missing")

    lighting = package.get("lighting_intent") or {}
    if not lighting.get("intent"):
        failures.append("lighting_intent_missing")

    score = max(0, 100 - 10 * len(failures))
    return {
        "ok": not failures,
        "score": score,
        "failures": failures,
        "rejects_hit": sorted(set(rejects)),
        "reject_catalog": list(REJECT_REASONS),
        "success": (
            "Feels directed by an experienced filmmaker — "
            "each shot supports story, emotion, and educational message."
        ),
        "mp4_required": True,
        "note": (
            "Passing this plan gate is necessary but not sufficient. "
            "Inspect the final MP4 for intentional direction."
        ),
    }


def validate_episode_direction(episode: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(episode, dict):
        return {"ok": False, "failures": ["missing_episode"], "rejects": list(REJECT_REASONS)}

    failures: list[str] = []
    rejects: list[str] = []
    scenes = episode.get("scenes") or []
    if len(scenes) < 1:
        failures.append("no_scenes")

    shots = [s.get("shot_type") for s in scenes]
    if len(shots) >= 3 and len(set(shots)) == 1:
        failures.append("identical_framing_every_scene")
        rejects.append("identical_framing_every_scene")

    # Detect immediate repeats
    for a, b in zip(shots, shots[1:]):
        if a and a == b:
            failures.append("shots_repeat_adjacent")
            rejects.append("shots_repeat")
            break

    timeline = episode.get("emotional_timeline") or {}
    if not timeline.get("has_arc") and len(scenes) >= 3:
        failures.append("emotional_arc_weak")
        rejects.append("emotion_unclear")

    scene_reviews = [validate_director_package(s) for s in scenes]
    if any(not r.get("ok") for r in scene_reviews):
        failures.append("scene_direction_failed")

    score = max(0, 100 - 12 * len(failures))
    return {
        "ok": not failures,
        "score": score,
        "failures": failures,
        "rejects_hit": sorted(set(rejects)),
        "scene_reviews": scene_reviews,
        "reject_catalog": list(REJECT_REASONS),
    }
