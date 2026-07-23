"""Music direction and audio mood — the emotional bed under the edit.

Turns the storyboard's music style, motion intensities, and emotional arc
into a concrete brief for a composer / music library search / future music
provider: tempo range, key/mode, per-scene energy curve, named sections
mapped to scene purposes, and ducking guidance. Also derives the overall
audio mood and its scene-by-scene progression.
"""

from __future__ import annotations

from core.heuristics import clamp

DEFAULT_MUSIC_STYLE = "understated cinematic underscore"

# Music section per scene purpose — how the track should behave under each beat.
PURPOSE_MUSIC_SECTIONS = {
    "hook": "cold-open sting — instant identity, no intro bar",
    "pattern_interrupt": "stutter break — cut the bed for the reversal",
    "curiosity_loop": "low pulse build — sparse, rising anticipation",
    "story_beat": "driving groove — steady momentum under the narrative",
    "payoff": "full swell — widest arrangement of the track",
    "cta": "stripped-back outro — bed thins so the ask feels personal",
}

# Emotions that pull the track toward a minor key.
TENSE_EMOTIONS = {"tension", "fear", "shock", "skepticism", "intrigue"}

# Audio mood per emotion — the sonic complement to EMOTION_LOOKS in
# services/visual/scenes.py.
EMOTION_AUDIO_MOODS = {
    "curiosity": "inquisitive undertow",
    "intrigue": "shadowed pull",
    "anticipation": "rising static",
    "skepticism": "dry, held-back tension",
    "tension": "coiled unease",
    "empathy": "warm closeness",
    "shock": "sudden cold drop",
    "surprise": "bright jolt",
    "revelation": "breaking daylight",
    "recognition": "familiar echo",
    "understanding": "settling clarity",
    "vindication": "triumphant lift",
    "reflection": "quiet afterglow",
    "clarity": "clean open air",
    "resolve": "grounded confidence",
    "connection": "shared warmth",
    "confidence": "forward stride",
    "satisfaction": "full resolution",
}
DEFAULT_AUDIO_MOOD = "focused momentum"


def _scene_energy(scene: dict) -> int:
    """0-100 musical energy for one scene — motion plus purpose weighting."""
    base = int(scene.get("motion_intensity", 50) or 50)
    boost = {"hook": 10, "payoff": 12, "pattern_interrupt": 8}.get(scene.get("purpose", ""), 0)
    calm = {"cta": -15, "curiosity_loop": -5}.get(scene.get("purpose", ""), 0)
    return clamp(base + boost + calm, low=5, high=100)


def build_music_direction(scenes: list, *, music_style: str = "") -> dict:
    """The complete background-music brief for one idea (JSON-safe dict)."""
    style = music_style or next(
        (scene.get("music_style") for scene in scenes if scene.get("music_style")),
        DEFAULT_MUSIC_STYLE,
    )

    intensities = [int(scene.get("motion_intensity", 50) or 50) for scene in scenes] or [50]
    average_motion = sum(intensities) / len(intensities)
    bpm_low = int(clamp(60 + average_motion * 0.8, low=60, high=140))
    bpm_high = min(bpm_low + 15, 150)

    emotions = [scene.get("emotion", "") for scene in scenes]
    tense_hits = sum(1 for emotion in emotions if emotion in TENSE_EMOTIONS)
    key_mode = "minor" if tense_hits >= max(1, len(emotions) // 3) else "major"

    energy_curve = [
        {"scene_number": scene.get("scene_number", 0), "energy": _scene_energy(scene)}
        for scene in scenes
    ]
    sections = [
        {
            "scene_number": scene.get("scene_number", 0),
            "start_sec": scene.get("caption_timing", {}).get("start_sec", 0),
            "end_sec": scene.get("caption_timing", {}).get("end_sec", 0),
            "section": PURPOSE_MUSIC_SECTIONS.get(scene.get("purpose", ""), PURPOSE_MUSIC_SECTIONS["story_beat"]),
        }
        for scene in scenes
    ]

    energies = [point["energy"] for point in energy_curve] or [0]
    return {
        "style": style,
        "bpm_range": [bpm_low, bpm_high],
        "key_mode": key_mode,
        "energy_curve": energy_curve,
        "peak_energy": max(energies),
        "dynamic_range": max(energies) - min(energies),
        "sections": sections,
        "ducking": "sidechain the bed -10 dB under narration; -6 dB on hook sting; breathe back on pauses; never drown VO",
        "hook_sting": "cold-open identity hit in first 0.4s then duck hard",
        "transition_rule": "riser into payoff; thin bed under CTA",
        "sfx_cues": "mark every pacing-label change with a light whoosh or click",
        "loop_note": "end the outro on an unresolved tail so replays feel seamless",
    }


def build_audio_mood(scenes: list) -> dict:
    """Overall audio mood plus the scene-by-scene mood progression."""
    progression = [
        {
            "scene_number": scene.get("scene_number", 0),
            "emotion": scene.get("emotion", ""),
            "mood": EMOTION_AUDIO_MOODS.get(scene.get("emotion", ""), DEFAULT_AUDIO_MOOD),
        }
        for scene in scenes
    ]
    if progression:
        overall = f"opens on {progression[0]['mood']}, resolves into {progression[-1]['mood']}"
    else:
        overall = DEFAULT_AUDIO_MOOD
    distinct = len({point["mood"] for point in progression}) if progression else 0
    variety = clamp((distinct / len(progression)) * 100, low=10, high=98) if progression else 0
    return {
        "overall": overall,
        "progression": progression,
        "variety_score": variety,
    }
