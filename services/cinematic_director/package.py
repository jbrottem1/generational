"""Build / apply Cinematic Direction Package — renderer blueprint (not a render engine)."""

from __future__ import annotations

import re
from typing import Any

from services.cinematic_director.intensity import (
    choose_camera_for_intensity,
    choose_composition,
    choose_lighting,
    choose_transition,
    emphasis_and_hierarchy,
    predicted_retention_weight,
)
from services.cinematic_director.validate import validate_cinematic_direction
from services.cinematic_director.vocabulary import CAMERA_MOVES, palette_for_niche, resolve_niche

PACKAGE_VERSION = "1.0.0"


def _scenes_from_candidate(candidate: dict[str, Any], script: str = "") -> list[dict[str, Any]]:
    vp = candidate.get("visual_package") or {}
    scenes = list(vp.get("scenes") or candidate.get("scenes") or [])
    if scenes:
        return scenes
    # Build lightweight beats from script / hook
    text = script or str(candidate.get("script") or candidate.get("hook") or candidate.get("title") or "")
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]
    if not parts:
        parts = [str(candidate.get("title") or "Scene")]
    # group into ~4–7 scenes
    target = min(7, max(3, len(parts)))
    chunk = max(1, len(parts) // target)
    beats = []
    for i in range(0, len(parts), chunk):
        beats.append(" ".join(parts[i : i + chunk]))
        if len(beats) >= target:
            break
    if len(beats) > 1 and len(parts) > chunk * len(beats):
        beats[-1] = beats[-1] + " " + " ".join(parts[chunk * len(beats) :])
    out = []
    t = 0.0
    for i, narr in enumerate(beats):
        dur = max(2.5, min(8.0, 2.2 + len(narr.split()) * 0.35))
        out.append(
            {
                "scene_id": f"s{i+1}",
                "narration": narr,
                "purpose": "hook" if i == 0 else ("cta" if i == len(beats) - 1 else "story_beat"),
                "duration_sec": round(dur, 2),
                "start_sec": round(t, 2),
            }
        )
        t += dur
    return out


def build_cinematic_direction_package(
    candidate: dict[str, Any] | None = None,
    *,
    script: str = "",
    topic: str = "",
    niche: str = "",
    platform: str = "youtube_shorts",
) -> dict[str, Any]:
    """Generate the directing blueprint between script and renderer."""
    candidate = dict(candidate or {})
    topic = topic or str(candidate.get("topic") or candidate.get("title") or "")
    niche_key = resolve_niche(niche or str(candidate.get("niche") or ""), topic)
    palette = palette_for_niche(niche_key, topic)
    scenes = _scenes_from_candidate(candidate, script=script)

    shot_list: list[dict[str, Any]] = []
    camera_plan: list[dict[str, Any]] = []
    motion_plan: list[dict[str, Any]] = []
    timing: list[dict[str, Any]] = []
    lighting_plan: list[dict[str, Any]] = []
    transition_plan: list[dict[str, Any]] = []
    emotional_pacing: list[dict[str, Any]] = []
    director_notes: list[str] = []

    prev_camera = ""
    used_moves: list[str] = []

    for i, scene in enumerate(scenes):
        narration = str(scene.get("narration") or scene.get("voiceover") or "")
        purpose = str(scene.get("purpose") or "")
        start = float(scene.get("start_sec") or scene.get("start") or 0)
        dur = float(scene.get("duration_sec") or scene.get("duration") or 4.0)
        sid = str(scene.get("scene_id") or f"s{i+1}")

        ret = predicted_retention_weight(
            scene_index=i,
            total_scenes=len(scenes),
            narration=narration,
            purpose=purpose,
            start_sec=start,
        )
        camera = choose_camera_for_intensity(ret["intensity_0_1"], avoid_static=True, scene_index=i)
        # Avoid repeating identical move
        if used_moves and camera == used_moves[-1]:
            alts = [c for c in ("push_in", "orbit", "dolly", "tracking", "pull_out", "macro") if c != camera]
            camera = alts[i % len(alts)]
        used_moves.append(camera)

        composition = choose_composition(narration, camera)
        lighting = choose_lighting(niche_key, ret["intensity_0_1"], narration)
        transition = choose_transition(prev_camera, ret["intensity_0_1"], i)
        emphasis = emphasis_and_hierarchy(narration, ret["intensity_0_1"])
        cam_meta = CAMERA_MOVES[camera]
        movement_score = int(ret["recommended_motion_score"])
        if cam_meta.get("intensity_boost"):
            movement_score = min(100, movement_score + int(cam_meta["intensity_boost"]))
        if cam_meta.get("static"):
            movement_score = min(movement_score, 24)

        zoom_speed = "fast" if ret["intensity_0_1"] >= 0.9 else ("medium" if ret["intensity_0_1"] >= 0.65 else "slow")
        framing = composition if composition in ("close_up", "wide", "medium") else "medium"

        shot = {
            "scene_id": sid,
            "index": i,
            "camera": camera,
            "cinematography_movement": cam_meta.get("cinematography"),
            "composition": composition,
            "framing": framing,
            "subject_framing": framing,
            "lighting": lighting,
            "color_palette": palette,
            "transition_in": transition,
            "movement_score": movement_score,
            "motion_intensity": movement_score,
            "zoom": cam_meta.get("zoom") or "none",
            "zoom_speed": zoom_speed,
            "angle": cam_meta.get("angle") or "eye_level",
            "timing": {"start_sec": start, "duration_sec": dur, "end_sec": round(start + dur, 2)},
            "duration_sec": dur,
            "emphasis": emphasis,
            "emotional_pacing": {
                "intensity_0_1": ret["intensity_0_1"],
                "intensity_pct": int(round(ret["intensity_0_1"] * 100)),
                "tags": ret["tags"],
                "label": ret["label"],
            },
            "retention_prediction": ret,
            "narration_excerpt": narration[:160],
            "purpose": purpose,
            "director_note": _note(camera, lighting, composition, ret["tags"]),
        }
        shot_list.append(shot)
        camera_plan.append(
            {
                "scene_id": sid,
                "camera": camera,
                "movement": cam_meta.get("cinematography"),
                "zoom_speed": zoom_speed,
                "angle": shot["angle"],
            }
        )
        motion_plan.append(
            {
                "scene_id": sid,
                "movement_score": movement_score,
                "static": bool(cam_meta.get("static")),
                "zoom": shot["zoom"],
                "zoom_speed": zoom_speed,
            }
        )
        timing.append({"scene_id": sid, **shot["timing"]})
        lighting_plan.append({"scene_id": sid, "lighting": lighting, "mood": lighting})
        transition_plan.append({"scene_id": sid, "transition": transition})
        emotional_pacing.append({"scene_id": sid, **shot["emotional_pacing"]})
        director_notes.append(f"{sid}: {shot['director_note']}")
        prev_camera = camera

    package = {
        "package_version": PACKAGE_VERSION,
        "package_type": "cinematic_direction",
        "topic": topic,
        "niche": niche_key,
        "platform": platform,
        "color": palette,
        "shot_list": shot_list,
        "camera_plan": camera_plan,
        "timing": timing,
        "motion_plan": motion_plan,
        "lighting": lighting_plan,
        "color_plan": {"global": palette, "per_scene": [{"scene_id": s["scene_id"], "palette": palette} for s in shot_list]},
        "transition_plan": transition_plan,
        "emotional_pacing": emotional_pacing,
        "director_notes": director_notes,
        "renderer_blueprint": True,
        "render_engine": "existing — maps to visual_package.scenes + cinematography_plan",
    }
    package["validation"] = validate_cinematic_direction(package)

    # Autofix pass if opening weak / repetitive
    if not package["validation"]["ok"]:
        package = _autofix(package)
        package["validation"] = validate_cinematic_direction(package)
        package["autofixed"] = True

    return package


def _note(camera: str, lighting: str, composition: str, tags: list[str]) -> str:
    tag = ",".join(tags) if tags else "steady_story"
    return f"Use {camera} with {composition} framing under {lighting} light — beat={tag}."


def _autofix(package: dict[str, Any]) -> dict[str, Any]:
    shots = list(package.get("shot_list") or [])
    alternates = ["push_in", "orbit", "dolly", "tracking", "macro", "pull_out"]
    prev = ""
    for i, shot in enumerate(shots):
        move = shot.get("camera")
        if i == 0 and int(shot.get("movement_score") or 0) < 55:
            shot["camera"] = "push_in"
            shot["cinematography_movement"] = CAMERA_MOVES["push_in"]["cinematography"]
            shot["movement_score"] = max(70, int(shot.get("movement_score") or 0))
            shot["motion_intensity"] = shot["movement_score"]
            shot["zoom"] = "in"
            shot["zoom_speed"] = "fast"
        if move == prev or move == "static":
            alt = alternates[i % len(alternates)]
            shot["camera"] = alt
            meta = CAMERA_MOVES[alt]
            shot["cinematography_movement"] = meta["cinematography"]
            shot["zoom"] = meta.get("zoom") or "none"
            shot["movement_score"] = max(48, int(shot.get("movement_score") or 40))
            shot["motion_intensity"] = shot["movement_score"]
        prev = shot["camera"]
        package["camera_plan"][i]["camera"] = shot["camera"]
        package["camera_plan"][i]["movement"] = shot["cinematography_movement"]
        package["motion_plan"][i]["movement_score"] = shot["movement_score"]
        package["motion_plan"][i]["static"] = False
    package["shot_list"] = shots
    return package


def apply_cinematic_direction_to_candidate(candidate: dict[str, Any], package: dict[str, Any]) -> dict[str, Any]:
    """Enrich visual_package.scenes with directed fields the renderer already consumes."""
    out = dict(candidate)
    vp = dict(out.get("visual_package") or {})
    scenes = list(vp.get("scenes") or out.get("scenes") or [])
    by_id = {s.get("scene_id"): s for s in package.get("shot_list") or []}

    # If no scenes yet, materialize from shot list
    if not scenes:
        scenes = []
        for shot in package.get("shot_list") or []:
            scenes.append(
                {
                    "scene_id": shot["scene_id"],
                    "narration": shot.get("narration_excerpt") or "",
                    "purpose": shot.get("purpose") or "story_beat",
                    "duration_sec": shot.get("duration_sec"),
                    "start_sec": (shot.get("timing") or {}).get("start_sec"),
                }
            )

    enriched = []
    for i, scene in enumerate(scenes):
        sid = scene.get("scene_id") or f"s{i+1}"
        shot = by_id.get(sid) or (package.get("shot_list") or [None])[min(i, len(package.get("shot_list") or []) - 1)]
        if not shot:
            enriched.append(scene)
            continue
        row = dict(scene)
        row["camera_motion"] = shot.get("cinematography_movement") or shot.get("camera")
        row["camera"] = shot.get("camera")
        row["camera_angle"] = shot.get("angle")
        row["zoom"] = shot.get("zoom")
        row["zoom_speed"] = shot.get("zoom_speed")
        row["motion_intensity"] = shot.get("motion_intensity")
        row["movement_score"] = shot.get("movement_score")
        row["shot_composition"] = shot.get("composition")
        row["lighting"] = shot.get("lighting")
        row["color_palette"] = package.get("color") or shot.get("color_palette")
        row["color_grade_hint"] = (package.get("color") or {}).get("grade_hint") or ""
        row["transition"] = shot.get("transition_in")
        row["transition_in"] = shot.get("transition_in")
        row["text_emphasis"] = (shot.get("emphasis") or {}).get("text_emphasis")
        row["visual_hierarchy"] = (shot.get("emphasis") or {}).get("visual_hierarchy")
        row["cinematic_direction"] = {
            "camera": shot.get("camera"),
            "composition": shot.get("composition"),
            "lighting": shot.get("lighting"),
            "movement_score": shot.get("movement_score"),
            "director_note": shot.get("director_note"),
        }
        enriched.append(row)

    vp["scenes"] = enriched
    vp["cinematic_direction_summary"] = {
        "niche": package.get("niche"),
        "color": package.get("color"),
        "validation": package.get("validation"),
    }
    out["visual_package"] = vp
    out["cinematic_direction_package"] = package
    out["scenes"] = enriched
    return out
