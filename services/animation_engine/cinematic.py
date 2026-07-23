"""Cinematic storytelling intent — V2 quality layer (planning, not a renderer).

Before every scene is planned, answer:
  What should the audience understand?
  What emotion should they feel?
  What visual moment best communicates that?
  Would a muted viewer still get the idea?
"""

from __future__ import annotations

from typing import Any

from services.animation_engine.intent import narration_text
from services.animation_engine.models import (
    EMOTIONS,
    LIGHTING_MOODS,
    REJECT_VISUALS,
    SHOT_SIZES,
)


def _purpose(scene: dict[str, Any]) -> str:
    return str(scene.get("purpose") or scene.get("segment_type") or "story_beat").lower()


def detect_emotion(scene: dict[str, Any]) -> str:
    purpose = _purpose(scene)
    text = narration_text(scene).lower()
    if purpose == "hook" or any(w in text for w in ("wait", "secret", "danger", "shock", "could")):
        return "curiosity"
    if purpose == "payoff" or any(w in text for w in ("therefore", "so", "matters", "remember", "truth")):
        return "clarity"
    if any(w in text for w in ("fear", "threat", "danger", "deadly", "crisis")):
        return "tension"
    if any(w in text for w in ("wonder", "beautiful", "vast", "ancient", "legend", "myth")):
        return "awe"
    if any(w in text for w in ("warm", "home", "family", "save", "together")):
        return "warmth"
    if any(w in text for w in ("sad", "lost", "gone", "extinct", "ruin")):
        return "melancholy"
    if purpose in {"pattern_interrupt", "curiosity_loop"}:
        return "curiosity"
    return "focus" if "focus" in EMOTIONS else EMOTIONS[0]


def detect_lighting_mood(scene: dict[str, Any], *, world_env: str = "generic", emotion: str = "focus") -> str:
    text = narration_text(scene).lower()
    if any(w in text for w in ("night", "moon", "dark", "shadow")):
        return "moonlight"
    if any(w in text for w in ("storm", "thunder", "rain", "lightning")):
        return "storm"
    if any(w in text for w in ("fire", "ember", "torch", "campfire", "flame")):
        return "firelight"
    if any(w in text for w in ("dawn", "sunrise", "sunset", "golden")) or emotion == "warmth":
        return "golden_hour"
    if emotion in {"awe", "curiosity"} and world_env in {"countryside", "forest", "ocean"}:
        return "volumetric_sunlight"
    if emotion == "tension":
        return "cinematic_contrast"
    if world_env == "laboratory":
        return "practical_interior"
    if world_env == "space":
        return "moonlight"
    return "soft_daylight" if "soft_daylight" in LIGHTING_MOODS else LIGHTING_MOODS[0]


def choose_shot_size(scene: dict[str, Any], *, emotion: str) -> str:
    purpose = _purpose(scene)
    text = narration_text(scene).lower()
    if purpose == "hook":
        return "intimate_close_up" if emotion == "curiosity" else "dynamic_medium"
    if purpose == "payoff":
        return "hero_low_angle" if emotion in {"clarity", "awe"} else "intimate_close_up"
    if any(w in text for w in ("wide", "landscape", "world", "across", "map", "street", "skyline")):
        return "establishing_wide"
    if any(w in text for w in ("detail", "look", "notice", "label", "read", "close")):
        return "intimate_close_up"
    if emotion == "tension":
        return "high_angle_vulnerable"
    if emotion == "awe":
        return "establishing_wide"
    return "dynamic_medium" if "dynamic_medium" in SHOT_SIZES else SHOT_SIZES[0]


def audience_understanding(scene: dict[str, Any]) -> str:
    subject = str(
        scene.get("subject")
        or scene.get("viewer_understanding")
        or scene.get("concept")
        or "the core idea"
    ).strip()
    purpose = _purpose(scene)
    narr = narration_text(scene)
    if narr:
        # Keep short — planning cue for directors / true_motion titles
        gist = " ".join(narr.split()[:14])
        return f"Audience should understand: {gist} (subject={subject}, purpose={purpose})"
    return f"Audience should visually grasp {subject} for purpose={purpose}"


def visual_moment(scene: dict[str, Any], *, emotion: str, shot_size: str) -> str:
    """What should appear on screen — story demonstration, not decoration."""
    text = narration_text(scene).lower()
    subject = str(scene.get("subject") or "the subject").strip()
    if any(w in text for w in ("gold", "treasure", "coin")):
        return f"Demonstrate hidden treasure interacting with {subject} — not a floating icon"
    if any(w in text for w in ("color", "label", "means", "indicates")):
        return f"Show meaning through labeled {subject} with motivated callout, not abstract shapes"
    if any(w in text for w in ("walk", "run", "move", "journey")):
        return f"Character performs locomotion through the living world ({shot_size})"
    if emotion == "awe":
        return f"Scale reveal of the world around {subject} ({shot_size})"
    if emotion == "tension":
        return f"Compress space around {subject} — motivated camera pressure"
    return f"Advance story by showing {subject} in action ({emotion}/{shot_size})"


def immersion_checklist(layers_preview: dict[str, Any] | None = None) -> dict[str, Any]:
    """Questions every render must answer. Failures identify re-render targets."""
    layers_preview = layers_preview or {}
    questions = {
        "world_feels_alive": bool((layers_preview.get("world") or {}).get("living_background")),
        "camera_has_purpose": bool((layers_preview.get("camera") or {}).get("narrative_purpose")),
        "environments_believable": bool((layers_preview.get("world") or {}).get("depth_layers")),
        "characters_feel_alive": bool(
            not (layers_preview.get("character") or {}).get("enabled")
            or (layers_preview.get("character") or {}).get("micro_performance")
        ),
        "visuals_engaging_muted": bool(layers_preview.get("muted_comprehension")),
        "every_frame_advances_story": bool(layers_preview.get("visual_moment")),
        "rejects_abstract_geometry": not bool((layers_preview.get("world") or {}).get("allow_abstract_geometry")),
    }
    failing = [k for k, ok in questions.items() if not ok]
    return {
        "questions": questions,
        "passed": not failing,
        "failing": failing,
        "re_render_required": bool(failing),
    }


def plan_cinematic_intent(
    scene: dict[str, Any],
    *,
    world_env: str = "generic",
    topic: str = "",
) -> dict[str, Any]:
    emotion = detect_emotion(scene)
    lighting = detect_lighting_mood(scene, world_env=world_env, emotion=emotion)
    shot = choose_shot_size(scene, emotion=emotion)
    understanding = audience_understanding(scene)
    moment = visual_moment(scene, emotion=emotion, shot_size=shot)
    return {
        "version": "2.0",
        "emotion": emotion,
        "lighting_mood": lighting,
        "shot_size": shot,
        "audience_understanding": understanding,
        "visual_moment": moment,
        "color_intent": {
            "harmony": "natural",
            "hierarchy": "subject_isolation",
            "avoid": ["oversaturated_randomness", "neon_scatter"],
        },
        "forbid": list(REJECT_VISUALS)[:12],
        "topic_hint": topic[:80],
    }
