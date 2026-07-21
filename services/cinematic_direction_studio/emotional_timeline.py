"""Emotional timeline — audience arc across the episode / scene."""

from __future__ import annotations

from typing import Any

from services.cinematic_direction_studio.models import EMOTIONAL_ARC


def infer_scene_emotion(
    *,
    scene_index: int,
    total: int,
    purpose: str,
    narration: str,
    prior_emotion: str | None = None,
) -> str:
    purpose = str(purpose or "").lower()
    text = (narration or "").lower()
    if scene_index == 0 or purpose == "hook":
        return "curiosity"
    if purpose == "payoff" or scene_index >= max(0, total - 1):
        return "resolution"
    if any(w in text for w in ("wonder", "amazing", "beautiful", "vast")):
        return "wonder"
    if any(w in text for w in ("think", "pause", "means", "consider")):
        return "reflection"
    if any(w in text for w in ("can", "create", "choice", "together", "hope")):
        return "inspiration"
    if any(w in text for w in ("because", "how", "explain", "simple", "learn")):
        return "understanding"
    # Progress along arc
    return EMOTIONAL_ARC[min(scene_index, len(EMOTIONAL_ARC) - 1)]


def build_emotional_timeline(scene_plans: list[dict[str, Any]]) -> dict[str, Any]:
    beats = []
    for i, plan in enumerate(scene_plans):
        emotion = str(
            plan.get("emotional_objective")
            or (plan.get("camera_language") or {}).get("emotion")
            or EMOTIONAL_ARC[min(i, len(EMOTIONAL_ARC) - 1)]
        )
        beats.append(
            {
                "scene_number": plan.get("scene_number") or i + 1,
                "audience_emotion": emotion,
                "shot_type": plan.get("shot_type"),
                "arc_position": emotion if emotion in EMOTIONAL_ARC else "curiosity",
            }
        )
    # Ensure full arc coverage when enough scenes
    covered = {b["audience_emotion"] for b in beats}
    return {
        "beats": beats,
        "required_arc": list(EMOTIONAL_ARC),
        "covered": sorted(covered),
        "has_arc": len(covered) >= min(3, len(beats)),
        "philosophy": "Every scene should have an emotional arc for the audience.",
    }
