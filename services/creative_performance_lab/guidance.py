"""Pre-production guidance from validated learnings (recommendations only)."""

from __future__ import annotations

from typing import Any

from services.creative_performance_lab.knowledge import search_learnings


def guidance_for_production(
    *,
    topic: str = "",
    platform: str = "youtube_shorts",
    audience: str = "general_public",
    duration_sec: int = 45,
    content_category: str = "",
    narrator_profile: str = "professor",
    visual_style: str = "",
) -> dict[str, Any]:
    """Retrieve relevant learnings. Never force weak evidence into the pipeline."""
    learnings = search_learnings(topic=content_category or topic, platform=platform, audience=audience, limit=15)
    # Also pull publishing intelligence patterns (soft)
    pi_patterns = []
    try:
        from services.publishing_intelligence.creative_library import recommend_creative_patterns

        pi_patterns = recommend_creative_patterns(topic=topic, platform=platform, limit=5)
    except Exception:  # noqa: BLE001
        pi_patterns = []

    strong = [L for L in learnings if float(L.get("confidence") or 0) >= 0.55 and int(L.get("sample_size") or 0) >= 500]
    weak = [L for L in learnings if L not in strong]

    recommendations = []
    for L in strong:
        recommendations.append(
            {
                "priority": "high",
                "variable": L.get("creative_variable"),
                "suggestion": L.get("winning_pattern"),
                "avoid": L.get("losing_pattern"),
                "supporting_experiment_ids": L.get("supporting_experiment_ids"),
                "confidence": L.get("confidence"),
                "forced": False,
            }
        )
    for L in weak[:5]:
        recommendations.append(
            {
                "priority": "low",
                "variable": L.get("creative_variable"),
                "suggestion": L.get("winning_pattern"),
                "supporting_experiment_ids": L.get("supporting_experiment_ids"),
                "confidence": L.get("confidence"),
                "forced": False,
                "note": "Weak evidence — optional hint only",
            }
        )

    return {
        "topic": topic,
        "platform": platform,
        "audience": audience,
        "duration_sec": duration_sec,
        "narrator_profile": narrator_profile,
        "visual_style": visual_style,
        "recommendations": recommendations,
        "publishing_intelligence_patterns": pi_patterns,
        "policy": "Recommendations only — pipeline must not blindly force weak patterns",
    }
