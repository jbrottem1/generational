"""Builds a `BehavioralIntelligenceReport` from a candidate/idea dict.

`build_report()` is the one function that turns whatever behavioral signal a
candidate currently carries — Psychology dimensions, an Attention Graph, a
Threat Report, any mix of the three — into the standardized report defined
in `models.py`. It degrades gracefully: call it right after
`engines/psychology.py` runs (before the Attention Graph or Threat Detection
exist for this candidate) and every field still comes back populated, just
with lower `confidence` and Psychology-only fallback formulas for the fields
that the Attention Graph would otherwise supply directly.

This is what makes the report usable by Script Generation, Visual
Intelligence, and Voice & Audio: all three run in the pipeline *before* the
Attention Graph and Threat Detection (see `core/workflows.py`), so they only
ever see the Psychology-only version — and that version is exactly as
well-formed and typed as the richer one produced later.

Usage (any engine, no custom parsing):

    from services.behavioral_intelligence import build_report

    report = build_report(candidate)
    if report.hook_strength < 60:
        ...  # act on a typed attribute, not a raw dict key
"""

from __future__ import annotations

from core.heuristics import clamp
from services.behavioral_intelligence.models import BehavioralIntelligenceReport, SCORE_FIELDS

# (field, low-score tip) — one concrete growth tip per scored field. Kept
# self-contained (no import of engines/attention_graph.py's own
# RECOMMENDATIONS dict) so this module never depends on engine internals —
# only on the plain dict shape candidates already carry.
FIELD_TIPS = {
    "viral_score": "Strengthen the weakest Psychology dimension driving this score (see the psychology report).",
    "attention_score": "Tighten the hook and add a mid-video pattern interrupt to lift overall attention.",
    "curiosity_score": "Add an explicit unanswered question or a 'secret/hidden' framing to the title.",
    "emotional_intensity": "Swap neutral verbs for charged ones (shocking, heartbreaking, unbelievable).",
    "novelty_score": "Frame the concept as new, first-of-its-kind, or freshly discovered.",
    "shareability_score": "Combine emotion + surprise + an identity callout so viewers forward it to someone.",
    "replay_probability": "Add a numbered structure (stages/steps) viewers replay to catch details.",
    "comment_probability": "End with a direct question or a mildly debatable claim.",
    "retention_prediction": "Speak directly to the viewer and tighten pacing to hold attention to the end.",
    "hook_strength": "Cut the opening line to under 10 words and open mid-action or with a direct question.",
    "identity_resonance": "Name the 'type of person' this concept is for.",
    "visual_interest_score": "Describe a concrete, visual first frame (before/after, close-up, transformation).",
    "narrative_tension": "Introduce a turning-point word ('but then', 'suddenly', 'until') to create a mini-arc.",
}

# Below this, a field's tip is considered worth surfacing as a recommendation.
_WEAK_THRESHOLD = 55

# Max recommendations returned, growth tips first (weakest fields), then any
# high-severity threat fixes.
_MAX_RECOMMENDATIONS = 5
_MAX_THREAT_FIXES = 2


def _visual_interest(psychology: dict, attention_scores: dict) -> int:
    """Blend Psychology's visual_hook_strength with the Attention Graph's
    visual_novelty when both exist; use whichever one is available otherwise."""
    values = []
    if "visual_hook_strength" in psychology:
        values.append(psychology["visual_hook_strength"])
    if "visual_novelty" in attention_scores:
        values.append(attention_scores["visual_novelty"])
    if not values:
        return 50
    return clamp(sum(values) / len(values))


def _narrative_tension(psychology: dict, attention_scores: dict) -> int:
    """Story Tension direct from the Attention Graph once it exists;
    otherwise approximate from Psychology's surprise + dopamine_curve —
    the closest pre-Attention-Graph proxy for a mini story-arc signal."""
    if "story_tension" in attention_scores:
        return attention_scores["story_tension"]
    surprise = psychology.get("surprise", 50)
    dopamine = psychology.get("dopamine_curve", 50)
    return clamp((surprise + dopamine) / 2)


