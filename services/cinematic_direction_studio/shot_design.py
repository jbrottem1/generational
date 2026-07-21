"""Shot design — choose intentional framing per beat."""

from __future__ import annotations

from typing import Any

from services.cinematic_direction_studio.models import SHOT_TYPES


def choose_shot_type(
    *,
    scene_index: int,
    total: int,
    purpose: str,
    emotion: str,
    used: set[str],
    vfd_language: str | None = None,
) -> str:
    purpose = str(purpose or "story_beat").lower()
    emotion = str(emotion or "curiosity").lower()

    # Honor VFD when present by mapping language → studio shot type
    if vfd_language:
        mapped = _map_vfd(vfd_language)
        if mapped and mapped not in used:
            return mapped

    preferred: list[str] = []
    if scene_index == 0 or purpose == "hook":
        preferred = ["establishing", "wide", "orbit"]
    elif purpose == "payoff" or scene_index >= max(0, total - 1):
        preferred = ["close_up", "reaction", "medium"]
    elif emotion in {"wonder", "awe", "discovery"}:
        preferred = ["orbit", "wide", "tracking"]
    elif emotion in {"teaching", "scientific", "understanding"}:
        preferred = ["tracking", "medium", "over_the_shoulder"]
    elif emotion in {"reflection", "inspiration"}:
        preferred = ["medium", "close_up", "follow"]
    elif "detail" in purpose or emotion == "curiosity":
        preferred = ["insert", "extreme_close_up", "close_up"]
    else:
        preferred = ["medium", "tracking", "over_the_shoulder", "reaction"]

    for shot in preferred:
        if shot not in used and shot in SHOT_TYPES:
            return shot
    for shot in SHOT_TYPES:
        if shot not in used:
            return shot
    return preferred[0]


def _map_vfd(language: str) -> str | None:
    lang = str(language or "").lower()
    mapping = {
        "epic_establishing": "establishing",
        "wide_landscape": "wide",
        "drone_shot": "wide",
        "crane_shot": "wide",
        "medium_dialogue": "medium",
        "close_up": "close_up",
        "extreme_close_up": "extreme_close_up",
        "tracking_shot": "tracking",
        "action_follow": "follow",
        "orbit_shot": "orbit",
        "over_the_shoulder": "over_the_shoulder",
        "pov": "pov",
        "reveal_shot": "orbit",
        "push_in": "close_up",
        "hero_shot": "medium",
        "parallax": "orbit",
        "rack_focus": "extreme_close_up",
    }
    return mapping.get(lang)


def shot_purpose(shot_type: str, emotion: str, narration: str) -> str:
    chunk = (narration or "").split(".")[0].strip()
    if len(chunk) > 90:
        chunk = chunk[:87] + "..."
    return (
        f"{shot_type.replace('_', ' ')} serves {emotion}: "
        f"{chunk or 'advance story and educational clarity'}"
    )
