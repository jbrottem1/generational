"""Attention Graph engine — Phase 2: Attention Intelligence.

Builds a 12-dimension **Attention Graph** for every candidate idea: a
radar-chart-ready structure with a 0-100 score per dimension, a single
blended 0-100 Attention Score, and a concrete recommendation for increasing
every dimension (not just the weak ones — the strongest levers get advice
on how to push them further too).

Where Phase 1 (`engines/psychology.py`) produces the full 18-dimension
ViralScore used for ranking and the publish gate, the Attention Graph is a
focused, visualization-first lens on the 12 dimensions that most directly
predict whether a viewer keeps watching, rewatches, comments, and shares.
Nine of the twelve are pulled straight from the (already-tested) psychology
dimension scorer to avoid duplicating logic; three are new to this phase —
Dopenness, Story Tension, and Visual Novelty — scored with their own
deterministic text-feature heuristics.

Runs after Psychology and Script Generation and before Ranking, so every
candidate that reaches ranking already carries its attention graph (the
engine only needs each candidate's title/hook, so its position relative to
Script Generation is a pipeline-ordering choice, not a data dependency).
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.base import Engine
from engines.heuristics import (
    DOPENNESS_WORDS,
    STORY_TENSION_WORDS,
    SURPRISE_WORDS,
    VISUAL_NOVELTY_WORDS,
    VISUAL_WORDS,
    clamp,
    count_hits,
    has_digit,
    sentences,
    stable_jitter,
    weighted_blend,
)
from engines.analysis import score_dimensions as _psychology_dimensions
from services.behavioral_intelligence import attach_report

logger = get_logger(__name__)

# Order matters — this is the display/radar order requested for Phase 2.
ATTENTION_DIMENSIONS = [
    "first_3_second_hook",
    "curiosity_gap",
    "dopenness",
    "emotional_intensity",
    "story_tension",
    "surprise",
    "visual_novelty",
    "shareability",
    "rewatch_probability",
    "comment_likelihood",
    "identity_signaling",
    "tribal_engagement",
]

ATTENTION_LABELS = {
    "first_3_second_hook": "First 3-Second Hook",
    "curiosity_gap": "Curiosity Gap",
    "dopenness": "Dopenness",
    "emotional_intensity": "Emotional Intensity",
    "story_tension": "Story Tension",
    "surprise": "Surprise",
    "visual_novelty": "Visual Novelty",
    "shareability": "Shareability",
    "rewatch_probability": "Rewatch Probability",
    "comment_likelihood": "Comment Likelihood",
    "identity_signaling": "Identity Signaling",
    "tribal_engagement": "Tribal Engagement",
}

# Blend weights for the single Attention Score (0-100). Data, not code —
# tunable by the future Learning Engine. Sum == 1.0.
ATTENTION_GRAPH_WEIGHTS = {
    "first_3_second_hook": 0.14,
    "curiosity_gap": 0.12,
    "dopenness": 0.10,
    "emotional_intensity": 0.08,
    "story_tension": 0.08,
    "surprise": 0.08,
    "visual_novelty": 0.07,
    "shareability": 0.09,
    "rewatch_probability": 0.08,
    "comment_likelihood": 0.06,
    "identity_signaling": 0.05,
    "tribal_engagement": 0.05,
}

# Maps the Attention Graph's own dimensions onto the Phase 1 psychology
# dimensions that already score the same underlying signal, so the two
# phases stay consistent instead of drifting apart.
_PSYCHOLOGY_ALIASES = {
    "first_3_second_hook": "first_3_second_hook",
    "curiosity_gap": "curiosity_gap",
    "emotional_intensity": "emotional_intensity",
    "surprise": "surprise",
    "shareability": "share_likelihood",
    "rewatch_probability": "replay_value",
    "comment_likelihood": "comment_likelihood",
    "identity_signaling": "audience_identity",
    "tribal_engagement": "community_appeal",
}

# (low-score tip, mid-score tip, high-score tip) — a recommendation is
# always returned for every dimension, framed as "how to push this higher".
RECOMMENDATIONS = {
    "first_3_second_hook": (
        "Cut the opening line to under 10 words and open mid-action or with a direct question.",
        "Sharpen the first sentence — remove throat-clearing words before the hook lands.",
        "Hook is strong — keep testing shorter variants to shave off even more 3-second drop-off.",
    ),
    "curiosity_gap": (
        "Add an explicit unanswered question or a 'secret/hidden' framing to the title.",
        "Name what's missing without revealing the answer to widen the gap.",
        "Curiosity gap is strong — don't resolve it until deep into the script.",
    ),
    "dopenness": (
        "Add a simple, low-jargon promise of a payoff (e.g. 'here's what happens next').",
        "Simplify the language slightly and tease the reward earlier in the hook.",
        "Great open-loop pull — keep the promise concrete and deliver on it fast.",
    ),
    "emotional_intensity": (
        "Swap neutral verbs for charged ones (shocking, heartbreaking, unbelievable).",
        "Push one emotional beat further — pick the strongest word and amplify it.",
        "Strong emotional charge — make sure the script's payoff matches the setup's intensity.",
    ),
    "story_tension": (
        "Introduce a turning-point word ('but then', 'suddenly', 'until') to create a mini-arc.",
        "Add a clearer before/after contrast to raise the stakes.",
        "Tension is set up well — make sure the script pays off the turn quickly.",
    ),
    "surprise": (
        "Reframe the premise as a myth-bust or a reversal of expectation.",
        "Make the twist more explicit in the hook itself.",
        "Surprise lands — don't telegraph it in the title, save it for the hook.",
    ),
    "visual_novelty": (
        "Describe a concrete, visual first frame (before/after, close-up, transformation).",
        "Add one more visual cue word so the thumbnail concept is obvious.",
        "Visual concept is strong — storyboard the first 3 seconds around it.",
    ),
    "shareability": (
        "Combine emotion + surprise + an identity callout so viewers forward it to someone specific.",
        "Add a line that makes the sharer look smart or in-the-know.",
        "Highly shareable — make the CTA explicitly ask viewers to send it to someone.",
    ),
    "rewatch_probability": (
        "Add a numbered structure (stages/steps) viewers replay to catch details.",
        "Layer in one more detail worth catching on a second watch.",
        "Strong rewatch pull — consider an on-screen counter or checklist overlay.",
    ),
    "comment_likelihood": (
        "End with a direct question or a mildly debatable claim.",
        "Sharpen the stance so viewers want to agree or push back.",
        "Comments should flow naturally — seed a reply-bait question in the caption too.",
    ),
    "identity_signaling": (
        "Name the 'type of person' this is for (e.g. 'if you're someone who...').",
        "Move the identity callout earlier in the hook.",
        "Identity hook is clear — lean into it in the CTA ('tag someone who...').",
    ),
    "tribal_engagement": (
        "Use in-group language ('we', 'us', 'you're not alone') to build belonging.",
        "Add one more community cue to reinforce belonging.",
        "Community pull is strong — invite viewers to share their own experience in the comments.",
    ),
}


def _recommend(dimension: str, score: int) -> str:
    low, mid, high = RECOMMENDATIONS[dimension]
    if score < 45:
        return low
    if score < 70:
        return mid
    return high


def _dopenness(text: str, jitter: int) -> int:
    words = text.split() or [""]
    avg_word_len = sum(len(w) for w in words) / len(words)
    simplicity_bonus = 10 if avg_word_len <= 5.5 else 0
    raw = (
        38
        + 15 * min(count_hits(text, DOPENNESS_WORDS), 3)
        + simplicity_bonus
        + (6 if has_digit(text) else 0)
    )
    return clamp(raw + jitter)


def _story_tension(text: str, jitter: int) -> int:
    parts = sentences(text)
    multi_beat_bonus = 8 if len(parts) >= 2 else 0
    raw = (
        34
        + 17 * min(count_hits(text, STORY_TENSION_WORDS), 3)
        + 8 * min(count_hits(text, SURPRISE_WORDS), 2)
        + multi_beat_bonus
    )
    return clamp(raw + jitter)


def _visual_novelty(text: str, jitter: int) -> int:
    raw = (
        36
        + 15 * min(count_hits(text, VISUAL_NOVELTY_WORDS), 3)
        + 8 * min(count_hits(text, VISUAL_WORDS), 2)
        + (6 if has_digit(text) else 0)
    )
    return clamp(raw + jitter)


def score_attention_dimensions(text: str) -> dict:
    """Score a title+hook text across all 12 Attention Graph dimensions (0-100)."""
    jitter = stable_jitter(text)
    psychology = _psychology_dimensions(text)

    scores = {key: psychology[source] for key, source in _PSYCHOLOGY_ALIASES.items()}
    scores["dopenness"] = _dopenness(text, jitter)
    scores["story_tension"] = _story_tension(text, jitter)
    scores["visual_novelty"] = _visual_novelty(text, jitter)

    return {key: scores[key] for key in ATTENTION_DIMENSIONS}


def attention_score(dimensions: dict) -> int:
    """Single weighted 0-100 Attention Score from the 12 dimensions."""
    return weighted_blend(dimensions, ATTENTION_GRAPH_WEIGHTS)


def build_radar_chart(dimensions: dict) -> dict:
    """Radar-chart-ready payload: parallel label/score arrays in display order."""
    return {
        "labels": [ATTENTION_LABELS[key] for key in ATTENTION_DIMENSIONS],
        "scores": [dimensions[key] for key in ATTENTION_DIMENSIONS],
    }


def build_recommendations(dimensions: dict) -> dict:
    """One actionable recommendation per dimension, keyed by dimension name."""
    return {key: _recommend(key, dimensions[key]) for key in ATTENTION_DIMENSIONS}


def build_attention_graph(title: str = "", hook: str = "") -> dict:
    """Full Attention Graph payload for one idea: scores, radar data, recommendations."""
    text = f"{title} {hook}".strip()
    dimensions = score_attention_dimensions(text)
    score = attention_score(dimensions)
    return {
        "scores": dimensions,
        "attention_score": score,
        "radar_chart": build_radar_chart(dimensions),
        "recommendations": build_recommendations(dimensions),
    }


class AttentionGraphEngine(Engine):
    key = "attention_graph"
    label = "Attention Graph"
    icon = "🕸️"
    description = (
        "Build a 12-dimension Attention Graph (radar chart + 0-100 scores) for every "
        "idea with recommendations for increasing each score."
    )

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        candidates = context.get("candidates", [])
        for candidate in candidates:
            candidate["attention_graph"] = build_attention_graph(
                candidate.get("title", ""), candidate.get("hook", "")
            )
            # Refresh the Behavioral Intelligence report now that richer
            # Attention Graph data (shareability, rewatch, story tension, ...)
            # is available for this candidate.
            attach_report(candidate)

        avg_score = (
            round(sum(c["attention_graph"]["attention_score"] for c in candidates) / len(candidates), 1)
            if candidates
            else 0
        )
        log_event(logger, "attention_graph.built", candidates=len(candidates), avg_attention_score=avg_score)
        return {
            "candidates": candidates,
            "attention_graph_summary": {"average_attention_score": avg_score, "scored": len(candidates)},
        }
