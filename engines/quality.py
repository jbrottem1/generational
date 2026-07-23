"""Final Quality engine — stage 10: score, cite-check, and apply the publish gate.

Publishable content must pass ALL gates:
- Overall publish score >= threshold
- Research confidence >= research threshold
- Unsupported claims <= max allowed
- Claim confidence >= minimum (when citations required)
- Optional motivational gates (story structure, psychology progression, quote integrity)
  when niche is Motivation or the corresponding setting is enabled
"""

from __future__ import annotations

from core.constants import DEFAULT_PUBLISH_THRESHOLD
from core.log import get_logger, log_event
from engines.base import Engine
from engines.heuristics import clamp
from services.editorial import (
    beats_complete,
    is_motivational_niche,
    score_story_structure,
    score_viewer_progression,
)

logger = get_logger(__name__)

PUBLISH_WEIGHTS = {
    "opportunity": 0.16,
    "seo": 0.14,
    "psychology": 0.18,
    "retention": 0.14,
    "ctr": 0.10,
    "virality": 0.10,
    "story_structure": 0.10,
    "psychology_progression": 0.08,
}


def _flag(context: dict, key: str, default: bool) -> bool:
    """Read an optional bool gate flag; None/missing → default."""
    if key not in context or context.get(key) is None:
        return default
    return bool(context.get(key))


def _gate_settings(context: dict) -> dict:
    settings = context.get("research_settings") or {}
    niche = context.get("niche", "")
    motivational = is_motivational_niche(niche)
    return {
        "threshold": context.get("threshold", DEFAULT_PUBLISH_THRESHOLD),
        "research_confidence_threshold": float(settings.get("research_confidence_threshold", 0.45)),
        "max_unsupported_claims": int(settings.get("max_unsupported_claims", 2)),
        "min_claim_confidence": float(settings.get("min_claim_confidence", 0.5)),
        "citation_required": bool(settings.get("citation_required", True)),
        # Motivational gates default ON for Motivation niche. Explicit False in
        # context disables them; None / missing falls back to niche default.
        "require_story_structure": _flag(context, "require_story_structure", motivational),
        "require_psychology_progression": _flag(
            context, "require_psychology_progression", motivational
        ),
        "require_quote_integrity": _flag(
            context, "require_quote_integrity", motivational
        ),
        "story_structure_threshold": int(context.get("story_structure_threshold", 70)),
        "psychology_progression_threshold": int(context.get("psychology_progression_threshold", 65)),
    }


def _best_variant(idea: dict) -> dict:
    variants = idea.get("script_variants") or []
    if not variants:
        return {}
    return max(variants, key=lambda v: v.get("score", 0))


