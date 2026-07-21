"""Module 5 — Sound Design Engine: layered audio supporting the story."""

from __future__ import annotations

from core.heuristics import clamp
from services.viewer_retention.models import ScenePacing


def _music_curve(scene_count: int) -> list[dict]:
    if scene_count <= 0:
        return [{"t": 0.0, "intensity": 0.35}]
    curve = []
    for i in range(scene_count + 1):
        t = i / max(1, scene_count)
        # Soft open → rise mid → peak near payoff → gentle resolve
        if t < 0.15:
            intensity = 0.28
        elif t < 0.55:
            intensity = 0.28 + (t - 0.15) * 0.9
        elif t < 0.85:
            intensity = 0.72
        else:
            intensity = 0.45
        curve.append({"t": round(t, 2), "intensity": round(min(0.85, intensity), 2)})
    return curve


def build_sound_design(candidate: dict, pacing: list[ScenePacing] | None = None) -> dict:
    pacing = pacing or []
    n = len(pacing) or 5
    events: list[dict] = []

    for i, p in enumerate(pacing or []):
        label = p.pacing_label
        sid = p.scene_id
        if i == 0:
            events.append(
                {
                    "scene_id": sid,
                    "type": "riser",
                    "intensity": 0.55,
                    "reason": "Hook riser into opening claim",
                }
            )
        if label in ("cut_2s", "montage"):
            events.append(
                {
                    "scene_id": sid,
                    "type": "whoosh",
                    "intensity": 0.4,
                    "reason": "Fast cut transition whoosh",
                }
            )
        if label == "dramatic_pause":
            events.append(
                {
                    "scene_id": sid,
                    "type": "intentional_silence",
                    "intensity": 0.0,
                    "duration_ms": 350,
                    "reason": "Silence underlines importance",
                }
            )
        if p.importance >= 85:
            events.append(
                {
                    "scene_id": sid,
                    "type": "impact_hit",
                    "intensity": 0.6,
                    "reason": "Key educational beat impact",
                }
            )
        if label == "zoom_rhythm":
            events.append(
                {
                    "scene_id": sid,
                    "type": "bass_drop",
                    "intensity": 0.35,
                    "reason": "Subtle bass under zoom rhythm",
                }
            )

    # Environmental bed from topic keywords
    title = str(candidate.get("title") or candidate.get("topic") or "").lower()
    ambience = "soft_studio_room"
    if any(w in title for w in ("ocean", "coral", "sea", "turtle")):
        ambience = "underwater_soft"
    elif any(w in title for w in ("space", "planet", "nasa", "earth")):
        ambience = "space_hum"
    elif any(w in title for w in ("factory", "chip", "robot", "ai")):
        ambience = "tech_room_hum"

    existing = candidate.get("audio_package") or {}
    duck = True
    score = clamp(
        55
        + min(25, len(events) * 3)
        + (10 if duck else 0)
        + (8 if ambience != "soft_studio_room" else 0),
        0,
        100,
    )

    return {
        "ambience": ambience,
        "music_intensity_curve": _music_curve(n),
        "events": events,
        "ducking": {
            "enabled": duck,
            "narration_priority": True,
            "music_under_narration_db": -14,
        },
        "silence_policy": "intentional_only",
        "inherits_audio_package": bool(existing),
        "score": score,
        "guidance": [
            "Music ducks beneath narration",
            "Whooshes only on cuts that need energy",
            "Use silence as punctuation, never as absence",
        ],
    }
