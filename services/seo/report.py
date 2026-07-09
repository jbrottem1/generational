"""Optimization Report — the ten headline metrics of the SEO stage.

One report per content item. Every metric is 0-100 and deterministic;
`overall_optimization_score` is the weighted blend the Publishing Engine
and dashboards read first.
"""

from __future__ import annotations

from engines.heuristics import clamp, weighted_blend
from services.seo.models import KEYWORD_CLASSES

_EVERGREEN_ARCHETYPES = {"educational": 18, "scientific": 15, "question": 12, "story": 10}
_TIMELY_ARCHETYPES = {"breaking_news": -20, "shock": -8}

_OVERALL_WEIGHTS = {
    "seo_score": 0.18,
    "ctr_prediction": 0.18,
    "retention_prediction": 0.14,
    "competition_score": 0.08,
    "trend_strength": 0.10,
    "evergreen_score": 0.06,
    "localization_readiness": 0.08,
    "publishing_readiness": 0.10,
    "confidence": 0.08,
}


def _evergreen_score(titles: "list[dict]", keyword_package: dict) -> int:
    score = 50
    top = titles[0] if titles else {}
    score += _EVERGREEN_ARCHETYPES.get(top.get("archetype", ""), 0)
    score += _TIMELY_ARCHETYPES.get(top.get("archetype", ""), 0)
    score += min(len(keyword_package.get("question", [])), 4) * 4
    score += min(len(keyword_package.get("long_tail", [])), 4) * 2
    return clamp(score)


def build_optimization_report(
    titles: "list[dict]",
    keyword_package: dict,
    description_package: dict,
    hashtag_package: dict,
    thumbnails: "list[dict]",
    localization: dict,
    windows: "list[dict]",
    signals: "dict | None" = None,
) -> dict:
    """The ten-metric Optimization Report (see OPTIMIZATION_REPORT_FIELDS).

    `signals` carries upstream scores: base_seo_score, retention_prediction,
    competition_score (higher = more open field), trend_strength.
    """
    signals = signals or {}
    top_title = titles[0] if titles else {}
    top_thumbnail = thumbnails[0] if thumbnails else {}

    keyword_coverage = sum(1 for cls in KEYWORD_CLASSES if keyword_package.get(cls))
    seo_score = clamp(
        top_title.get("seo_score", 40) * 0.5
        + keyword_coverage / len(KEYWORD_CLASSES) * 100 * 0.3
        + (100 if description_package.get("long_description") else 0) * 0.1
        + signals.get("base_seo_score", 50) * 0.1
    )
    # Thumbnail click probability is a percentage (~0-10); rescale to 0-100.
    thumb_ctr = clamp(float(top_thumbnail.get("click_probability_pct", 0.0)) * 10)
    ctr_prediction = clamp(
        top_title.get("ctr_prediction", 40) * (0.6 if thumbnails else 1.0)
        + (thumb_ctr * 0.4 if thumbnails else 0)
    )
    retention_prediction = clamp(int(signals.get("retention_prediction", 50)))
    competition_score = clamp(int(signals.get("competition_score", 50)))
    trend_strength = clamp(int(signals.get("trend_strength", 50)))
    evergreen_score = _evergreen_score(titles, keyword_package)
    localization_readiness = clamp(int(localization.get("readiness", 0)))

    components_present = [
        bool(titles),
        bool(keyword_package.get("primary")),
        bool(description_package.get("long_description")),
        bool(hashtag_package),
        bool(thumbnails),
        bool(windows),
        bool(localization.get("targets")),
    ]
    publishing_readiness = clamp(int(round(sum(components_present) / len(components_present) * 100)), low=0)

    confidences = (
        [t.get("confidence", 0) for t in titles[:3]]
        + [w.get("confidence", 0) for w in windows[:3]]
    )
    confidence = clamp(int(round(sum(confidences) / len(confidences)))) if confidences else 40

    metrics = {
        "seo_score": seo_score,
        "ctr_prediction": ctr_prediction,
        "retention_prediction": retention_prediction,
        "competition_score": competition_score,
        "trend_strength": trend_strength,
        "evergreen_score": evergreen_score,
        "localization_readiness": localization_readiness,
        "publishing_readiness": publishing_readiness,
        "confidence": confidence,
    }
    metrics["overall_optimization_score"] = weighted_blend(metrics, _OVERALL_WEIGHTS)
    return metrics
