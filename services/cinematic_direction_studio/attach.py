"""Soft-attach DIRECTOR_PACKAGE onto scenes and candidates."""

from __future__ import annotations

from typing import Any

from services.cinematic_direction_studio.package import (
    build_director_package,
    build_episode_director_package,
)


def attach_cinematic_direction(
    scenes: list[dict[str, Any]],
    *,
    topic: str = "",
    location: dict[str, Any] | str | None = None,
) -> list[dict[str, Any]]:
    used: set[str] = set()
    total = max(len(scenes), 1)
    out: list[dict[str, Any]] = []
    for i, scene in enumerate(scenes):
        row = dict(scene)
        if not row.get("director_package"):
            row["director_package"] = build_director_package(
                scene=row,
                scene_index=i,
                total_scenes=total,
                used_shots=used,
                topic=topic,
                location=location,
            )
        else:
            used.add(str(row["director_package"].get("shot_type") or ""))

        plan = row["director_package"]
        seed = plan.get("animation_seed") or {}
        # Stamp direction fields Animation Engine / true_motion already honor
        row["director_emotion"] = seed.get("director_emotion") or plan.get("emotional_objective")
        row["shot_size"] = seed.get("shot_size") or row.get("shot_size")
        row["lighting_mood"] = seed.get("lighting_mood") or row.get("lighting_mood")
        row["shot_language"] = row.get("shot_language") or seed.get("shot_language")
        row["transition_style"] = seed.get("transition_style") or row.get("transition_style")
        row["scene_objective"] = plan.get("story_objective")
        row["actor_direction"] = plan.get("actor_direction")
        row["director_shot_type"] = plan.get("shot_type")
        row["director_pacing"] = plan.get("pacing")
        row["director_editing"] = plan.get("editing_plan")

        tm = dict(row.get("true_motion") or {})
        tm["camera"] = seed.get("true_motion_camera") or tm.get("camera")
        tm["emotion"] = seed.get("emotion") or tm.get("emotion")
        tm["lighting_mood"] = seed.get("lighting_mood") or tm.get("lighting_mood")
        tm["shot_size"] = seed.get("shot_size") or tm.get("shot_size")
        tm["cinematic_direction"] = True
        tm["motivated_camera"] = True
        row["true_motion"] = tm

        # Enrich vfd_seed without wiping VFD
        vfd = dict(row.get("vfd_seed") or {})
        vfd.setdefault("emotion", seed.get("emotion"))
        vfd.setdefault("lighting_mood", seed.get("lighting_mood"))
        vfd.setdefault("shot_size", seed.get("shot_size"))
        vfd.setdefault("true_motion_camera", seed.get("true_motion_camera"))
        vfd["cinematic_direction_studio"] = True
        row["vfd_seed"] = vfd
        out.append(row)
    return out


def attach_cinematic_direction_to_candidate(
    candidate: dict[str, Any],
    *,
    topic: str = "",
    location: dict[str, Any] | str | None = None,
    write: bool = False,
) -> dict[str, Any]:
    out = dict(candidate)
    topic = topic or str(out.get("topic") or out.get("title") or "")
    loc = location or out.get("studio_location")
    vp = dict(out.get("visual_package") or {})
    scenes = list(vp.get("scenes") or out.get("scenes") or [])
    scenes = attach_cinematic_direction(scenes, topic=topic, location=loc)
    if scenes:
        vp["scenes"] = scenes
        out["visual_package"] = vp
        out["scenes"] = scenes

    episode = build_episode_director_package(
        scenes,
        topic=topic,
        production_id=str(out.get("production_id") or ""),
        location=loc,
        write=write,
    )
    out["cinematic_direction_studio"] = {
        "path": episode.get("path"),
        "validation": episode.get("validation"),
        "emotional_timeline": episode.get("emotional_timeline"),
        "scene_count": episode.get("scene_count"),
    }
    out["DIRECTOR_PACKAGE"] = episode
    out["directed_by_cinematic_direction_studio"] = True
    return out
