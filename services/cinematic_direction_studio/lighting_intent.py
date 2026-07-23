"""Lighting intent — emotional light direction."""

from __future__ import annotations

from typing import Any

from services.cinematic_direction_studio.models import LIGHTING_INTENTS, LIGHTING_TO_MOOD


def plan_lighting_intent(
    *,
    emotion: str,
    location_hint: str = "",
    vfd_mood: str | None = None,
) -> dict[str, Any]:
    emotion = str(emotion or "curiosity").lower()
    loc = str(location_hint or "").lower()

    intent = "scientific"
    if emotion in {"hope", "inspiration", "joy"}:
        intent = "hopeful"
    elif emotion in {"comfort", "understanding"}:
        intent = "comforting"
    elif emotion in {"wonder", "reflection"}:
        intent = "warm"
    elif emotion in {"mystery", "awe"} and "night" in loc:
        intent = "mysterious"
    elif emotion in {"urgency", "tension"}:
        intent = "urgent"
    elif "lab" in loc or "hospital" in loc or "medical" in loc:
        intent = "scientific"
    elif emotion == "curiosity":
        intent = "warm"

    if intent not in LIGHTING_INTENTS:
        intent = "warm"

    mood = vfd_mood or LIGHTING_TO_MOOD.get(intent, "soft_daylight")
    return {
        "intent": intent,
        "lighting_mood": mood,
        "emotion": emotion,
        "motivated": True,
        "purpose": f"{intent} light supports {emotion}",
        "forbid_unmotivated_grade": True,
    }
