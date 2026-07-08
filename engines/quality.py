"""Final Quality engine — stage 10: score, cite-check, and apply the publish gate.

Publishable content must pass ALL gates:
- Overall publish score >= threshold
- Research confidence >= research threshold
- Unsupported claims <= max allowed
- Claim confidence >= minimum (when citations required)
"""

from __future__ import annotations

from core.constants import DEFAULT_PUBLISH_THRESHOLD
from core.log import get_logger, log_event
from engines.base import Engine
from engines.heuristics import clamp

logger = get_logger(__name__)

PUBLISH_WEIGHTS = {
    "opportunity": 0.20,
    "seo": 0.20,
    "psychology": 0.25,
    "retention": 0.20,
    "ctr": 0.15,
}


def _gate_settings(context: dict) -> dict:
    settings = context.get("research_settings") or {}
    return {
        "threshold": context.get("threshold", DEFAULT_PUBLISH_THRESHOLD),
        "research_confidence_threshold": float(settings.get("research_confidence_threshold", 0.45)),
        "max_unsupported_claims": int(settings.get("max_unsupported_claims", 2)),
        "min_claim_confidence": float(settings.get("min_claim_confidence", 0.5)),
        "citation_required": bool(settings.get("citation_required", True)),
    }


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

            retention = clamp(0.55 * psychology.get("retention_potential", 50) + 0.45 * critic)
            ctr = clamp(
                0.5 * psychology.get("curiosity", 50)
                + 0.3 * psychology.get("surprise", 50)
                + 0.2 * seo
            )
            publish = clamp(
                PUBLISH_WEIGHTS["opportunity"] * opportunity
                + PUBLISH_WEIGHTS["seo"] * seo
                + PUBLISH_WEIGHTS["psychology"] * psychology_score
                + PUBLISH_WEIGHTS["retention"] * retention
                + PUBLISH_WEIGHTS["ctr"] * ctr
            )

            unsupported = citations.get("unsupported_claims", [])
            claim_confidence = citations.get("claim_confidence", 0) / 100.0
            citation_count = citations.get("citation_count", 0)

            score_ok = publish >= threshold
            research_ok = research_confidence >= gates["research_confidence_threshold"]
            unsupported_ok = len(unsupported) <= gates["max_unsupported_claims"]
            claim_ok = claim_confidence >= gates["min_claim_confidence"]
            citation_ok = (not gates["citation_required"]) or citation_count > 0

            publishable = score_ok and research_ok and unsupported_ok and claim_ok and citation_ok

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

            for reason in gate_failures:
                held_reasons[reason] = held_reasons.get(reason, 0) + 1

            idea["scores"] = {
                "opportunity": opportunity,
                "seo": seo,
                "psychology": psychology_score,
                "retention": retention,
                "ctr": ctr,
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
            },
        }
