"""Emotion vectors and emotion→face control mapping.

Architecture frozen: structured performance data only — not a renderer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class EmotionVector:
    valence: float  # -1 negative … +1 positive
    arousal: float  # 0 calm … 1 intense
    dominance: float  # -1 uncertain … +1 confident
    attention: float  # 0 unfocused … 1 concentrated
    openness: float  # 0 guarded … 1 approachable

    def clamped(self) -> EmotionVector:
        def c(v: float) -> float:
            return max(-1.0, min(1.0, float(v)))

        def u(v: float) -> float:
            return max(0.0, min(1.0, float(v)))

        return EmotionVector(
            valence=c(self.valence),
            arousal=u(self.arousal),
            dominance=c(self.dominance),
            attention=u(self.attention),
            openness=u(self.openness),
        )

    def to_dict(self) -> dict[str, float]:
        return asdict(self.clamped())


EMOTION_LIBRARY: dict[str, EmotionVector] = {
    "neutral": EmotionVector(0.0, 0.25, 0.0, 0.4, 0.5),
    "curiosity": EmotionVector(0.30, 0.55, 0.10, 0.90, 0.70),
    "concern": EmotionVector(-0.45, 0.45, -0.10, 0.85, 0.35),
    "joy": EmotionVector(0.85, 0.70, 0.40, 0.60, 0.90),
    "determination": EmotionVector(0.15, 0.60, 0.90, 1.00, 0.30),
    "surprise": EmotionVector(0.00, 1.00, -0.20, 1.00, 0.75),
    "sadness": EmotionVector(-0.85, 0.25, -0.55, 0.40, 0.20),
    "confidence": EmotionVector(0.45, 0.35, 0.95, 0.80, 0.65),
    "compassion": EmotionVector(0.55, 0.30, 0.20, 0.75, 0.95),
    "fear": EmotionVector(-0.70, 0.85, -0.70, 0.95, 0.15),
    "anger": EmotionVector(-0.60, 0.80, 0.70, 0.90, 0.10),
    "contemplation": EmotionVector(0.05, 0.30, 0.10, 0.70, 0.45),
    "teaching": EmotionVector(0.35, 0.40, 0.55, 0.85, 0.75),
}


# Control deltas relative to neutral (0–1 or -1–1 as noted)
EMOTION_FACE_MAP: dict[str, dict[str, float]] = {
    "curiosity": {
        "brow_inner_left": 0.25,
        "brow_inner_right": 0.15,
        "brow_outer_right": 0.2,
        "upper_lid_left": 0.15,
        "upper_lid_right": 0.15,
        "jaw_open": 0.08,
        "head_tilt": 0.2,
        "forward_lean": 0.25,
    },
    "concern": {
        "brow_inner_left": 0.45,
        "brow_inner_right": 0.45,
        "lower_lid_left": 0.25,
        "lower_lid_right": 0.25,
        "lip_corner_left": -0.15,
        "lip_corner_right": -0.15,
        "neck_tension": 0.2,
        "shoulders_guarded": 0.3,
    },
    "joy": {
        "lip_corner_left": 0.55,
        "lip_corner_right": 0.55,
        "cheek_raise_left": 0.5,
        "cheek_raise_right": 0.5,
        "lower_lid_left": 0.35,
        "lower_lid_right": 0.35,
        "posture_open": 0.5,
    },
    "determination": {
        "brow_outer_left": 0.2,
        "brow_outer_right": 0.2,
        "upper_lid_left": -0.1,
        "upper_lid_right": -0.1,
        "jaw_open": 0.0,
        "chin_raise": 0.25,
        "neck_tension": 0.3,
        "gaze_direct": 1.0,
    },
    "surprise": {
        "brow_inner_left": 0.7,
        "brow_inner_right": 0.7,
        "brow_outer_left": 0.65,
        "brow_outer_right": 0.65,
        "upper_lid_left": 0.7,
        "upper_lid_right": 0.7,
        "jaw_open": 0.45,
        "breath_pause": 1.0,
    },
    "sadness": {
        "brow_inner_left": 0.4,
        "brow_inner_right": 0.4,
        "upper_lid_left": 0.35,
        "upper_lid_right": 0.35,
        "lip_corner_left": -0.45,
        "lip_corner_right": -0.45,
        "gaze_lower": 0.5,
        "posture_collapse": 0.35,
    },
    "confidence": {
        "lip_corner_left": 0.18,
        "lip_corner_right": 0.18,
        "chin_raise": 0.15,
        "gaze_direct": 1.0,
        "posture_balanced": 0.6,
    },
    "compassion": {
        "brow_inner_left": 0.2,
        "brow_inner_right": 0.2,
        "cheek_raise_left": 0.2,
        "cheek_raise_right": 0.2,
        "lip_corner_left": 0.22,
        "lip_corner_right": 0.22,
        "eye_soften": 0.55,
    },
    "teaching": {
        "brow_inner_left": 0.1,
        "brow_inner_right": 0.1,
        "lip_corner_left": 0.18,
        "lip_corner_right": 0.18,
        "gaze_direct": 0.8,
    },
}


def resolve_emotion(name: str | None, *, intensity: float = 1.0) -> EmotionVector:
    base = EMOTION_LIBRARY.get(str(name or "neutral").lower(), EMOTION_LIBRARY["neutral"])
    intensity = max(0.0, min(1.0, float(intensity)))
    return EmotionVector(
        valence=base.valence * intensity,
        arousal=base.arousal * intensity,
        dominance=base.dominance * intensity,
        attention=max(base.attention * intensity, 0.2),
        openness=base.openness * intensity,
    ).clamped()


def emotion_to_face_controls(emotion_name: str, *, intensity: float = 1.0) -> dict[str, float]:
    raw = dict(EMOTION_FACE_MAP.get(str(emotion_name or "neutral").lower()) or {})
    intensity = max(0.0, min(1.0, float(intensity)))
    return {k: round(v * intensity, 4) for k, v in raw.items()}


def blend_emotions(
    primary: str,
    secondary: str | None = None,
    *,
    primary_weight: float = 0.7,
) -> dict[str, Any]:
    a = resolve_emotion(primary)
    if not secondary:
        return {"vector": a.to_dict(), "face_controls": emotion_to_face_controls(primary)}
    b = resolve_emotion(secondary)
    w = max(0.0, min(1.0, primary_weight))
    blended = EmotionVector(
        valence=a.valence * w + b.valence * (1 - w),
        arousal=a.arousal * w + b.arousal * (1 - w),
        dominance=a.dominance * w + b.dominance * (1 - w),
        attention=a.attention * w + b.attention * (1 - w),
        openness=a.openness * w + b.openness * (1 - w),
    ).clamped()
    face_a = emotion_to_face_controls(primary, intensity=w)
    face_b = emotion_to_face_controls(secondary, intensity=1 - w)
    keys = set(face_a) | set(face_b)
    face = {k: round(face_a.get(k, 0.0) + face_b.get(k, 0.0), 4) for k in keys}
    return {
        "primary": primary,
        "secondary": secondary,
        "vector": blended.to_dict(),
        "face_controls": face,
    }


def emotion_transition(
    *,
    from_emotion: str,
    to_emotion: str,
    trigger: str,
    anticipation_seconds: float = 0.12,
    rise_seconds: float = 0.18,
    hold_seconds: float = 0.35,
    recovery_seconds: float = 0.70,
    residue_emotion: str | None = None,
    residue_intensity: float = 0.45,
) -> dict[str, Any]:
    return {
        "from": from_emotion,
        "to": to_emotion,
        "trigger": trigger,
        "phases": ["anticipation", "recognition", "peak", "response", "recovery", "emotional_residue"],
        "anticipation_seconds": anticipation_seconds,
        "rise_seconds": rise_seconds,
        "hold_seconds": hold_seconds,
        "recovery_seconds": recovery_seconds,
        "residue": {
            "emotion": residue_emotion or to_emotion,
            "intensity": residue_intensity,
        },
        "forbid_instant_neutral_reset": True,
    }
