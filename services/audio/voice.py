"""Voice style selection — who is speaking and how.

Every niche maps to a narrator persona (tone, pitch, character), modulated
by the idea's emotional arc and the platform's narration tone. Styles are
data, not code — retuning a niche's voice (or adding one) is an edit to
`NICHE_VOICE_STYLES`, never to the selector.
"""

from __future__ import annotations

# Narrator persona per niche — the audio identity that matches the niche's
# visual palette in services/visual/scenes.py.
NICHE_VOICE_STYLES = {
    "Science": {
        "persona": "clear-eyed documentary explainer",
        "tone": "curious and precise",
        "pitch": "medium",
        "character": "the brilliant friend who makes complex things feel simple",
    },
    "Psychology": {
        "persona": "warm late-night confidant",
        "tone": "intimate and knowing",
        "pitch": "low-medium",
        "character": "someone who has read your mind and is gently telling you about it",
    },
    "Finance": {
        "persona": "composed market insider",
        "tone": "confident and matter-of-fact",
        "pitch": "medium-low",
        "character": "the advisor who never oversells but is always right",
    },
    "Space": {
        "persona": "awe-struck cosmic narrator",
        "tone": "reverent and expansive",
        "pitch": "low",
        "character": "a guide standing at the edge of something enormous",
    },
    "Dark History": {
        "persona": "measured candlelit storyteller",
        "tone": "grave and deliberate",
        "pitch": "low",
        "character": "the keeper of stories people tried to bury",
    },
    "Health": {
        "persona": "encouraging evidence-based coach",
        "tone": "bright and reassuring",
        "pitch": "medium",
        "character": "the trainer who explains why before asking you to change",
    },
    "AI & Future Tech": {
        "persona": "fast-forward futurist",
        "tone": "electric and assured",
        "pitch": "medium-high",
        "character": "someone reporting live from five years ahead",
    },
}

DEFAULT_VOICE_STYLE = {
    "persona": "engaging short-form narrator",
    "tone": "energetic and conversational",
    "pitch": "medium",
    "character": "a sharp friend who gets to the point",
}

# Vocal energy from the storyboard's average motion intensity — a kinetic
# edit needs a kinetic read; a contemplative one needs restraint.
ENERGY_LEVELS = ((70, "high"), (45, "medium"), (0, "low"))


def _energy_level(average_motion: float) -> str:
    for threshold, label in ENERGY_LEVELS:
        if average_motion >= threshold:
            return label
    return ENERGY_LEVELS[-1][1]


def select_voice_style(
    scenes: list,
    *,
    niche: str = "",
    platform_tone: str = "",
) -> dict:
    """Pick the narrator voice style for one idea's storyboard (JSON-safe dict)."""
    style = dict(NICHE_VOICE_STYLES.get(niche, DEFAULT_VOICE_STYLE))

    intensities = [scene.get("motion_intensity", 50) for scene in scenes] or [50]
    average_motion = sum(intensities) / len(intensities)
    style["energy"] = _energy_level(average_motion)

    emotions = [scene.get("emotion", "") for scene in scenes if scene.get("emotion")]
    arc = f"{emotions[0]} → {emotions[-1]}" if emotions else "curiosity → resolve"

    notes = [
        f"Emotional arc travels {arc} — let certainty build in the voice as the story resolves.",
        f"Keep overall energy {style['energy']} to match the edit's motion.",
    ]
    if platform_tone:
        notes.append(f"Platform tone: {platform_tone}.")
    style["delivery_notes"] = notes
    style["emotional_arc"] = arc
    return style
