"""Validate / reject weak opportunities before production."""

from __future__ import annotations

from typing import Any

from services.trend_opportunity.models import REJECTION_REASONS


def validate_opportunity(
    card: dict[str, Any],
    *,
    min_overall: float = 55.0,
    min_confidence: float = 0.45,
    max_production_count: int = 3,
    policy_categories: set[str] | None = None,
) -> dict[str, Any]:
    """Reject oversatured, weak edu, low curiosity, poor visual, overproduced, low confidence, policy."""
    reasons: list[str] = []
    scores = dict(card.get("scores") or {})
    analysis = dict(card.get("analysis") or {})
    overall = float(card.get("overall_opportunity_score") or 0)
    conf = float(card.get("confidence") or card.get("confidence_score") or 0.7)
    category = str(card.get("category") or "general").lower()
    prod_count = int(card.get("previous_productions_count") or card.get("production_count") or 0)

    policy = policy_categories or {
        "science",
        "education",
        "psychology",
        "space",
        "history",
        "health",
        "technology",
        "biology",
        "general",
    }

    if overall < min_overall:
        reasons.append("low_confidence")
    if conf < min_confidence:
        reasons.append("low_confidence")
    if float(scores.get("educational_score") or analysis.get("educational_value") or 0) < 45:
        reasons.append("weak_educational_value")
    if float(scores.get("curiosity_score") or analysis.get("curiosity_gap") or 0) < 40:
        reasons.append("low_curiosity")
    if float(scores.get("visual_score") or analysis.get("visual_potential") or 0) < 35:
        reasons.append("poor_visual_potential")
    # Low competition_score means saturated (competition_score = openness)
    if float(scores.get("competition_score") or 100) < 25:
        reasons.append("oversaturated")
    if float(analysis.get("competition") or 0) >= 85:
        reasons.append("oversaturated")
    if prod_count >= max_production_count:
        reasons.append("previously_overproduced")
    if category not in policy and category not in {c.lower() for c in policy}:
        # soft: allow biology under science umbrella
        if category not in ("biology", "physics", "chemistry", "nature", "marine"):
            reasons.append("outside_content_policy")

    reasons = sorted(set(r for r in reasons if r in REJECTION_REASONS or r))
    return {
        "ok": len(reasons) == 0,
        "accepted": len(reasons) == 0,
        "reject_reasons": reasons,
        "overall_opportunity_score": overall,
        "confidence": conf,
    }
