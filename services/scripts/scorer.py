"""Script variant scorer — deterministic 0-100 quality scoring and ranking.

Every generated variant is scored across six weighted factors (hook power,
retention engineering, emotional arc, story substance, platform fit, CTA
strength) and the variants are ranked best-first. Weights are data, not
code — the future Learning Engine can tune them from real watch-time and
CTR results without touching scoring logic.

Scoring reuses the same word-bank heuristics that power the Psychology and
Critic engines, so a script that scores well here also survives the
downstream adversarial review.
"""

from __future__ import annotations

from engines.heuristics import (
    CURIOSITY_WORDS,
    EMOTION_WORDS,
    SURPRISE_WORDS,
    clamp,
    count_hits,
    has_digit,
    sentences,
    stable_jitter,
)
from services.scripts.models import ScriptVariant
from services.scripts.platforms import get_platform_spec

VARIANT_SCORE_WEIGHTS = {
    "hook_power": 0.24,
    "retention_engineering": 0.22,
    "emotional_arc": 0.14,
    "story_substance": 0.16,
    "platform_fit": 0.14,
    "cta_strength": 0.10,
}


def _hook_power(variant: ScriptVariant) -> int:
    hook = variant.hook
    words = hook.split()
    score = 40
    if count_hits(hook, CURIOSITY_WORDS + SURPRISE_WORDS):
        score += 18
    if "?" in hook or "—" in hook:
        score += 8
    if len(words) <= 16:
        score += 12
    if variant.pattern_interrupt.strip():
        score += 10
    if variant.curiosity_loop.strip():
        score += 8
    return clamp(score)


def _retention_engineering(variant: ScriptVariant) -> int:
    score = 34
    checkpoints = variant.retention_checkpoints or []
    score += min(len(checkpoints), 3) * 12
    if "you" in variant.full_script.lower():
        score += 12
    if variant.curiosity_loop.strip():
        score += 8
    long_sentences = [s for s in sentences(variant.core_story) if len(s.split()) > 28]
    if long_sentences:
        score -= 10 * min(len(long_sentences), 2)
    return clamp(score)


def _emotional_arc(variant: ScriptVariant) -> int:
    arc = variant.emotional_progression or []
    score = 36 + min(len(arc), 5) * 8
    if len(set(arc)) == len(arc) and len(arc) >= 3:
        score += 10  # distinct beats — a real progression, not a mood repeated
    if count_hits(variant.core_story, EMOTION_WORDS):
        score += 8
    return clamp(score)


def _story_substance(variant: ScriptVariant) -> int:
    story = variant.core_story
    score = 36
    if has_digit(story):
        score += 12
    hits = count_hits(story, ["research", "study", "data", "evidence", "found", "shows"])
    score += min(hits, 3) * 8
    if len(story.split()) >= 40:
        score += 10
    if variant.seo_keywords:
        keyword_hits = sum(1 for kw in variant.seo_keywords[:5] if kw in story.lower())
        score += min(keyword_hits, 3) * 4
    return clamp(score)


def _platform_fit(variant: ScriptVariant) -> int:
    spec = get_platform_spec(variant.platform)
    runtime = variant.estimated_runtime_sec
    if spec.min_runtime_sec <= runtime <= spec.max_runtime_sec:
        return clamp(88 + stable_jitter(variant.variant_id, span=10))
    # Outside the window: penalize proportionally to how far off it is.
    edge = spec.min_runtime_sec if runtime < spec.min_runtime_sec else spec.max_runtime_sec
    deviation = abs(runtime - edge) / max(edge, 1)
    return clamp(85 - deviation * 120)


def _cta_strength(variant: ScriptVariant) -> int:
    cta = variant.call_to_action
    score = 40
    if cta.strip():
        score += 15
    action_verbs = ["follow", "subscribe", "share", "comment", "save", "repost", "tag"]
    score += min(count_hits(cta, action_verbs), 2) * 12
    if len(cta.split()) <= 22:
        score += 8
    return clamp(score)


def score_variant(variant: ScriptVariant) -> ScriptVariant:
    """Score one variant in place: per-factor breakdown + weighted total."""
    breakdown = {
        "hook_power": _hook_power(variant),
        "retention_engineering": _retention_engineering(variant),
        "emotional_arc": _emotional_arc(variant),
        "story_substance": _story_substance(variant),
        "platform_fit": _platform_fit(variant),
        "cta_strength": _cta_strength(variant),
    }
    total = sum(VARIANT_SCORE_WEIGHTS[name] * value for name, value in breakdown.items())
    variant.score_breakdown = breakdown
    variant.score = clamp(total + stable_jitter(variant.full_script, span=4))
    return variant


def rank_variants(variants: "list[ScriptVariant]") -> "list[ScriptVariant]":
    """Score every variant and return them best-first."""
    for variant in variants:
        score_variant(variant)
    return sorted(variants, key=lambda v: v.score, reverse=True)
