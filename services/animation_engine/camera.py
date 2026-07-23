"""Camera Director V2 — motivated cinematography (emotion + story first).

Every move must carry narrative_purpose. Purposeless drift is rejected.
"""

from __future__ import annotations

from typing import Any

from services.animation_engine.intent import narration_text
from services.animation_engine.models import (
    CAMERA_MOVES,
    CAMERA_TO_MOTION_EFFECT,
    CAMERA_TO_TRUE_MOTION,
    PREFERRED_TRANSITIONS,
)


def _purpose(scene: dict[str, Any]) -> str:
    return str(scene.get("purpose") or scene.get("segment_type") or "story_beat").lower()


def choose_camera(
    scene: dict[str, Any],
    *,
    scene_index: int = 0,
    used: set[str] | None = None,
    cinematic: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Pick a camera move that reinforces emotion and understanding — never random lock-off."""
    used = used or set()
    cinematic = cinematic or {}
    purpose = _purpose(scene)
    text = narration_text(scene).lower()
    emotion = str(cinematic.get("emotion") or scene.get("director_emotion") or scene.get("emotion") or "focus")
    shot = str(cinematic.get("shot_size") or scene.get("shot_size") or "dynamic_medium")

    # Honor Virtual Film Director seed when present
    vfd_seed = scene.get("vfd_seed") if isinstance(scene.get("vfd_seed"), dict) else {}
    vfd_move = str(scene.get("vfd_camera_move") or vfd_seed.get("ae_camera_move") or "")
    if vfd_move and vfd_move not in used:
        pick = vfd_move
        narrative_purpose = str(
            scene.get("camera_narrative_purpose")
            or vfd_seed.get("narrative_purpose")
            or scene.get("scene_objective")
            or f"Execute VFD shot `{scene.get('shot_language') or pick}` for {emotion}"
        )
        speed = {
            "curiosity": "energized",
            "tension": "pressing",
            "awe": "glacial",
            "warmth": "gentle",
            "melancholy": "slow",
            "clarity": "resolved",
            "focus": "measured",
        }.get(emotion, "measured")
        return {
            "camera_move": pick,
            "motion_effect": CAMERA_TO_MOTION_EFFECT.get(pick, "cinematic_push_in"),
            "true_motion_camera": str(
                vfd_seed.get("true_motion_camera")
                or scene.get("animation_camera")
                or CAMERA_TO_TRUE_MOTION.get(pick, "push_in")
            ),
            "depth_of_field": pick in {"depth_of_field", "rack_focus", "slow_cinematic_push"}
            or shot == "intimate_close_up",
            "rack_focus": pick == "rack_focus",
            "shot_size": shot or vfd_seed.get("shot_size") or "dynamic_medium",
            "emotion": emotion,
            "speed": speed,
            "narrative_purpose": narrative_purpose,
            "storytelling_reason": narrative_purpose,
            "forbid_static_lock": True,
            "forbid_purposeless_drift": True,
            "motivated": True,
            "source": "virtual_film_director",
        }

    preferred: list[str] = []
    if shot == "hero_low_angle" or (emotion == "clarity" and purpose == "payoff"):
        preferred = ["hero_low_angle_push", "slow_cinematic_push", "dolly_forward", "reveal"]
    elif shot == "high_angle_vulnerable" or emotion == "tension":
        preferred = ["vulnerability_high_angle", "crane", "dolly_backward", "handheld_documentary"]
    elif shot == "establishing_wide" or emotion == "awe":
        preferred = ["crane", "reveal", "tracking", "parallax", "dolly_backward"]
    elif shot == "intimate_close_up":
        preferred = ["rack_focus", "depth_of_field", "slow_cinematic_push", "dolly_forward"]
    elif purpose == "hook":
        preferred = ["dynamic_zoom", "reveal", "slow_cinematic_push", "handheld_documentary"]
    elif purpose in {"pattern_interrupt", "curiosity_loop"} or emotion == "curiosity":
        preferred = ["orbit", "tracking", "handheld_documentary", "parallax", "reveal"]
    elif any(w in text for w in ("look", "notice", "detail", "close", "label", "color")):
        preferred = ["rack_focus", "depth_of_field", "slow_cinematic_push", "dolly_forward"]
    elif any(w in text for w in ("wide", "landscape", "street", "world", "across", "map")):
        preferred = ["crane", "reveal", "tracking", "dolly_backward"]
    elif purpose == "payoff":
        preferred = ["slow_cinematic_push", "dolly_forward", "hero_low_angle_push", "orbit"]
    else:
        preferred = [
            "slow_cinematic_push",
            "parallax",
            "tracking",
            "orbit",
            "dolly_forward",
            CAMERA_MOVES[scene_index % len(CAMERA_MOVES)],
        ]

    pick = next((m for m in preferred if m not in used), None)
    if pick is None:
        pick = next((m for m in CAMERA_MOVES if m not in used), CAMERA_MOVES[scene_index % len(CAMERA_MOVES)])

    narrative_purpose = {
        "hook": f"Interrupt pattern with motivated energy ({emotion})",
        "payoff": f"Land the takeaway with a decisive, emotionally settled move ({emotion})",
        "story_beat": f"Advance comprehension of the beat while holding {emotion}",
    }.get(purpose, f"Serve understanding + {emotion} — never decorative drift")

    speed = {
        "curiosity": "energized",
        "tension": "pressing",
        "awe": "glacial",
        "warmth": "gentle",
        "melancholy": "slow",
        "clarity": "resolved",
        "focus": "measured",
    }.get(emotion, "measured")

    return {
        "camera_move": pick,
        "motion_effect": CAMERA_TO_MOTION_EFFECT.get(pick, "cinematic_push_in"),
        "true_motion_camera": CAMERA_TO_TRUE_MOTION.get(pick, "push_in"),
        "depth_of_field": pick in {"depth_of_field", "rack_focus", "slow_cinematic_push", "intimate_close_up"}
        or shot == "intimate_close_up",
        "rack_focus": pick == "rack_focus",
        "shot_size": shot,
        "emotion": emotion,
        "speed": speed,
        "narrative_purpose": narrative_purpose,
        "storytelling_reason": narrative_purpose,
        "forbid_static_lock": True,
        "forbid_purposeless_drift": True,
        "motivated": True,
        "source": "animation_engine_v2",
    }


def choose_transition(
    prev: dict[str, Any] | None,
    nxt: dict[str, Any],
    *,
    index: int,
    prev_cinematic: dict[str, Any] | None = None,
    nxt_cinematic: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Motivated transitions — continuation when emotion/world aligns; never arbitrary fades."""
    purpose = _purpose(nxt)
    prev_cinematic = prev_cinematic or {}
    nxt_cinematic = nxt_cinematic or {}
    same_emotion = prev_cinematic.get("emotion") and prev_cinematic.get("emotion") == nxt_cinematic.get("emotion")
    same_light = prev_cinematic.get("lighting_mood") and prev_cinematic.get(
        "lighting_mood"
    ) == nxt_cinematic.get("lighting_mood")

    if purpose == "hook" or index == 0:
        move = "hard_cut"
        reason = "Clean entry — no decorative fade into the hook"
    elif purpose == "payoff":
        move = "zoom_transition"
        reason = "Resolve into the takeaway"
    elif same_emotion and same_light:
        move = "seamless_camera_continuation"
        reason = "Emotion and lighting continue — invisible cut via motion continuity"
    elif same_light:
        move = "light_transition"
        reason = "Carry lighting mood across the cut"
    elif _purpose(prev or {}) == purpose:
        move = "motion_continue"
        reason = "Same beat type — continue camera energy"
    else:
        move = PREFERRED_TRANSITIONS[index % len(PREFERRED_TRANSITIONS)]
        if move in {"cross_dissolve", "fade", "crossfade"}:
            move = "match_cut"
        reason = f"Introduce a visually new beat for purpose={purpose}"
    return {
        "transition": move,
        "avoid_crossfade": True,
        "motivated": True,
        "reason": reason,
    }