class QualityEngine(Engine):
    key = "quality"
    label = "Quality"
    icon = "✅"
    description = "Final quality scoring and multi-factor publish gate."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        selected = context.get("selected_ideas", [])
        gates = _gate_settings(context)
        threshold = gates["threshold"]
        opportunity = context.get("research", {}).get("opportunity_score", 60)
        research_confidence = context.get("research", {}).get("research_confidence", 0.0)

        publishable_count = 0
        held_reasons: dict[str, int] = {}

        for idea in selected:
            psychology = idea.get("psychology", {})
            psychology_score = idea.get("psychology_score", 50)
            seo = idea.get("seo_score", 50)
            critic = idea.get("critique", {}).get("score", 70)
            citations = idea.get("citations", {})
            best = _best_variant(idea)
            story_beats = idea.get("story_beats") or best.get("story_beats") or {}
            emotional_progression = (
                idea.get("emotional_progression")
                or best.get("emotional_progression")
                or []
            )
            structure = score_story_structure(story_beats, idea.get("script", ""))
            progression = score_viewer_progression(
                emotional_progression,
                f"{idea.get('hook', '')} {idea.get('script', '')}",
            )
            idea["story_structure"] = structure
            idea["psychology_progression"] = progression
            if story_beats and not idea.get("story_beats"):
                idea["story_beats"] = story_beats

            # When motivational structure gates are off, blend neutral mid-scores so
            # non-Motivation niches are not penalized for empty story_beats.
            structure_for_publish = (
                structure["score"] if gates["require_story_structure"] else max(structure["score"], 70)
            )
            progression_for_publish = (
                progression["score"]
                if gates["require_psychology_progression"]
                else max(progression["score"], 70)
            )

            retention = clamp(
                0.40 * psychology.get("retention_potential", 50)
                + 0.20 * psychology.get("dopamine_curve", 50)
                + 0.15 * psychology.get("replay_value", 50)
                + 0.25 * critic
            )
            ctr = clamp(
                0.35 * psychology.get("curiosity_gap", 50)
                + 0.25 * psychology.get("first_3_second_hook", 50)
                + 0.20 * psychology.get("surprise", 50)
                + 0.20 * seo
            )
            # "Virality" isolates the pure spread/engagement signal (sharing,
            # commenting, identity, community, bounded controversy) from
            # click-through and watch-through, so the publish gate rewards
            # concepts built to spread — not just to be watched once.
            virality = clamp(
                0.30 * psychology.get("share_likelihood", 50)
                + 0.25 * psychology.get("comment_likelihood", 50)
                + 0.20 * psychology.get("audience_identity", 50)
                + 0.15 * psychology.get("community_appeal", 50)
                + 0.10 * psychology.get("controversy", 50)
            )
            publish = clamp(
                PUBLISH_WEIGHTS["opportunity"] * opportunity
                + PUBLISH_WEIGHTS["seo"] * seo
                + PUBLISH_WEIGHTS["psychology"] * psychology_score
                + PUBLISH_WEIGHTS["retention"] * retention
                + PUBLISH_WEIGHTS["ctr"] * ctr
                + PUBLISH_WEIGHTS["virality"] * virality
                + PUBLISH_WEIGHTS["story_structure"] * structure_for_publish
                + PUBLISH_WEIGHTS["psychology_progression"] * progression_for_publish
            )

            unsupported = citations.get("unsupported_claims", [])
            quote_flags = citations.get("quote_integrity_flags", [])
            claim_confidence = citations.get("claim_confidence", 0) / 100.0
            citation_count = citations.get("citation_count", 0)

            score_ok = publish >= threshold
            research_ok = research_confidence >= gates["research_confidence_threshold"]
            unsupported_ok = len(unsupported) <= gates["max_unsupported_claims"]
            claim_ok = claim_confidence >= gates["min_claim_confidence"]
            citation_ok = (not gates["citation_required"]) or citation_count > 0
            structure_ok = (not gates["require_story_structure"]) or (
                beats_complete(story_beats) and structure["score"] >= gates["story_structure_threshold"]
            )
            progression_ok = (not gates["require_psychology_progression"]) or (
                progression["score"] >= gates["psychology_progression_threshold"]
            )
            quote_ok = (not gates["require_quote_integrity"]) or not quote_flags

            publishable = (
                score_ok
                and research_ok
                and unsupported_ok
                and claim_ok
                and citation_ok
                and structure_ok
                and progression_ok
                and quote_ok
            )

            gate_failures = []
            if not score_ok:
                gate_failures.append("publish_score")
            if not research_ok:
                gate_failures.append("research_confidence")
            if not unsupported_ok:
                gate_failures.append("unsupported_claims")
            if not claim_ok:
                gate_failures.append("claim_confidence")
            if not citation_ok:
                gate_failures.append("citation_required")
            if not structure_ok:
                gate_failures.append("story_structure")
            if not progression_ok:
                gate_failures.append("psychology_progression")
            if not quote_ok:
                gate_failures.append("quote_integrity")

            for reason in gate_failures:
                held_reasons[reason] = held_reasons.get(reason, 0) + 1

            idea["scores"] = {
                "opportunity": opportunity,
                "seo": seo,
                "psychology": psychology_score,
                "retention": retention,
                "ctr": ctr,
                "virality": virality,
                "story_structure": structure["score"],
                "psychology_progression": progression["score"],
                "publish": publish,
                "research_confidence": int(research_confidence * 100),
                "claim_confidence": citations.get("claim_confidence", 0),
            }
            idea["publishable"] = publishable
            idea["gate_failures"] = gate_failures
            publishable_count += publishable

        log_event(
            logger,
            "quality.gated",
            scored=len(selected),
            publishable=publishable_count,
            threshold=threshold,
            research_confidence=research_confidence,
        )
        return {
            "ideas": selected,
            "quality_summary": {
                "threshold": threshold,
                "research_confidence_threshold": gates["research_confidence_threshold"],
                "publishable": publishable_count,
                "held": len(selected) - publishable_count,
                "held_reasons": held_reasons,
                "autonomous_publishing_enabled": bool(
                    context.get("autonomous_publishing_enabled", False)
                ),
            },
        }