def _confidence(candidate: dict) -> int:
    """More upstream signal present -> higher confidence in the report.

    A future ML confidence model would replace this rule with a learned
    calibration (e.g. predicted-vs-actual error by signal combination) but
    must keep returning an int 0-100 — see the Extension Points section in
    MASTER_ARCHITECTURE.md.
    """
    score = 55
    if candidate.get("psychology"):
        score += 10
    if candidate.get("attention_graph"):
        score += 15
    if candidate.get("threat_report"):
        score += 10
    if candidate.get("script") or candidate.get("full_script"):
        score += 5
    return clamp(score, low=50, high=98)


def _recommendations(values: dict, candidate: dict) -> list:
    """Actionable fixes: flagged threats reserve their slots first (they are
    production risks, not just growth opportunities), then the weakest
    scored fields fill whatever room is left, up to `_MAX_RECOMMENDATIONS`."""
    threat_report = candidate.get("threat_report") or {}
    threat_fixes = []
    for item in threat_report.get("flagged_threats", [])[:_MAX_THREAT_FIXES]:
        fix = item.get("fix")
        if fix and fix not in threat_fixes:
            threat_fixes.append(fix)

    remaining_slots = max(_MAX_RECOMMENDATIONS - len(threat_fixes), 0)
    weak_fields = sorted(
        (key for key in FIELD_TIPS if values[key] < _WEAK_THRESHOLD),
        key=lambda key: values[key],
    )
    growth_tips = [FIELD_TIPS[key] for key in weak_fields[:remaining_slots]]

    tips = threat_fixes + growth_tips
    if not tips:
        tips.append("No major gaps detected — maintain the current hook/pacing/payoff balance.")

    return tips[:_MAX_RECOMMENDATIONS]


def build_report(candidate: dict) -> BehavioralIntelligenceReport:
    """Build the standardized Behavioral Intelligence report for one candidate.

    Reads whatever of `psychology`, `attention_graph`, and `threat_report`
    the candidate currently carries — never requires all three. Safe to call
    at any point in the pipeline once Psychology has run.
    """
    psychology = candidate.get("psychology") or {}
    attention = candidate.get("attention_graph") or {}
    attention_scores = attention.get("scores") or {}

    fallback_score = candidate.get("viral_score", candidate.get("psychology_score", 50))

    values = {
        "viral_score": fallback_score,
        "attention_score": attention.get("attention_score", fallback_score),
        "curiosity_score": psychology.get("curiosity_gap", 50),
        "emotional_intensity": psychology.get("emotional_intensity", 50),
        "novelty_score": psychology.get("novelty", 50),
        "shareability_score": attention_scores.get("shareability", psychology.get("share_likelihood", 50)),
        "replay_probability": attention_scores.get("rewatch_probability", psychology.get("replay_value", 50)),
        "comment_probability": attention_scores.get(
            "comment_likelihood", psychology.get("comment_likelihood", 50)
        ),
        "retention_prediction": psychology.get("retention_potential", 50),
        "hook_strength": attention_scores.get("first_3_second_hook", psychology.get("first_3_second_hook", 50)),
        "identity_resonance": attention_scores.get("identity_signaling", psychology.get("audience_identity", 50)),
        "visual_interest_score": _visual_interest(psychology, attention_scores),
        "narrative_tension": _narrative_tension(psychology, attention_scores),
    }
    # Belt-and-suspenders: guarantee every declared score field was set above.
    assert set(values) == set(SCORE_FIELDS), "build_report() field mismatch with SCORE_FIELDS"

    confidence = _confidence(candidate)
    recommendations = _recommendations(values, candidate)

    return BehavioralIntelligenceReport(**values, confidence=confidence, recommendations=recommendations)


def attach_report(candidate: dict) -> BehavioralIntelligenceReport:
    """Build the report and attach it to `candidate["behavioral_intelligence"]`.

    Called from `engines/psychology.py`, `engines/attention_graph.py`, and
    `engines/threat_detection.py` at the end of each of their `run()`
    methods so the report is available immediately after Psychology and
    refreshed (richer, more confident) as each later stage runs. Returns the
    dataclass too, for callers that want typed access without a second parse.
    """
    report = build_report(candidate)
    candidate["behavioral_intelligence"] = report.to_dict()
    return report
