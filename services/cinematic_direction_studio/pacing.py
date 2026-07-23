"""Pacing — shot duration, pauses, dialogue spacing, rhythm."""

from __future__ import annotations

from typing import Any


def plan_pacing(
    *,
    duration_sec: float,
    emotion: str,
    shot_type: str,
    actor_beats: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    dur = max(float(duration_sec or 3.0), 1.0)
    emotion = str(emotion or "curiosity").lower()

    # Emotion shapes pause density
    pause_scale = {
        "reflection": 1.35,
        "wonder": 1.2,
        "inspiration": 1.15,
        "resolution": 1.25,
        "urgency": 0.7,
        "curiosity": 1.0,
        "understanding": 1.05,
        "teaching": 1.0,
    }.get(emotion, 1.0)

    pause_sec = min(0.85, max(0.25, 0.35 * pause_scale))
    dialogue_gap = min(0.55, max(0.15, 0.22 * pause_scale))

    # Camera rhythm — slower for reflection/wonder
    camera_rhythm = "measured"
    if emotion in {"urgency"}:
        camera_rhythm = "pressing"
    elif emotion in {"reflection", "wonder", "inspiration"}:
        camera_rhythm = "glacial"
    elif shot_type in {"tracking", "follow"}:
        camera_rhythm = "walking_tempo"

    pause_marks = []
    for beat in actor_beats or []:
        if str(beat.get("action") or "") in {"pause", "breathe", "stop"}:
            pause_marks.append({"t": float(beat.get("t") or 0), "duration_sec": pause_sec})

    if not pause_marks:
        pause_marks = [{"t": dur * 0.4, "duration_sec": pause_sec}]

    return {
        "shot_duration_sec": dur,
        "pause_timing": pause_marks,
        "dialogue_spacing_sec": round(dialogue_gap, 3),
        "camera_rhythm": camera_rhythm,
        "movement_rhythm": "actor_leads" if shot_type in {"tracking", "follow"} else "shared",
        "scene_transition_hold_sec": round(min(0.4, dur * 0.08), 3),
        "forbid_machine_gun_cuts": True,
        "forbid_static_dead_air_over_sec": 3.0,
    }
