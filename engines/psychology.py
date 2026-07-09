"""Psychology & Virality Engine — stage 3: score every candidate concept.

This is the attention-engineering core of the Intelligence Pipeline. It runs
immediately after Ideation (which itself runs after Trend Discovery) and
immediately before Script Generation and Ranking, so nothing gets scripted,
produced, or published without first passing through a measurable model of
human attention.

Every candidate is scored across 18 behavioral-psychology / attention
dimensions (curiosity gap, emotional intensity, surprise, novelty, fear,
humor, satisfaction, retention potential, replay value, comment likelihood,
share likelihood, controversy, visual hook strength, first-3-second hook,
dopamine curve, information density, audience identity, community appeal).
Dimensions are blended into a single weighted **ViralScore (0-100)**, and a
plain-English **psychology report** explains why the concept scored the way
it did — its top strengths, its weakest levers, and concrete language to
watch for.

Scoring is deterministic text-feature analysis (word-bank hits, punctuation,
structure, digits) so it is fast, free, reproducible in every mode, and
fully unit-testable without an API key. Swapping in a learned model later
only requires changing `score_dimensions()` — the engine contract, the
context keys, and the report shape all stay the same.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.analysis import score_dimensions
from engines.base import Engine
from engines.heuristics import weighted_blend
from services.behavioral_intelligence import attach_report

logger = get_logger(__name__)

# How much each dimension contributes to the overall ViralScore (0-100).
# Weights are data, not code, so the future Learning Engine can tune them
# from real performance data without touching scoring logic. Sum == 1.0.
VIRAL_SCORE_WEIGHTS = {
    "curiosity_gap": 0.10,
    "emotional_intensity": 0.08,
    "surprise": 0.07,
    "novelty": 0.05,
    "fear": 0.03,
    "humor": 0.04,
    "satisfaction": 0.04,
    "retention_potential": 0.12,
    "replay_value": 0.05,
    "comment_likelihood": 0.06,
    "share_likelihood": 0.08,
    "controversy": 0.03,
    "visual_hook_strength": 0.06,
    "first_3_second_hook": 0.10,
    "dopamine_curve": 0.04,
    "information_density": 0.02,
    "audience_identity": 0.02,
    "community_appeal": 0.01,
}

# Backward-compatible alias — earlier versions called this DIMENSION_WEIGHTS.
DIMENSION_WEIGHTS = VIRAL_SCORE_WEIGHTS

DIMENSION_LABELS = {
    "curiosity_gap": "Curiosity Gap",
    "emotional_intensity": "Emotional Intensity",
    "surprise": "Surprise",
    "novelty": "Novelty",
    "fear": "Fear",
    "humor": "Humor",
    "satisfaction": "Satisfaction",
    "retention_potential": "Retention Potential",
    "replay_value": "Replay Value",
    "comment_likelihood": "Comment Likelihood",
    "share_likelihood": "Share Likelihood",
    "controversy": "Controversy (bounded)",
    "visual_hook_strength": "Visual Hook Strength",
    "first_3_second_hook": "First 3-Second Hook",
    "dopamine_curve": "Dopamine Curve",
    "information_density": "Information Density",
    "audience_identity": "Audience Identity",
    "community_appeal": "Community Appeal",
}

# (high-score note, low-score note) shown to explain WHY a dimension landed
# where it did. Anything in between gets a neutral "moderate" note.
DIMENSION_EXPLANATIONS = {
    "curiosity_gap": (
        "Opens an information gap the viewer must watch to close.",
        "States the idea plainly — nothing left unanswered to pull viewers in.",
    ),
    "emotional_intensity": (
        "Uses charged language that provokes a strong emotional reaction.",
        "Emotionally flat phrasing — unlikely to trigger a felt response.",
    ),
    "surprise": (
        "Signals a reversal or myth-bust that defies expectations.",
        "No twist or contradiction — the premise is expected.",
    ),
    "novelty": (
        "Framed as new, first-of-its-kind, or freshly discovered.",
        "Familiar framing the audience has likely already seen before.",
    ),
    "fear": (
        "Taps loss-aversion / threat language that drives urgency to watch.",
        "No risk or warning framing — low urgency to act or keep watching.",
    ),
    "humor": (
        "Playful or absurd framing that invites a light, shareable reaction.",
        "Serious tone throughout — little comedic hook.",
    ),
    "satisfaction": (
        "Promises a payoff, resolution, or 'aha' moment worth watching for.",
        "No clear payoff moment signaled — reward is unclear.",
    ),
    "retention_potential": (
        "Speaks directly to the viewer at a paceable length — built to be watched to the end.",
        "Not addressed to the viewer directly, or awkward length for a short.",
    ),
    "replay_value": (
        "Packs a countable structure (numbers/stages) worth rewatching to catch details.",
        "Single flat statement — nothing to invite a second watch.",
    ),
    "comment_likelihood": (
        "Invites a reaction or takes a stance people will want to weigh in on.",
        "Neutral statement that gives viewers nothing to respond to.",
    ),
    "share_likelihood": (
        "Combines emotion, surprise, and identity — the exact mix people forward to friends.",
        "Low emotional/surprise/identity signal — little reason to share.",
    ),
    "controversy": (
        "Takes a mild contrarian stance that sparks debate (bounded — no policy-violating claims).",
        "Uncontroversial framing — unlikely to spark disagreement in the comments.",
    ),
    "visual_hook_strength": (
        "Cues a strong first-frame visual (reveal, before/after, concrete imagery).",
        "Abstract phrasing with nothing concrete for a thumbnail or first frame.",
    ),
    "first_3_second_hook": (
        "Short, punchy opening line built to survive the first 3-second drop-off window.",
        "Opening line is long or generic — high risk of a 3-second drop-off.",
    ),
    "dopamine_curve": (
        "Sets up a mini reward loop (tease → payoff) that keeps attention climbing.",
        "Flat delivery with no tease-then-payoff structure.",
    ),
    "information_density": (
        "Balanced density — concrete enough to feel valuable without becoming a lecture.",
        "Too sparse or too jargon-dense for a 15-30s short.",
    ),
    "audience_identity": (
        "Names a 'type of person' the viewer can recognize themselves in.",
        "Speaks to no one in particular — no identity hook.",
    ),
    "community_appeal": (
        "Uses in-group language ('we', 'us', community) that builds belonging.",
        "Individual framing only — no community/in-group pull.",
    ),
}

TIER_THRESHOLDS = (
    (80, "Breakout Viral Potential"),
    (65, "Strong Viral Potential"),
    (50, "Moderate Potential"),
    (0, "Low Potential — needs a stronger hook"),
)


def _tier_for(score: int) -> str:
    for threshold, label in TIER_THRESHOLDS:
        if score >= threshold:
            return label
    return TIER_THRESHOLDS[-1][1]


# The 18-dimension scorer now lives in the shared analysis library
# (`engines/analysis.py`) per Architecture Directive #1, so the Attention
# Graph can consume it without an engine-to-engine import. Re-exported here
# because this module remains its public psychology-facing home.
# Backward-compatible alias for the pre-v7.1 six-dimension API name.
score_text = score_dimensions


def viral_score(dimensions: dict) -> int:
    """Weighted 0-100 ViralScore from the 18 psychology dimensions."""
    return weighted_blend(dimensions, VIRAL_SCORE_WEIGHTS)


# Backward-compatible alias — earlier versions called this overall_score.
overall_score = viral_score


def _explain(dimension: str, score: int) -> str:
    high_note, low_note = DIMENSION_EXPLANATIONS[dimension]
    if score >= 70:
        return high_note
    if score <= 40:
        return low_note
    return f"Middling signal — some cues present but not decisive ({score}/100)."


def build_report(dimensions: dict, score: int, title: str = "", hook: str = "") -> dict:
    """Human-readable psychology report explaining WHY a concept scored as it did."""
    ranked = sorted(dimensions.items(), key=lambda kv: kv[1], reverse=True)
    strengths = [
        {"dimension": DIMENSION_LABELS[key], "key": key, "score": value, "note": _explain(key, value)}
        for key, value in ranked[:3]
    ]
    weaknesses = [
        {"dimension": DIMENSION_LABELS[key], "key": key, "score": value, "note": _explain(key, value)}
        for key, value in ranked[-3:]
    ]
    tier = _tier_for(score)
    label = title or hook or "This concept"
    top_names = ", ".join(item["dimension"] for item in strengths)
    weak_names = ", ".join(item["dimension"] for item in weaknesses)
    summary = (
        f"\"{label}\" scores {score}/100 ({tier}). "
        f"Strongest levers: {top_names}. Weakest levers: {weak_names}."
    )
    return {
        "viral_score": score,
        "tier": tier,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "dimension_notes": {key: _explain(key, value) for key, value in dimensions.items()},
        "summary": summary,
    }


class PsychologyEngine(Engine):
    key = "psychology"
    label = "Psychology & Virality"
    icon = "🧠"
    description = (
        "Score every concept across 18 attention/virality dimensions and produce a "
        "weighted ViralScore (0-100) with a plain-English psychology report."
    )

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        candidates = context.get("candidates", [])
        for candidate in candidates:
            text = f"{candidate.get('title', '')} {candidate.get('hook', '')}".strip()
            dimensions = score_dimensions(text)
            score = viral_score(dimensions)
            report = build_report(dimensions, score, candidate.get("title", ""), candidate.get("hook", ""))

            candidate["psychology"] = dimensions
            # `psychology_score` stays for backward compatibility with the
            # ranking and quality engines; `viral_score` is the new canonical name.
            candidate["psychology_score"] = score
            candidate["viral_score"] = score
            candidate["psychology_report"] = report
            # Behavioral Intelligence API (Phase 4): a standardized report any
            # engine can consume by attribute access. Available from this point
            # on for every downstream stage — Script Generation, Visual
            # Intelligence, and Voice & Audio all run before the Attention Graph
            # and Threat Detection refresh it with richer data below.
            attach_report(candidate)

        avg_score = round(sum(c["viral_score"] for c in candidates) / len(candidates), 1) if candidates else 0
        log_event(logger, "psychology.scored", candidates=len(candidates), avg_viral_score=avg_score)
        return {
            "candidates": candidates,
            "psychology_summary": {"average_viral_score": avg_score, "scored": len(candidates)},
        }
