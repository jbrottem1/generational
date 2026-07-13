"""Predictive models — expected views, CTR, retention, virality, etc.

Heuristic Bayesian-style estimates from historical analytics + production
memory. Confidence grows with sample size; improves as more data arrives.
"""

from __future__ import annotations

from typing import Any

from services.analytics.models import performance_score
from services.analytics.store import get_analytics_store
from services.learning.productions import get_production_memory


def _avg(values: list[float], default: float = 0.0) -> float:
    return sum(values) / len(values) if values else default


def _ci(values: list[float], point: float) -> dict[str, float]:
    if len(values) < 2:
        return {"low": round(point * 0.7, 3), "high": round(point * 1.3, 3), "n": len(values)}
    mean = _avg(values)
    var = _avg([(v - mean) ** 2 for v in values])
    std = var ** 0.5
    return {
        "low": round(max(0.0, point - 1.28 * std), 3),
        "high": round(point + 1.28 * std, 3),
        "n": len(values),
    }


def _similar_analytics(topic: str, niche: str = "") -> list[dict]:
    topic_l = (topic or "").lower()
    niche_l = (niche or "").lower()
    tokens = [t for t in topic_l.split() if len(t) > 2]
    out = []
    for rec in get_analytics_store().list_records():
        hay = f"{rec.get('topic', '')} {rec.get('niche', '')} {rec.get('title', '')}".lower()
        if niche_l and niche_l in hay:
            out.append(rec)
            continue
        if tokens and sum(1 for t in tokens if t in hay) >= max(1, len(tokens) // 2):
            out.append(rec)
    return out


def predict_performance(
    *,
    topic: str,
    niche: str = "",
    platform: str = "youtube_shorts",
    runtime_sec: int = 60,
    psychology_score: float | None = None,
    seo_score: float | None = None,
    qa_score: float | None = None,
) -> dict[str, Any]:
    """Estimate expected platform outcomes before export."""
    similar = _similar_analytics(topic, niche)
    metrics_list = [r.get("metrics") or {} for r in similar if (r.get("metrics") or {})]
    productions = get_production_memory().find_similar(topic, limit=20)

    views = [float(m.get("views") or 0) for m in metrics_list]
    ctrs = [float(m.get("ctr") or 0) for m in metrics_list]
    watch = [float(m.get("average_view_duration_sec") or 0) for m in metrics_list]
    retention = [float(m.get("audience_retention") or 0) for m in metrics_list]
    shares = [float(m.get("shares") or 0) for m in metrics_list]
    subs = [float(m.get("subscriber_growth") or m.get("followers_gained") or 0) for m in metrics_list]
    scores = [float(performance_score(m)) for m in metrics_list]

    # Priors when history is thin
    prior_views = 1200 if platform in ("youtube_shorts", "tiktok", "instagram_reels") else 3500
    prior_ctr = 4.5
    prior_watch = min(runtime_sec * 0.55, float(runtime_sec))
    prior_ret = 45.0
    prior_shares = 25.0
    prior_subs = 8.0

    quality_boost = 1.0
    for score in (psychology_score, seo_score, qa_score):
        if score is not None:
            quality_boost += (float(score) - 70.0) / 400.0

    expected_views = _avg(views, prior_views) * quality_boost
    expected_ctr = _avg(ctrs, prior_ctr) * (1.0 + (quality_boost - 1.0) * 0.5)
    expected_watch = _avg(watch, prior_watch)
    expected_retention = _avg(retention, prior_ret) * (1.0 + (quality_boost - 1.0) * 0.4)
    expected_shares = _avg(shares, prior_shares) * quality_boost
    expected_subs = _avg(subs, prior_subs) * quality_boost
    expected_virality = min(100.0, _avg(scores, 55.0) * quality_boost)
    # Revenue placeholder — grows with views * RPM prior
    expected_revenue = expected_views * 0.002

    n = max(len(metrics_list), len(productions))
    confidence = min(95, 25 + n * 8)

    prediction = {
        "expected_views": int(round(expected_views)),
        "expected_ctr": round(expected_ctr, 2),
        "expected_watch_time_sec": round(expected_watch, 1),
        "expected_audience_retention": round(expected_retention, 1),
        "expected_shares": round(expected_shares, 1),
        "expected_revenue": round(expected_revenue, 4),
        "expected_subscriber_gain": round(expected_subs, 1),
        "expected_virality_score": round(expected_virality, 1),
        "confidence": confidence,
        "confidence_intervals": {
            "views": _ci(views or [prior_views], expected_views),
            "ctr": _ci(ctrs or [prior_ctr], expected_ctr),
            "watch_time_sec": _ci(watch or [prior_watch], expected_watch),
            "retention": _ci(retention or [prior_ret], expected_retention),
            "virality": _ci(scores or [55.0], expected_virality),
        },
        "samples": {"analytics": len(metrics_list), "productions": len(productions)},
        "platform": platform,
        "topic": topic,
    }
    return prediction
