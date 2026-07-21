"""Per-scene intentional planning — what to understand, what visual fits."""

from __future__ import annotations

from typing import Any

from services.visual_source_intelligence.models import DIAGRAM_HINTS, MOTION_HINTS


def scene_narration(scene: dict[str, Any]) -> str:
    return str(
        scene.get("narration")
        or scene.get("voiceover")
        or scene.get("script")
        or scene.get("text")
        or ""
    ).strip()


def scene_purpose(scene: dict[str, Any]) -> str:
    return str(scene.get("purpose") or scene.get("segment_type") or "story_beat").lower()


def viewer_understanding(scene: dict[str, Any], *, topic: str = "") -> str:
    """1. What is the viewer supposed to understand?"""
    purpose = scene_purpose(scene)
    narration = scene_narration(scene)
    subject = str(scene.get("subject") or scene.get("visual_description") or topic or "the subject")
    if purpose == "hook":
        return f"Something surprising about {subject} that earns the next few seconds of attention."
    if purpose in {"payoff", "cta"}:
        return f"The clear takeaway about {subject}."
    if narration:
        # First clause as the beat-level lesson
        for sep in (". ", "? ", "! ", " — "):
            if sep in narration:
                return narration.split(sep, 1)[0].strip() + sep.strip()
        return narration[:160]
    return f"One concrete idea about {subject}."


def ideal_visual(scene: dict[str, Any], *, topic: str = "") -> str:
    """2. What visual best communicates that idea?"""
    purpose = scene_purpose(scene)
    narration = scene_narration(scene).lower()
    description = str(scene.get("visual_description") or "")
    if purpose == "hook":
        return (
            "High-motion establishing or close trio of contrasting subjects filling the frame "
            "in the first seconds — not a title card."
        )
    if any(h in narration for h in DIAGRAM_HINTS):
        return (
            "Animated diagram or labeled close-up with callouts that map narration keywords "
            "to visible elements."
        )
    if any(h in narration for h in MOTION_HINTS):
        return "Live-action or AI video with motivated subject/camera motion matching the verb in narration."
    if description:
        return description
    return f"Cinematic documentary coverage of {topic or 'the subject'} that visually proves the narration beat."


def prefers_diagram(scene: dict[str, Any]) -> bool:
    text = f"{scene_narration(scene)} {scene.get('visual_description') or ''}".lower()
    purpose = scene_purpose(scene)
    return any(h in text for h in DIAGRAM_HINTS) or purpose in {"understanding", "evidence"}


def prefers_motion(scene: dict[str, Any]) -> bool:
    purpose = scene_purpose(scene)
    text = scene_narration(scene).lower()
    if purpose in {"hook", "pattern_interrupt", "payoff"}:
        return True
    return any(h in text for h in MOTION_HINTS)


def build_scene_intent(scene: dict[str, Any], *, topic: str = "") -> dict[str, Any]:
    return {
        "viewer_understanding": viewer_understanding(scene, topic=topic),
        "ideal_visual": ideal_visual(scene, topic=topic),
        "prefers_diagram": prefers_diagram(scene),
        "prefers_motion": prefers_motion(scene),
        "purpose": scene_purpose(scene),
        "narration": scene_narration(scene),
    }
