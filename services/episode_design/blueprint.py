"""LessonBlueprint builder — maps a content item onto the canonical beat structure.

The blueprint answers exactly *how* each timing beat should be executed for
this specific topic/script, giving production teams a per-beat content guide,
viewer question to hold, reveal moments, and pause points.
"""

from __future__ import annotations

from services.episode_design.models import BLUEPRINT_BEATS


def _extract_script(item: dict) -> str:
    """Pull script text from the item, checking multiple slots."""
    script_pkg = item.get("script_package") or {}
    return (
        str(item.get("script") or "")
        or str(script_pkg.get("script") or "")
        or str(script_pkg.get("script_text") or "")
    )


def _extract_hook(item: dict) -> str:
    return str(item.get("hook") or "")


def _extract_topic(item: dict) -> str:
    return str(item.get("topic") or item.get("title") or "")


def _extract_niche(item: dict) -> str:
    return str(item.get("niche") or "general")


def _beat_content_guidance(beat: dict, topic: str, hook: str, script: str) -> dict:
    """Generate per-beat content guidance specific to this item."""
    name = beat["beat"]
    label = beat["label"]
    duration = beat["duration_sec"]
    purpose = beat["purpose"]

    guidance: dict[str, object] = {
        "beat": name,
        "label": label,
        "start_sec": beat["start_sec"],
        "duration_sec": duration,
        "purpose": purpose,
        "viewer_question": beat["viewer_question"],
        "is_reveal": beat["reveal"],
        "is_pause_point": beat["pause_point"],
        "content_guidance": "",
        "production_note": "",
    }

    if name == "curiosity_hook":
        opening = hook or (script[:80] if script else "")
        guidance["content_guidance"] = (
            f"Open with the most arresting element of '{topic}'. "
            f"In {duration}s establish a visual or audio hook that creates "
            "immediate 'I have to know more' tension. "
            f"Suggested anchor: {opening!r}" if opening else
            f"Open with the most arresting element of '{topic}'. "
            f"In {duration}s establish a visual or audio hook."
        )
        guidance["production_note"] = (
            "No title card, no intro music — open on the hook itself. "
            "The first frame must be visually surprising or emotionally provocative."
        )

    elif name == "interesting_question":
        guidance["content_guidance"] = (
            f"State the surprising question that '{topic}' answers. "
            "Frame it counterintuitively — challenge what the viewer thinks they know. "
            f"Must fit in {duration}s (≈ 1-2 sentences)."
        )
        guidance["production_note"] = (
            "Use rising intonation. Display the question as text on screen. "
            "Viewer must feel the gap between what they know and what the answer might be."
        )

    elif name == "demonstration":
        guidance["content_guidance"] = (
            f"Show '{topic}' in action before explaining it. "
            "Visual proof: an experiment, animation, real-world clip, or diagram. "
            f"In {duration}s let the viewer see the phenomenon — no narration required yet."
        )
        guidance["production_note"] = (
            "Visual-first. Narration should be minimal or silent here. "
            "The best demonstrations create a second 'why does that happen?' moment."
        )

    elif name == "explanation":
        guidance["content_guidance"] = (
            f"Layer the explanation of '{topic}' from simple to complex. "
            f"In {duration}s build: (1) the simple model, (2) why it works, "
            "(3) the deeper mechanism. Avoid jargon; use analogies."
        )
        guidance["production_note"] = (
            "Pause naturally after each layer — give viewers a beat to absorb. "
            "This is where animation, diagrams, and text overlays pay off most. "
            "The biggest reveal should land in the final third of this beat."
        )

    elif name == "real_world_application":
        guidance["content_guidance"] = (
            f"Connect '{topic}' to something in the viewer's everyday life. "
            f"In {duration}s: one concrete example they have personally experienced "
            "or will encounter. Make the abstract tangible."
        )
        guidance["production_note"] = (
            "Use second-person language ('You've probably noticed…'). "
            "Real-world footage or relatable scenarios work better than further animation."
        )

    elif name == "powerful_takeaway":
        guidance["content_guidance"] = (
            f"Distil '{topic}' into ONE memorable, shareable insight. "
            f"In {duration}s: the single sentence the viewer will repeat to a friend. "
            "Aim for emotional resonance, not information density."
        )
        guidance["production_note"] = (
            "Slow the pace here. Display the takeaway as large text on screen. "
            "This is the emotional peak — music swell, pause after delivery."
        )

    elif name == "bridge_to_next":
        guidance["content_guidance"] = (
            f"Tease the next episode in this series or the next piece of curiosity "
            f"about '{topic}'. In {duration}s: open a new question without answering it. "
            "Make the viewer feel they must watch the next episode."
        )
        guidance["production_note"] = (
            "End on a question, not a statement. "
            "A brief visual teaser of the next topic is highly effective. "
            "Subscribe/follow CTA may live here if platform requires it."
        )

    return guidance


def build_lesson_blueprint(item: dict, context: dict | None = None) -> dict:
    """Full LessonBlueprint for one content item.

    Returns a dict with all seven timing beats populated with topic-specific
    content guidance, viewer questions, reveal moments, and pause points.
    """
    context = context or {}
    topic = _extract_topic(item)
    hook = _extract_hook(item)
    script = _extract_script(item)
    niche = _extract_niche(item)

    beats = [
        _beat_content_guidance(beat, topic, hook, script)
        for beat in BLUEPRINT_BEATS
    ]

    total_sec = sum(b["duration_sec"] for b in BLUEPRINT_BEATS)
    reveal_beats = [b["beat"] for b in beats if b["is_reveal"]]
    pause_beats = [b["beat"] for b in beats if b["is_pause_point"]]

    return {
        "topic": topic,
        "niche": niche,
        "total_duration_sec": total_sec,
        "beats": beats,
        "reveal_moments": reveal_beats,
        "pause_points": pause_beats,
        "script_words": len(script.split()) if script else 0,
        "has_hook": bool(hook),
        "has_script": bool(script),
    }
