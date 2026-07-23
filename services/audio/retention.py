"""Retention pacing notes — the audio events that keep viewers from leaving.

Short-form retention data says the ear notices change before the eye:
a sound event (SFX hit, music section change, pause, delivery shift) every
few seconds keeps the brain from marking the video "predictable". This
module audits the planned audio timeline and emits concrete, scene-anchored
retention notes plus a 0-100 retention-audio fitness score.
"""

from __future__ import annotations

from core.heuristics import clamp

# An audio change roughly every 3-6 seconds keeps short-form attention;
# translated to events per 10 seconds.
IDEAL_EVENTS_PER_10S_LOW = 1.5
IDEAL_EVENTS_PER_10S_HIGH = 4.0


def build_retention_notes(scenes: list, *, sfx_plan: dict, music_direction: dict, narration_plan: dict) -> dict:
    """Audit the audio timeline and emit retention pacing notes (JSON-safe dict)."""
    if not scenes:
        return {"notes": [], "audio_events": 0, "events_per_10s": 0.0, "fitness": 0, "verdict": "no scenes to audit"}

    runtime = float(scenes[-1].get("caption_timing", {}).get("end_sec", 0) or 0) or sum(
        float(scene.get("length_sec", 0) or 0) for scene in scenes
    )
    sfx_events = sfx_plan.get("total_cues", 0)
    section_changes = max(0, len(music_direction.get("sections", [])) - 1)
    pause_events = sum(len(segment.get("pauses", [])) for segment in narration_plan.get("segments", []))
    events = sfx_events + section_changes + pause_events
    events_per_10s = round(events / runtime * 10, 1) if runtime else 0.0

    notes = []

    first_scene = scenes[0]
    first_cues = next(iter(sfx_plan.get("scenes", [])), {}).get("cues", [])
    if any(cue["time_sec"] <= 0.5 for cue in first_cues):
        notes.append("Scene 1: sonic impact lands inside the first half-second — the ear commits before the eye does.")
    else:
        notes.append("Scene 1: add a hard sound event inside the first 0.5s — silence at open reads as a dead video.")

    payoff = next((scene for scene in scenes if scene.get("purpose") == "payoff"), None)
    if payoff:
        start = payoff.get("caption_timing", {}).get("start_sec", 0)
        notes.append(
            f"Scene {payoff.get('scene_number')}: cut the music bed to silence for ~0.5s at {start}s before the reveal — "
            "the loudest moment in a video is the silence before the payoff."
        )

    if events_per_10s < IDEAL_EVENTS_PER_10S_LOW:
        notes.append(
            f"Audio timeline is too static ({events_per_10s} events/10s) — add SFX or music movement so something "
            "changes every 3-6 seconds."
        )
    elif events_per_10s > IDEAL_EVENTS_PER_10S_HIGH:
        notes.append(
            f"Audio timeline is crowded ({events_per_10s} events/10s) — thin the low-intensity layers so the big hits keep contrast."
        )
    else:
        notes.append(f"Audio change rate is in the retention sweet spot ({events_per_10s} events/10s).")

    if runtime >= 20:
        midpoint = round(runtime / 2, 1)
        notes.append(f"Insert a texture reset near {midpoint}s (drop a layer or shift the groove) to defeat mid-video drift.")

    cta = next((scene for scene in scenes if scene.get("purpose") == "cta"), None)
    if cta:
        notes.append(
            f"Scene {cta.get('scene_number')}: strip the mix under the CTA — a quieter close makes the ask feel personal "
            "and cues a natural rewatch loop."
        )

    notes.append(f"Narration pacing: {narration_plan.get('pacing_verdict', '')}")

    deviation = 0.0
    if events_per_10s < IDEAL_EVENTS_PER_10S_LOW:
        deviation = IDEAL_EVENTS_PER_10S_LOW - events_per_10s
    elif events_per_10s > IDEAL_EVENTS_PER_10S_HIGH:
        deviation = events_per_10s - IDEAL_EVENTS_PER_10S_HIGH
    fitness = clamp(95 - deviation * 20, low=10, high=95)

    if deviation == 0:
        verdict = "audio pacing on target for short-form retention"
    elif events_per_10s < IDEAL_EVENTS_PER_10S_LOW:
        verdict = "too few audio events — viewers' ears will flag the video as static"
    else:
        verdict = "too many audio events — hits lose contrast and fatigue sets in"

    return {
        "notes": notes,
        "audio_events": events,
        "events_per_10s": events_per_10s,
        "runtime_sec": round(runtime, 1),
        "fitness": fitness,
        "verdict": verdict,
    }
