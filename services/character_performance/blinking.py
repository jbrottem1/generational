"""Context-aware blinking — never fixed robotic intervals."""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class BlinkContext:
    seconds_since_last_blink: float
    gaze_shift_intensity: float
    sentence_boundary: bool
    stress_level: float
    fatigue_level: float
    wind_exposure: float
    focus_intensity: float


def blink_probability(context: BlinkContext) -> float:
    probability = 0.02
    probability += min(context.seconds_since_last_blink / 12.0, 0.35)
    probability += context.gaze_shift_intensity * 0.15
    probability += 0.12 if context.sentence_boundary else 0.0
    probability += context.stress_level * 0.10
    probability += context.fatigue_level * 0.15
    probability += context.wind_exposure * 0.08
    probability -= context.focus_intensity * 0.10
    return max(0.0, min(probability, 0.85))


def should_blink(context: BlinkContext, *, rng: random.Random | None = None) -> bool:
    r = rng or random.Random(0)  # deterministic default for plans
    return r.random() < blink_probability(context)


BLINK_TYPES = [
    "normal",
    "partial",
    "double",
    "slow_tired",
    "startled",
    "emotional",
    "refocus",
]

BLINK_PHASES = [
    "pre_blink_softening",
    "rapid_upper_lid_closure",
    "brief_contact",
    "slower_reopening",
    "refocus",
]


def build_blink_profile(
    *,
    mode: str = "natural",
    stress_multiplier: float = 0.2,
    fatigue: float = 0.1,
    wind_exposure: float = 0.0,
    focus_intensity: float = 0.6,
    sentence_boundary: bool = False,
    gaze_shift_intensity: float = 0.3,
) -> dict[str, Any]:
    ctx = BlinkContext(
        seconds_since_last_blink=4.0,
        gaze_shift_intensity=gaze_shift_intensity,
        sentence_boundary=sentence_boundary,
        stress_level=stress_multiplier,
        fatigue_level=fatigue,
        wind_exposure=wind_exposure,
        focus_intensity=focus_intensity,
    )
    return {
        "mode": mode,
        "stress_multiplier": stress_multiplier,
        "context": asdict(ctx),
        "probability_now": round(blink_probability(ctx), 4),
        "phases": list(BLINK_PHASES),
        "types_supported": list(BLINK_TYPES),
        "rules": [
            "upper_lids_do_most_of_the_motion",
            "lower_lids_subtle",
            "never_fixed_robotic_interval",
            "context_aware",
        ],
    }


def plan_blinks_for_duration(
    duration_seconds: float,
    *,
    stress: float = 0.2,
    focus: float = 0.6,
    seed: int = 7,
) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    events: list[dict[str, Any]] = []
    t = 0.0
    last = 0.0
    while t < duration_seconds:
        t += 0.25
        ctx = BlinkContext(
            seconds_since_last_blink=t - last,
            gaze_shift_intensity=0.2 if abs(t - duration_seconds * 0.5) < 0.3 else 0.05,
            sentence_boundary=abs(t - duration_seconds * 0.7) < 0.2,
            stress_level=stress,
            fatigue_level=0.1,
            wind_exposure=0.0,
            focus_intensity=focus,
        )
        if should_blink(ctx, rng=rng):
            events.append(
                {
                    "time": round(t, 3),
                    "type": "refocus" if ctx.gaze_shift_intensity > 0.15 else "normal",
                    "phases": list(BLINK_PHASES),
                }
            )
            last = t
    return events
