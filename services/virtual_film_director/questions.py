"""Director's questions — a scene is not ready until every answer is clear."""

from __future__ import annotations

from typing import Any

from services.animation_engine.intent import narration_text
from services.virtual_film_director.models import DIRECTOR_QUESTIONS


def _purpose(scene: dict[str, Any]) -> str:
    return str(scene.get("purpose") or scene.get("segment_type") or "story_beat").lower()


def answer_director_questions(
    scene: dict[str, Any],
    *,
    topic: str = "",
    emotion: str = "focus",
    shot_language: str = "medium_dialogue",
    primary_subject: str = "",
) -> dict[str, Any]:
    narr = narration_text(scene)
    purpose = _purpose(scene)
    subject = primary_subject or str(scene.get("subject") or topic or "the idea").strip()
    gist = " ".join(narr.split()[:16]) if narr else subject

    answers = {
        "why_scene_exists": (
            f"Advance {purpose}: establish audience investment in {subject}"
            if purpose == "hook"
            else (
                f"Deliver the takeaway on {subject}"
                if purpose == "payoff"
                else f"Demonstrate the idea so learning sticks: {gist or subject}"
            )
        ),
        "what_viewer_learns": gist or f"Visual comprehension of {subject}",
        "emotion_to_feel": emotion,
        "notice_first": f"Primary subject first — {subject} — then supporting world",
        "what_should_move": (
            "Camera + living environment + character performance when present; "
            "object physics when narration discusses a mechanism"
        ),
        "what_should_remain_still": (
            "Composition anchors (horizon / practical light sources) — never freeze the whole world"
        ),
        "camera_begin": f"Open in a framed read of {subject} matching {shot_language}",
        "camera_end": f"Land on the beat's cinematic payoff for emotion={emotion}",
        "cinematic_payoff": (
            f"Muted viewer still understands: {gist or subject}"
        ),
    }
    unclear = [q for q in DIRECTOR_QUESTIONS if not str(answers.get(q) or "").strip()]
    return {
        "answers": answers,
        "ready": not unclear,
        "unclear": unclear,
        "scene_ready": not unclear,
    }
