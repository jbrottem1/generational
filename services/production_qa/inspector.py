"""Inspect a production / idea and produce the unified PQA report."""

from __future__ import annotations

from typing import Any

from services.production_qa.categories import CATEGORY_SCORERS, score_platform_compliance
from services.production_qa.models import (
    CATEGORY_PASS_THRESHOLD,
    CRITICAL_BLOCK_FLOOR,
    OVERALL_PASS_THRESHOLD,
    PQA_CATEGORIES,
    ProductionQAReport,
)
from services.production_qa.revision import CRITICAL_CATEGORIES, build_revision_requests


def _overall(categories: dict) -> int:
    if not categories:
        return 0
    weights = {
        "research_accuracy": 1.15,
        "evidence": 1.15,
        "visuals": 1.05,
        "typography": 0.9,
        "annotations": 1.0,
        "cinematography": 1.0,
        "retention": 1.1,
        "render_quality": 1.1,
        "optimization": 1.05,
        "audio": 1.0,
        "narration": 1.05,
        "synchronization": 1.0,
        "educational_value": 1.15,
        "psychology": 0.95,
        "seo": 0.85,
        "platform_compliance": 0.9,
    }
    total_w = 0.0
    total = 0.0
    for key, cat in categories.items():
        w = weights.get(key, 1.0)
        total += cat.score * w
        total_w += w
    return int(round(total / max(total_w, 1.0)))


def decide(
    overall: int,
    categories: dict,
    hard_fails: list[str],
) -> str:
    if hard_fails:
        return "BLOCK_EXPORT"
    critical_fail = any(
        cat.score < CRITICAL_BLOCK_FLOOR
        for key, cat in categories.items()
        if key in CRITICAL_CATEGORIES
    )
    if critical_fail:
        return "BLOCK_EXPORT"
    below = [c for c in categories.values() if c.score < CATEGORY_PASS_THRESHOLD]
    if overall >= OVERALL_PASS_THRESHOLD and not below:
        return "APPROVE"
    if below or overall < OVERALL_PASS_THRESHOLD:
        return "REQUEST_REVISION"
    return "APPROVE"


def inspect_production(item: dict, context: dict | None = None) -> ProductionQAReport:
    """Evaluate one candidate/idea/production package."""
    context = context or {}
    categories = {}
    hard_fails: list[str] = []
    warnings: list[str] = []
    sources_checked: list[str] = []

    for key in PQA_CATEGORIES:
        scorer = CATEGORY_SCORERS[key]
        cat = scorer(item, context)
        categories[key] = cat
        if cat.key == "research_accuracy":
            sources_checked = list(cat.details.get("sources_checked") or [])
        if cat.score < CRITICAL_BLOCK_FLOOR and cat.key in CRITICAL_CATEGORIES:
            hard_fails.append(f"{cat.label} critically low ({cat.score})")
        warnings.extend(cat.issues)

    platform_cat, platforms = score_platform_compliance(item, context)
    categories["platform_compliance"] = platform_cat
    warnings.extend(platform_cat.issues)

    # Concept-level publishable=False from QualityEngine is advisory hard signal
    if item.get("publishable") is False and item.get("gate_failures"):
        hard_fails.append("QualityEngine publish gate failed: " + ", ".join(item.get("gate_failures") or []))

    overall = _overall(categories)
    decision = decide(overall, categories, hard_fails)
    revisions = build_revision_requests(categories, hard_fails=hard_fails)

    # If anything below 90, never APPROVE
    if any(c.score < CATEGORY_PASS_THRESHOLD for c in categories.values()) and decision == "APPROVE":
        decision = "REQUEST_REVISION"

    psych_details = (categories.get("psychology").details if categories.get("psychology") else {}) or {}
    predicted = dict(psych_details.get("predicted_metrics") or {})

    return ProductionQAReport(
        title=str(item.get("title") or item.get("topic") or context.get("subject") or ""),
        idea_id=str(item.get("id") or item.get("idea_id") or item.get("slug") or ""),
        overall_score=overall,
        decision=decision,  # type: ignore[arg-type]
        categories=categories,
        platform_ready=platforms,
        revision_requests=revisions,
        hard_fails=hard_fails,
        warnings=list(dict.fromkeys(warnings))[:40],
        predicted_metrics=predicted,
        sources_checked=sources_checked,
    )


def inspect_many(items: list[dict], context: dict | None = None) -> list[ProductionQAReport]:
    return [inspect_production(item, context) for item in items]
