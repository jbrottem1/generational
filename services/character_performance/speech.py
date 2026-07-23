"""Speech / viseme performance structures — sync with narration timing."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.character_performance.emotion import EmotionVector, resolve_emotion


VISEME_CATEGORIES = [
    "neutral",
    "closed_lips",
    "wide_vowel",
    "round_vowel",
    "teeth_contact",
    "tongue_forward",
    "jaw_open",
    "lip_funnel",
    "lip_pucker",
]


@dataclass
class VisemeKeyframe:
    timestamp: float
    viseme: str
    weight: float


@dataclass
class SpeechPerformance:
    audio_path: str
    visemes: list[VisemeKeyframe]
    emotion: EmotionVector
    breath_markers: list[float]


def rough_visemes_from_narration(
    narration: str,
    *,
    duration_seconds: float,
) -> list[VisemeKeyframe]:
    """Deterministic placeholder timing until real phoneme aligner is attached.

    Not proof of lip-sync quality — production must validate against audio.
    """
    words = [w for w in (narration or "").split() if w]
    if not words or duration_seconds <= 0:
        return [VisemeKeyframe(0.0, "neutral", 1.0)]
    step = duration_seconds / max(len(words), 1)
    keys: list[VisemeKeyframe] = []
    cycle = ["wide_vowel", "closed_lips", "round_vowel", "teeth_contact", "jaw_open", "lip_funnel"]
    for i, _w in enumerate(words):
        keys.append(VisemeKeyframe(round(i * step, 3), cycle[i % len(cycle)], 0.85))
    keys.append(VisemeKeyframe(round(duration_seconds, 3), "neutral", 1.0))
    return keys


def build_speech_performance(
    *,
    narration: str,
    duration_seconds: float,
    emotion_name: str = "teaching",
    audio_path: str = "",
) -> dict[str, Any]:
    emotion = resolve_emotion(emotion_name)
    visemes = rough_visemes_from_narration(narration, duration_seconds=duration_seconds)
    breath = [round(duration_seconds * x, 3) for x in (0.0, 0.45, 0.85) if x * duration_seconds < duration_seconds]
    perf = SpeechPerformance(
        audio_path=audio_path,
        visemes=visemes,
        emotion=emotion,
        breath_markers=breath,
    )
    return {
        "audio_path": perf.audio_path,
        "visemes": [asdict(v) for v in perf.visemes],
        "emotion": perf.emotion.to_dict(),
        "breath_markers": perf.breath_markers,
        "categories": list(VISEME_CATEGORIES),
        "rules": [
            "do_not_animate_only_lips",
            "include_jaw_cheeks_breath_expression_overlay",
            "coarticulation_required",
            "validate_against_real_narration_audio",
        ],
        "placeholder_timing": not bool(audio_path),
        "quality_note": (
            "Viseme keyframes here are planning aids. "
            "Lip sync is only valid after rendered frames match live narration audio."
        ),
    }
