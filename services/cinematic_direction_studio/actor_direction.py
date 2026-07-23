"""Actor direction — intentional performance beats, not mechanical motion."""

from __future__ import annotations

from typing import Any


def plan_actor_direction(
    *,
    character_id: str,
    narration: str,
    emotion: str,
    duration_sec: float,
    scene_index: int = 0,
    cpe: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Direct a readable performance sequence (walk → pause → address → explain)."""
    cid = str(character_id or "DOCTOR_001").upper()
    emotion = str(emotion or "curiosity").lower()
    dur = max(float(duration_sec or 3.0), 1.5)
    text = (narration or "").lower()

    # Choose business from narration / CPE
    if any(k in text for k in ("microscope", "look", "examine", "inspect")):
        beats = _microscope_teach(dur, emotion)
        objective = "Approach instrument, pause with intent, then teach to camera"
    elif any(k in text for k in ("walk", "come", "through", "lab")):
        beats = _walk_and_talk(dur, emotion)
        objective = "Walk-and-talk with purposeful stops and eye contact"
    elif any(k in text for k in ("door", "enter", "leave")):
        beats = _door_enter(dur, emotion)
        objective = "Enter space, orient, then address audience"
    else:
        beats = _teach_present(dur, emotion)
        objective = "Grounded teaching performance with breath and gesture"

    # Soft-merge CPE interaction verbs as business
    if cpe:
        for ev in (cpe.get("interactions") or {}).get("events") or []:
            beats.append(
                {
                    "t": float(ev.get("t") or dur * 0.5),
                    "action": str(ev.get("verb") or "gesture"),
                    "note": f"Interact with {ev.get('target') or 'prop'}",
                    "motivated": True,
                }
            )
        beats.sort(key=lambda b: float(b.get("t") or 0))

    return {
        "character_id": cid,
        "objective": objective,
        "emotion": emotion,
        "beats": beats,
        "forbid_mechanical_loop": True,
        "require_breath_and_pause": True,
        "require_eye_intent": True,
        "scene_index": scene_index,
        "example_philosophy": (
            "Doctor walks to microscope. Stops. Looks down. Pauses. Breathes. "
            "Turns toward viewer. Smiles. Explains. Returns to work."
        ),
    }


def _microscope_teach(dur: float, emotion: str) -> list[dict[str, Any]]:
    return [
        {"t": 0.0, "action": "walk_to_microscope", "note": "Purposeful approach", "motivated": True},
        {"t": dur * 0.22, "action": "stop", "note": "Plant feet", "motivated": True},
        {"t": dur * 0.28, "action": "look_down", "note": "Inspect eyepiece", "motivated": True},
        {"t": dur * 0.38, "action": "pause", "note": "Let beat land", "motivated": True},
        {"t": dur * 0.45, "action": "breathe", "note": "Human settle", "motivated": True},
        {"t": dur * 0.55, "action": "turn_to_viewer", "note": "Camera address", "motivated": True},
        {"t": dur * 0.62, "action": "smile" if emotion in {"hope", "joy", "inspiration"} else "warm_focus", "note": "Readable face", "motivated": True},
        {"t": dur * 0.70, "action": "explain", "note": "Gesture + speech", "motivated": True},
        {"t": dur * 0.90, "action": "return_to_work", "note": "Back to instrument", "motivated": True},
    ]


def _walk_and_talk(dur: float, emotion: str) -> list[dict[str, Any]]:
    return [
        {"t": 0.0, "action": "walk", "note": "Start in motion", "motivated": True},
        {"t": dur * 0.25, "action": "glance_environment", "note": "World awareness", "motivated": True},
        {"t": dur * 0.40, "action": "pause_weight_shift", "note": "Thought beat", "motivated": True},
        {"t": dur * 0.50, "action": "turn_to_viewer", "note": "Share idea", "motivated": True},
        {"t": dur * 0.60, "action": "gesture_explain", "note": "Teaching hands", "motivated": True},
        {"t": dur * 0.85, "action": "continue_walk", "note": "Momentum resumes", "motivated": True},
    ]


def _door_enter(dur: float, emotion: str) -> list[dict[str, Any]]:
    return [
        {"t": 0.0, "action": "open_door", "note": "Enter world", "motivated": True},
        {"t": dur * 0.25, "action": "step_in", "note": "Cross threshold", "motivated": True},
        {"t": dur * 0.40, "action": "orient", "note": "Read the room", "motivated": True},
        {"t": dur * 0.55, "action": "turn_to_viewer", "note": "Invite audience", "motivated": True},
        {"t": dur * 0.70, "action": "explain", "note": "Begin teaching", "motivated": True},
    ]


def _teach_present(dur: float, emotion: str) -> list[dict[str, Any]]:
    return [
        {"t": 0.0, "action": "plant_and_presence", "note": "Arrive in frame", "motivated": True},
        {"t": dur * 0.20, "action": "breathe", "note": "Settle", "motivated": True},
        {"t": dur * 0.35, "action": "gesture_prepare", "note": "Thought becomes motion", "motivated": True},
        {"t": dur * 0.50, "action": "explain", "note": "Core teaching", "motivated": True},
        {"t": dur * 0.75, "action": "point_or_indicate", "note": "Evidence beat", "motivated": True},
        {"t": dur * 0.90, "action": "soft_smile_or_resolve", "note": "Emotional close", "motivated": True},
    ]
