"""Psychology engine — stage 3: score every candidate concept.

Scores each candidate on six virality dimensions (curiosity, emotional
impact, surprise, authority, retention potential, shareability) using
deterministic text-feature analysis, so scoring is fast, free, and
reproducible in every mode.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.base import Engine
from engines.heuristics import (
    AUTHORITY_WORDS,
    CURIOSITY_WORDS,
    EMOTION_WORDS,
    SURPRISE_WORDS,
    clamp,
    count_hits,
    has_digit,
    stable_jitter,
)

logger = get_logger(__name__)

# How much each dimension contributes to the overall psychology score.
DIMENSION_WEIGHTS = {
    "curiosity": 0.25,
    "emotional_impact": 0.15,
    "surprise": 0.15,
    "authority": 0.10,
    "retention_potential": 0.20,
    "shareability": 0.15,
}


def score_text(text: str) -> dict:
    """Six-dimension psychology scores (0-100) for a title+hook text."""
    words = text.split()
    jitter = stable_jitter(text)

    curiosity = 42 + 13 * min(count_hits(text, CURIOSITY_WORDS), 3) + (8 if "?" in text else 0)
    emotional = 40 + 15 * min(count_hits(text, EMOTION_WORDS), 3)
    surprise = 38 + 16 * min(count_hits(text, SURPRISE_WORDS), 3)
    authority = 34 + (16 if has_digit(text) else 0) + 13 * min(count_hits(text, AUTHORITY_WORDS), 3)
    retention = (
        44
        + (10 if "you" in text.lower() else 0)
        + (10 if 8 <= len(words) <= 28 else 0)
        + (6 if count_hits(text, CURIOSITY_WORDS) else 0)
    )
    shareability = 40 + 9 * min(
        count_hits(text, CURIOSITY_WORDS) + count_hits(text, EMOTION_WORDS) + count_hits(text, SURPRISE_WORDS), 4
    )

    return {
        "curiosity": clamp(curiosity + jitter),
        "emotional_impact": clamp(emotional + jitter),
        "surprise": clamp(surprise + jitter),
        "authority": clamp(authority + jitter),
        "retention_potential": clamp(retention + jitter),
        "shareability": clamp(shareability + jitter),
    }


def overall_score(dimensions: dict) -> int:
    return clamp(sum(dimensions[key] * weight for key, weight in DIMENSION_WEIGHTS.items()))


class PsychologyEngine(Engine):
    key = "psychology"
    label = "Psychology"
    icon = "🧲"
    description = "Score concepts for curiosity, emotion, surprise, authority, retention, shareability."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        candidates = context.get("candidates", [])
        for candidate in candidates:
            text = f"{candidate.get('title', '')} {candidate.get('hook', '')}"
            dimensions = score_text(text)
            candidate["psychology"] = dimensions
            candidate["psychology_score"] = overall_score(dimensions)

        log_event(logger, "psychology.scored", candidates=len(candidates))
        return {"candidates": candidates}
