"""Storyboard package builder — animation-first expansion (no Orchestrator redesign).

Converts scene breakdowns into beats answering: who, doing, moving, camera, emotion, transition.
"""

from __future__ import annotations

from typing import Any

_CAMERA_BY_PURPOSE = {
    "hook": "push_in",
    "story_beat": "tracking",
    "curiosity_loop": "parallax",
    "payoff": "pull_out",
    "cta": "close_up",
    "pattern_interrupt": "handheld_energy",
}

_ACTION_CYCLE = (
    "walk_cycle",
    "talk_bob",
    "point_right",
    "think_scratch",
    "shock_recoil",
    "celebrate_jump",
    "face_audience",
)

_ENV_CYCLE = (
    "ENVFX-particle-field",
    "ENVFX-light-pulse",
    "ENVFX-dust-motes",
    "ENVFX-instrument-glow",
    "ENVFX-ocean-current",
    "ENVFX-star-twinkle",
)


def _purpose(scene: dict) -> str:
    raw = str(scene.get("purpose") or scene.get("segment_type") or "story_beat").lower()
    for key in _CAMERA_BY_PURPOSE:
        if key in raw:
            return key
    return "story_beat"


def build_storyboard_beat(scene: dict, *, index: int = 0, character_id: str = "CHAR-DASH") -> dict[str, Any]:
    """Build one storyboard beat from a scene dict."""
    purpose = _purpose(scene)
    t0 = float(scene.get("start_sec") or scene.get("t_start") or index * 4.0)
    dur = float(scene.get("length_sec") or scene.get("duration_sec") or 4.0)
    action = _ACTION_CYCLE[index % len(_ACTION_CYCLE)]
    env = _ENV_CYCLE[index % len(_ENV_CYCLE)]
    camera = (
        str(scene.get("camera_motion") or scene.get("camera") or "").strip()
        or _CAMERA_BY_PURPOSE.get(purpose, "tracking")
    )
    # Normalize free-text camera motion to nearest preset token when possible
    cam_l = camera.lower().replace("-", "_").replace(" ", "_")
    for preset in _CAMERA_BY_PURPOSE.values():
        if preset in cam_l or cam_l in preset:
            camera = preset
            break
    if "punch" in cam_l or "push" in cam_l:
        camera = "push_in"
    elif "pull" in cam_l or "reveal" in cam_l:
        camera = "pull_out" if "pull" in cam_l else "reveal"
    elif "orbit" in cam_l:
        camera = "orbit"
    elif "parallax" in cam_l or "pan" in cam_l:
        camera = "parallax"
    elif "chase" in cam_l or "handheld" in cam_l:
        camera = "handheld_energy"
    elif "close" in cam_l:
        camera = "close_up"
    elif "macro" in cam_l:
        camera = "macro"
    elif "overhead" in cam_l or "top" in cam_l:
        camera = "overhead"
    elif "track" in cam_l or "follow" in cam_l:
        camera = "tracking"
    elif "wide" in cam_l or "establish" in cam_l:
        camera = "establishing_wide"
    elif "crane" in cam_l:
        camera = "crane"

    emotion = str(scene.get("emotion") or purpose or "curious")
    narration = str(scene.get("narration") or "")
    return {
        "beat_id": f"B{int(scene.get('scene_number') or index + 1)}",
        "scene_number": scene.get("scene_number") or index + 1,
        "t_start": t0,
        "t_end": t0 + dur,
        "duration_sec": dur,
        "narration": narration,
        "who": [character_id],
        "action": action,
        "doing": action,
        "moving": ["character", env],
        "camera": camera,
        "emotion": emotion,
        "transition_out": str(scene.get("transition_out") or "hard_cut"),
        "environment_fx": [env],
        "animation_components": [action, "talk_bob"] if narration else [action],
        "purpose": purpose,
    }


def build_storyboard_package(
    scenes: list,
    *,
    title: str = "",
    character_id: str = "CHAR-DASH",
    series_id: str = "SERIES-DASH-SCIENCE",
) -> dict[str, Any]:
    """Build a full storyboard_package for animation-first production."""
    beats = []
    for i, scene in enumerate(scenes or []):
        if not isinstance(scene, dict):
            continue
        beats.append(build_storyboard_beat(scene, index=i, character_id=character_id))
    return {
        "package_type": "storyboard_package",
        "version": "1.0.0",
        "title": title,
        "series_id": series_id,
        "character_id": character_id,
        "department": "Animation Studio",
        "animation_director": 16,
        "beat_count": len(beats),
        "beats": beats,
        "protocol": "data/animation_studio/STORYBOARD_PROTOCOL.md",
    }


def attach_storyboard_to_scenes(scenes: list, storyboard: dict) -> list:
    """Copy beat fields onto scenes for downstream visual/animation use."""
    by_num = {
        int(b.get("scene_number") or 0): b
        for b in (storyboard.get("beats") or [])
        if isinstance(b, dict)
    }
    out = []
    for i, scene in enumerate(scenes or []):
        if not isinstance(scene, dict):
            continue
        s = dict(scene)
        beat = by_num.get(int(s.get("scene_number") or i + 1)) or {}
        if beat:
            s["storyboard_beat"] = beat
            s.setdefault("camera_preset", beat.get("camera"))
            s.setdefault("environment_fx", beat.get("environment_fx"))
            s.setdefault("animation_components", beat.get("animation_components"))
            s.setdefault("emotion", beat.get("emotion"))
        out.append(s)
    return out
