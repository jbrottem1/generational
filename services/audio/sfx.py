"""Sound effect planner — the SFX layer of every scene.

Each scene gets its primary effect (carried over from the visual storyboard,
which already assigned one per purpose or from the script's SFX bank) plus
purpose-specific support layers: transition swishes, risers under curiosity
builds, ambience beds. Effects are recommendations for the sound designer /
future audio renderer — no audio is generated here.
"""

from __future__ import annotations

from core.heuristics import clamp

# Support layers per scene purpose, on top of the scene's primary effect.
# Data, not code — sound-design changes are edits to this table.
PURPOSE_SFX_LAYERS = {
    "hook": [
        {"effect": "airy whoosh into the first frame", "layer": "transition", "offset_sec": 0.0, "intensity": "high"},
    ],
    "pattern_interrupt": [
        {"effect": "tape-stop drop-out", "layer": "transition", "offset_sec": 0.0, "intensity": "high"},
    ],
    "curiosity_loop": [
        {"effect": "low tension drone under the tease", "layer": "ambience", "offset_sec": 0.2, "intensity": "low"},
    ],
    "story_beat": [
        {"effect": "soft tick or pop on each text overlay", "layer": "ui", "offset_sec": 0.5, "intensity": "low"},
    ],
    "payoff": [
        {"effect": "shimmer swell resolving with the reveal", "layer": "sweetener", "offset_sec": 0.3, "intensity": "medium"},
    ],
    "cta": [
        {"effect": "subtle pop on the follow-button overlay", "layer": "ui", "offset_sec": 0.5, "intensity": "low"},
    ],
}


def plan_scene_sfx(scene: dict) -> list:
    """All recommended effects for one scene, primary first (JSON-safe dicts)."""
    start = float(scene.get("caption_timing", {}).get("start_sec", 0) or 0)
    purpose = scene.get("purpose", "story_beat")

    cues = []
    primary = scene.get("sound_effect", "")
    if primary:
        cues.append(
            {
                "effect": primary,
                "layer": "primary",
                "time_sec": round(start, 1),
                "intensity": "high" if purpose in ("hook", "payoff") else "medium",
                "source": "storyboard",
            }
        )
    for extra in PURPOSE_SFX_LAYERS.get(purpose, []):
        cues.append(
            {
                "effect": extra["effect"],
                "layer": extra["layer"],
                "time_sec": round(start + extra["offset_sec"], 1),
                "intensity": extra["intensity"],
                "source": "purpose_grammar",
            }
        )
    return cues


def build_sfx_plan(scenes: list) -> dict:
    """Per-scene SFX recommendations plus coverage diagnostics."""
    by_scene = [
        {"scene_number": scene.get("scene_number", 0), "cues": plan_scene_sfx(scene)}
        for scene in scenes
    ]
    covered = sum(1 for entry in by_scene if entry["cues"])
    total_cues = sum(len(entry["cues"]) for entry in by_scene)
    coverage = clamp((covered / len(scenes)) * 95, low=0, high=95) if scenes else 0
    return {
        "scenes": by_scene,
        "total_cues": total_cues,
        "scene_coverage_pct": round(covered / len(scenes) * 100, 1) if scenes else 0.0,
        "coverage_score": coverage,
        "mix_note": "Keep SFX peaks 3-6 dB under narration; never stack two high-intensity hits inside one second.",
    }
