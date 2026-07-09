"""Master production timeline — scenes, shots, animation, audio, effects.

Builds the single timeline every downstream renderer / editor consumes.
Duration is unbounded: 15-second shorts through multi-hour productions.
"""

from __future__ import annotations

from services.animation.config import AnimationConfig


def _frames(sec: float, fps: int) -> int:
    return int(round(float(sec) * fps))


def build_scene_timing(
    scenes: "list[dict]",
    shot_list: "list[dict]",
    config: AnimationConfig,
) -> "list[dict]":
    """Assign absolute start/end times to every scene."""
    # Prefer explicit durations; otherwise distribute target duration.
    raw = [
        max(0.5, float(scene.get("estimated_duration_sec", 0) or 0))
        for scene in scenes
    ]
    if not scenes:
        return []

    if all(d == 0.5 and not (scene.get("estimated_duration_sec")) for scene, d in zip(scenes, raw)):
        # No durations provided — invent a measured pacing.
        target = config.target_duration_sec or max(15.0, 3.0 * len(scenes))
        each = target / len(scenes)
        raw = [each] * len(scenes)
    elif config.target_duration_sec and config.target_duration_sec > 0:
        total = sum(raw) or 1.0
        scale = config.target_duration_sec / total
        raw = [max(0.5, d * scale) for d in raw]

    shots_by_scene: "dict[str, list]" = {}
    for shot in shot_list:
        shots_by_scene.setdefault(str(shot.get("scene_id", "")), []).append(shot)

    timing: "list[dict]" = []
    cursor = 0.0
    for scene, duration in zip(scenes, raw):
        scene_id = str(scene.get("scene_id", f"scene_{len(timing) + 1}"))
        end = cursor + duration
        timing.append({
            "scene_id": scene_id,
            "start_sec": round(cursor, 3),
            "end_sec": round(end, 3),
            "duration_sec": round(duration, 3),
            "shot_ids": [
                str(s.get("shot_id", ""))
                for s in shots_by_scene.get(scene_id, [])
            ],
            "purpose": str(scene.get("purpose", "")),
        })
        cursor = end
    return timing


def build_timeline(
    scene_timing: "list[dict]",
    camera_plan: dict,
    character_motion: "list[dict]",
    facial_animation: "list[dict]",
    lip_sync_plan: "list[dict]",
    transitions: "list[dict]",
    visual_effects: "list[dict]",
    audio_sync: "list[dict]",
    subtitle_timing: "list[dict]",
    config: AnimationConfig,
    item: dict,
) -> dict:
    """Assemble the master multi-track timeline."""
    fps = max(1, int(config.fps))
    total = scene_timing[-1]["end_sec"] if scene_timing else 0.0
    if config.target_duration_sec and not scene_timing:
        total = float(config.target_duration_sec)

    def clip(clip_id: str, ref_id: str, start: float, end: float, label: str = "") -> dict:
        return {
            "clip_id": clip_id,
            "ref_id": ref_id,
            "start_sec": round(start, 3),
            "end_sec": round(end, 3),
            "start_frame": _frames(start, fps),
            "end_frame": _frames(end, fps),
            "label": label,
        }

    scene_clips = [
        clip(f"tl_scene_{t['scene_id']}", t["scene_id"], t["start_sec"], t["end_sec"], t.get("purpose", ""))
        for t in scene_timing
    ]
    shot_clips = [
        clip(f"tl_shot_{s['shot_id']}", s["shot_id"], s["start_sec"], s["end_sec"], s.get("shot_type", ""))
        for s in camera_plan.get("shots", [])
    ]
    anim_clips = [
        clip(
            f"tl_anim_{m['motion_id']}",
            m["motion_id"],
            min((a.get("start_sec", 0) for a in m.get("actions", [])), default=0),
            max((a.get("end_sec", 0) for a in m.get("actions", [])), default=0),
            m.get("character_id", ""),
        )
        for m in character_motion
    ]
    facial_clips = [
        clip(f"tl_face_{f['facial_id']}", f["facial_id"], f["start_sec"], f["end_sec"], f.get("expression", ""))
        for f in facial_animation
    ]
    lip_clips = [
        clip(
            f"tl_lip_{p['lip_sync_id']}",
            p["lip_sync_id"],
            min((w.get("start_sec", 0) for w in p.get("words", [])), default=0)
            if p.get("words") else 0,
            max((w.get("end_sec", 0) for w in p.get("words", [])), default=0)
            if p.get("words") else 0,
            p.get("character_id", ""),
        )
        for p in lip_sync_plan
    ]
    transition_clips = [
        clip(
            f"tl_tr_{t['transition_id']}",
            t["transition_id"],
            t["at_sec"],
            t["at_sec"] + float(t.get("duration_sec", 0.2)),
            t.get("transition_type", ""),
        )
        for t in transitions
    ]
    effect_clips = [
        clip(f"tl_fx_{e['effect_id']}", e["effect_id"], e["start_sec"], e["end_sec"], e.get("effect_type", ""))
        for e in visual_effects
    ]
    audio_clips = [
        clip(f"tl_aud_{a['sync_id']}", a["sync_id"], a["start_sec"], a["end_sec"], a.get("track", ""))
        for a in audio_sync
    ]
    subtitle_clips = [
        clip(f"tl_sub_{s['cue_id']}", s["cue_id"], s["start_sec"], s["end_sec"], s.get("text", "")[:40])
        for s in subtitle_timing
    ]

    markers = []
    for timing in scene_timing:
        markers.append({
            "marker_id": f"marker_{timing['scene_id']}",
            "at_sec": timing["start_sec"],
            "label": timing.get("purpose") or timing["scene_id"],
            "kind": "scene",
        })

    platforms = item.get("target_platforms") or item.get("platforms") or [config.target_platform]
    return {
        "timeline_id": f"timeline_{item.get('project_id', 'anon')}",
        "fps": fps,
        "total_duration_sec": round(total, 3),
        "total_frames": _frames(total, fps),
        "tracks": [
            {"track_id": "track_scenes", "track_type": "scene", "clips": scene_clips},
            {"track_id": "track_shots", "track_type": "shot", "clips": shot_clips},
            {"track_id": "track_animation", "track_type": "animation", "clips": anim_clips + facial_clips + lip_clips},
            {"track_id": "track_audio", "track_type": "audio", "clips": audio_clips},
            {"track_id": "track_music", "track_type": "music", "clips": [c for c in audio_clips if c["label"] == "music"]},
            {"track_id": "track_subtitles", "track_type": "subtitle", "clips": subtitle_clips},
            {"track_id": "track_effects", "track_type": "effects", "clips": effect_clips},
            {"track_id": "track_transitions", "track_type": "transition", "clips": transition_clips},
        ],
        "markers": markers,
        "publishing_metadata": {
            "target_platforms": list(platforms),
            "aspect_ratio": config.target_aspect_ratio,
            "series_ready": bool(item.get("series_id")),
            "project_id": str(item.get("project_id", "")),
        },
    }
