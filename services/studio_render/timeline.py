"""Module 1 — Master Timeline: synchronized production layers."""

from __future__ import annotations

from typing import Any


def _scenes(candidate: dict) -> list[dict]:
    vp = candidate.get("visual_package") or {}
    scenes = list(vp.get("scenes") or [])
    if scenes:
        return scenes
    ep = candidate.get("evidence_package") or {}
    return list(ep.get("scenes") or [])


def _pacing(candidate: dict) -> list[dict]:
    pkg = candidate.get("viewer_retention_package") or {}
    plan = pkg.get("pacing_plan") or (candidate.get("visual_package") or {}).get("pacing_plan_v2") or []
    return list(plan)


def build_master_timeline(candidate: dict, *, layers: dict[str, Any] | None = None) -> dict:
    """Unified timeline with every visual/audio/graphics layer."""
    layers = layers or {}
    scenes = _scenes(candidate)
    pacing = _pacing(candidate)
    vr = candidate.get("viewer_retention_package") or {}
    cine = candidate.get("cinematography_plan") or {}
    audio = candidate.get("audio_package") or vr.get("sound_design") or {}
    captions = vr.get("caption_plan") or (candidate.get("visual_package") or {}).get("caption_plan_v2") or {}

    tracks: list[dict] = []
    t = 0.0
    for i, scene in enumerate(scenes or [{"scene_id": "s1", "narration": str(candidate.get("hook") or "")}]):
        sid = str(scene.get("scene_id") or f"s{i+1}")
        dur = 3.0
        if i < len(pacing):
            dur = float(pacing[i].get("duration_sec") or dur)
        elif scene.get("length_sec"):
            dur = float(scene["length_sec"])

        camera = None
        for cs in (cine.get("scenes") or []):
            if str(cs.get("scene_id")) == sid:
                camera = cs
                break
        if not camera and i < len(layers.get("camera_choreography") or []):
            camera = layers["camera_choreography"][i]

        tracks.append(
            {
                "scene_id": sid,
                "start_sec": round(t, 3),
                "end_sec": round(t + dur, 3),
                "duration_sec": round(dur, 3),
                "narration": str(scene.get("narration") or scene.get("voiceover") or "")[:200],
                "camera": {
                    "movement": (camera or {}).get("movement") or (camera or {}).get("v2_motion") or "slow_push",
                    "intensity": (camera or {}).get("v2_intensity") or (camera or {}).get("intensity") or 0.6,
                },
                "transition_in": (layers.get("transitions") or [{}])[min(i, max(0, len(layers.get("transitions") or []) - 1))].get("type")
                if layers.get("transitions")
                else "cross_dissolve",
                "color_grade": (layers.get("color_grade") or {}).get("profile"),
                "motion_graphics": [
                    g for g in (layers.get("motion_graphics") or []) if g.get("scene_id") == sid
                ],
                "vfx": [e for e in (layers.get("visual_effects") or []) if e.get("scene_id") == sid],
                "diagram": next(
                    (d for d in (layers.get("diagrams") or []) if d.get("scene_id") == sid),
                    None,
                ),
            }
        )
        t += dur

    caption_cues = list((captions.get("cues") if isinstance(captions, dict) else []) or [])
    music_curve = list((audio.get("music_intensity_curve") if isinstance(audio, dict) else []) or [])

    return {
        "version": "3.0",
        "total_duration_sec": round(t, 3),
        "scene_count": len(tracks),
        "tracks": {
            "video": tracks,
            "camera": [tr["camera"] for tr in tracks],
            "narration": [{"scene_id": tr["scene_id"], "text": tr["narration"], "start": tr["start_sec"], "end": tr["end_sec"]} for tr in tracks],
            "subtitles": caption_cues,
            "music_intensity": music_curve,
            "sfx": list((audio.get("events") if isinstance(audio, dict) else []) or []),
            "transitions": layers.get("transitions") or [],
            "motion_graphics": layers.get("motion_graphics") or [],
            "visual_effects": layers.get("visual_effects") or [],
            "color": layers.get("color_grade") or {},
            "typography": layers.get("typography") or {},
            "diagrams": layers.get("diagrams") or [],
            "broll": layers.get("broll_plan") or [],
        },
        "synchronized": True,
    }
