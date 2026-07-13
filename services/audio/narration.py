"""Narration planner — how every scene should be read aloud.

Each storyboard scene gets a delivery direction, a target words-per-minute
(platform base modulated per scene purpose), scripted pauses, and the words
to emphasize. Everything is deterministic text analysis, so the plan is
reproducible in Demo Mode and unit-testable without an API key.
"""

from __future__ import annotations

import re

from engines.heuristics import (
    CURIOSITY_WORDS,
    EMOTION_WORDS,
    SURPRISE_WORDS,
    clamp,
    content_words,
)

# Delivery grammar per scene purpose. Data, not code — a direction change is
# an edit to this table, never to the planner (mirrors PURPOSE_GRAMMAR in
# services/visual/scenes.py).
PURPOSE_DELIVERY = {
    "hook": {
        "delivery": "urgent, leaning-in open — hit the first word hard and don't let the energy dip",
        "wpm_factor": 1.10,
        "pause": {"at": "after the opening line", "duration_sec": 0.3, "reason": "let the hook land before the next beat"},
    },
    "pattern_interrupt": {
        "delivery": "sharp tonal swerve — drop pitch and flatten the read to sell the reversal",
        "wpm_factor": 1.05,
        "pause": {"at": "before the contradicting word", "duration_sec": 0.25, "reason": "set up the whiplash"},
    },
    "curiosity_loop": {
        "delivery": "hushed, conspiratorial tease — pull the volume down and slow slightly",
        "wpm_factor": 0.95,
        "pause": {"at": "before the tease line", "duration_sec": 0.4, "reason": "open the curiosity gap"},
    },
    "story_beat": {
        "delivery": "confident storytelling stride — ride the rhythm and lift on every number or stat",
        "wpm_factor": 1.0,
        "pause": {"at": "after the key fact", "duration_sec": 0.2, "reason": "let the fact register"},
    },
    "payoff": {
        "delivery": "slow down and let the reveal breathe — near-whisper into full-voice resolve",
        "wpm_factor": 0.85,
        "pause": {"at": "before the reveal line", "duration_sec": 0.7, "reason": "dramatic silence sells the payoff"},
    },
    "cta": {
        "delivery": "warm, direct, eye-contact sincerity — relaxed and unhurried",
        "wpm_factor": 0.90,
        "pause": {"at": "before the final word", "duration_sec": 0.3, "reason": "a settled close feels intentional"},
    },
}
DEFAULT_DELIVERY = PURPOSE_DELIVERY["story_beat"]

# Pace label thresholds against the platform's base words-per-minute.
PACE_LABELS = ((1.05, "fast"), (0.95, "steady"), (0.0, "measured"))

MAX_PAUSES_PER_SCENE = 4
MAX_EMPHASIS_WORDS = 4

# Ideal delivery window: how far a scene's actual reading speed may drift
# from its target before pacing fitness degrades.
WPM_TOLERANCE = 25


def target_wpm(purpose: str, base_wpm: int) -> int:
    factor = PURPOSE_DELIVERY.get(purpose, DEFAULT_DELIVERY)["wpm_factor"]
    return int(round(base_wpm * factor))


def pace_label(purpose: str) -> str:
    factor = PURPOSE_DELIVERY.get(purpose, DEFAULT_DELIVERY)["wpm_factor"]
    for threshold, label in PACE_LABELS:
        if factor >= threshold:
            return label
    return PACE_LABELS[-1][1]


def plan_pauses(narration: str, purpose: str) -> list:
    """Scripted pause markers for one scene's narration."""
    pauses = [dict(PURPOSE_DELIVERY.get(purpose, DEFAULT_DELIVERY)["pause"])]
    for _ in range(narration.count("?")):
        pauses.append(
            {"at": "after the question", "duration_sec": 0.35, "reason": "give the viewer a beat to answer internally"}
        )
    if "…" in narration or "..." in narration:
        pauses.append({"at": "on the ellipsis", "duration_sec": 0.3, "reason": "hold the suspense the writing set up"})
    return pauses[:MAX_PAUSES_PER_SCENE]


def pick_emphasis(narration: str) -> list:
    """The words to stress in the read — numbers first, then trigger words."""
    picks: list = []

    for token in re.findall(r"\b\d[\d,.%]*\b", narration):
        if token not in picks:
            picks.append(token)

    lower = narration.lower()
    for bank in (CURIOSITY_WORDS, SURPRISE_WORDS, EMOTION_WORDS):
        for word in bank:
            if word in lower and word not in picks:
                picks.append(word)

    if not picks:
        picks = content_words(narration)[:2]
    return picks[:MAX_EMPHASIS_WORDS]


def _actual_wpm(narration: str, length_sec: float) -> int:
    words = len(narration.split())
    return int(round(words / length_sec * 60)) if length_sec else 0


def build_narration_plan(scenes: list, *, base_wpm: int, voice_style: dict) -> dict:
    """The full read plan: per-scene delivery segments plus global pacing."""
    segments = []
    deviations = []
    for scene in scenes:
        purpose = scene.get("purpose", "story_beat")
        narration = scene.get("narration", "")
        length_sec = float(scene.get("length_sec", 0) or 0)
        target = target_wpm(purpose, base_wpm)
        actual = _actual_wpm(narration, length_sec)
        if actual:
            deviations.append(abs(actual - target))
        segments.append(
            {
                "scene_number": scene.get("scene_number", 0),
                "purpose": purpose,
                "narration": narration,
                "delivery": PURPOSE_DELIVERY.get(purpose, DEFAULT_DELIVERY)["delivery"],
                "target_wpm": target,
                "actual_wpm": actual,
                "pace": pace_label(purpose),
                "pauses": plan_pauses(narration, purpose),
                "emphasis": pick_emphasis(narration),
            }
        )

    average_deviation = round(sum(deviations) / len(deviations), 1) if deviations else 0.0
    if average_deviation <= WPM_TOLERANCE:
        verdict = "on target — the script fits its scene timings at this voice pace"
    else:
        verdict = "drifting — tighten narration or scene lengths where actual wpm strays from target"
    fitness = clamp(95 - max(0.0, average_deviation - WPM_TOLERANCE) * 0.8, low=10, high=95)

    total_words = sum(len(segment["narration"].split()) for segment in segments)
    return {
        "voice_persona": voice_style.get("persona", ""),
        "base_wpm": base_wpm,
        "total_words": total_words,
        "segments": segments,
        "average_wpm_deviation": average_deviation,
        "pacing_verdict": verdict,
        "pacing_fitness": fitness,
    }
