"""Motivational story structure — Hook through Memorable Ending."""

from __future__ import annotations

from engines.heuristics import clamp

REQUIRED_STORY_BEATS = (
    "hook",
    "struggle",
    "real_life_example",
    "lesson",
    "application",
    "memorable_ending",
)

STORY_BEAT_LABELS = {
    "hook": "Hook",
    "struggle": "The Struggle",
    "real_life_example": "Real-Life Example",
    "lesson": "Lesson",
    "application": "Application",
    "memorable_ending": "Memorable Ending",
}

# Signals that a beat is concrete enough to count (not empty slogans).
_APPLICATION_WORDS = (
    "today",
    "this week",
    "start",
    "do this",
    "try",
    "practice",
    "write down",
    "take one",
    "first step",
    "apply",
)
_STRUGGLE_WORDS = (
    "struggle",
    "hard",
    "fail",
    "fear",
    "stuck",
    "tired",
    "doubt",
    "pain",
    "quit",
    "broken",
    "alone",
)
_EXAMPLE_WORDS = (
    "history",
    "scientist",
    "athlete",
    "soldier",
    "explorer",
    "inventor",
    "leader",
    "study",
    "research",
    "documented",
    "once",
    "example",
)


def empty_story_beats() -> dict:
    return {beat: "" for beat in REQUIRED_STORY_BEATS}


def beats_complete(story_beats: dict | None) -> bool:
    if not story_beats:
        return False
    return all(str(story_beats.get(beat, "")).strip() for beat in REQUIRED_STORY_BEATS)


def score_story_structure(story_beats: dict | None, full_script: str = "") -> dict:
    """Score beat completeness and usefulness (0-100) with a short note."""
    beats = story_beats or {}
    script_lower = (full_script or "").lower()
    filled = sum(1 for beat in REQUIRED_STORY_BEATS if str(beats.get(beat, "")).strip())
    score = 20 + filled * 12  # 6 beats → 92 before bonuses

    struggle = f"{beats.get('struggle', '')} {script_lower}".lower()
    application = f"{beats.get('application', '')} {script_lower}".lower()
    example = f"{beats.get('real_life_example', '')} {script_lower}".lower()

    if any(word in struggle for word in _STRUGGLE_WORDS):
        score += 4
    if any(word in application for word in _APPLICATION_WORDS):
        score += 6
    if any(word in example for word in _EXAMPLE_WORDS):
        score += 4

    score = clamp(score)
    missing = [beat for beat in REQUIRED_STORY_BEATS if not str(beats.get(beat, "")).strip()]
    note = (
        "Complete Hook → Struggle → Example → Lesson → Application → Ending arc."
        if not missing
        else f"Missing beats: {', '.join(STORY_BEAT_LABELS[b] for b in missing)}."
    )
    return {
        "score": score,
        "complete": not missing,
        "missing_beats": missing,
        "note": note,
    }
