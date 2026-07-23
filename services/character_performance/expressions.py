"""Expression blending, micro-expressions, face control recipes."""

from __future__ import annotations

from typing import Any

from services.character_performance.emotion import emotion_to_face_controls, emotion_transition


def micro_expression(
    *,
    kind: str,
    start: float,
    duration: float = 0.18,
    intensity: float = 0.25,
    asymmetric: bool = False,
    side: str = "left",
) -> dict[str, Any]:
    recipes = {
        "lip_press_uncertainty": {"lip_corner_left": -0.1, "lip_corner_right": -0.1, "chin_raise": 0.1},
        "brow_lift_question": {"brow_outer_left": 0.25, "brow_outer_right": 0.1},
        "eye_narrow_determination": {"upper_lid_left": -0.15, "upper_lid_right": -0.15},
        "nostril_flare_effort": {"nose_flare": 0.3},
        "cheek_tension_suppressed": {"cheek_raise_left": 0.15, "cheek_raise_right": 0.05},
        "fast_glance_withhold": {"gaze_shift": 0.4},
        "jaw_tension_concern": {"chin_raise": 0.2, "neck_tension": 0.25},
    }
    controls = dict(recipes.get(kind) or {"brow_inner_left": 0.15})
    if asymmetric and side == "right":
        controls = {k.replace("left", "tmp").replace("right", "left").replace("tmp", "right"): v for k, v in controls.items()}
    return {
        "kind": kind,
        "start": start,
        "duration": duration,
        "intensity": intensity,
        "asymmetric": asymmetric,
        "controls": {k: round(v * intensity, 4) for k, v in controls.items()},
        "rule": "brief_low_intensity_context_specific_never_random",
    }


def build_expression_curve(
    *,
    primary: str,
    secondary: str | None = None,
    duration_seconds: float = 3.0,
    intensity: float = 0.65,
) -> list[dict[str, Any]]:
    primary_controls = emotion_to_face_controls(primary, intensity=intensity)
    secondary_controls = emotion_to_face_controls(secondary or primary, intensity=intensity * 0.35)
    return [
        {"time": 0.0, "label": "anticipation", "controls": {k: v * 0.3 for k, v in primary_controls.items()}},
        {"time": round(duration_seconds * 0.15, 3), "label": "rise", "controls": primary_controls},
        {"time": round(duration_seconds * 0.45, 3), "label": "peak", "controls": primary_controls},
        {
            "time": round(duration_seconds * 0.75, 3),
            "label": "blend_secondary",
            "controls": {
                k: round(primary_controls.get(k, 0) * 0.6 + secondary_controls.get(k, 0), 4)
                for k in set(primary_controls) | set(secondary_controls)
            },
        },
        {
            "time": round(duration_seconds, 3),
            "label": "residue",
            "controls": {k: v * 0.4 for k, v in primary_controls.items()},
        },
    ]


def plan_micro_expressions(primary: str, duration_seconds: float) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if primary in {"concern", "compassion", "curiosity"}:
        out.append(micro_expression(kind="lip_press_uncertainty", start=0.15, asymmetric=True))
    if primary in {"curiosity", "teaching"}:
        out.append(micro_expression(kind="brow_lift_question", start=0.35, asymmetric=True))
    if primary in {"determination", "confidence"}:
        out.append(micro_expression(kind="eye_narrow_determination", start=0.25))
    if primary == "concern":
        out.append(micro_expression(kind="jaw_tension_concern", start=min(0.8, duration_seconds * 0.4)))
    return out


def expression_transition_block(primary: str, trigger: str = "story_beat") -> dict[str, Any]:
    return emotion_transition(
        from_emotion="neutral",
        to_emotion=primary,
        trigger=trigger,
        residue_emotion=primary if primary != "surprise" else "curiosity",
    )
