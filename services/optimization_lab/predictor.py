"""Module 5 — Performance Predictor with explanations."""

from __future__ import annotations

from core.heuristics import clamp
from services.learning.predictions import predict_performance


def predict_variant_performance(candidate: dict, winner: dict) -> dict:
    """Estimate CTR, AVD, completion, share/like/comment/sub with CI + reasons."""
    axes = (winner or {}).get("axes") or {}
    scores = (winner or {}).get("scores") or {}
    topic = str(candidate.get("title") or candidate.get("topic") or axes.get("title") or "")
    platform = str(candidate.get("platform") or "youtube_shorts")

    base = predict_performance(
        topic=topic,
        niche=str(candidate.get("niche") or candidate.get("topic") or ""),
        platform=platform,
        runtime_sec=int(candidate.get("duration_sec") or 60),
        psychology_score=float(scores.get("psychology") or 0),
        seo_score=float(scores.get("seo") or 0),
        qa_score=float(scores.get("overall") or 0),
    )

    hook_q = float(scores.get("hook_quality") or 70)
    retention = float(scores.get("retention") or 70)
    entertainment = float(scores.get("entertainment") or 70)
    seo = float(scores.get("seo") or 70)

    ctr = clamp(float(base.get("expected_ctr") or 4.5) + (hook_q - 70) * 0.08 + (seo - 70) * 0.04, 1.0, 22.0)
    avd = clamp(float(base.get("expected_avg_view_duration_sec") or 35) + (retention - 70) * 0.25, 8.0, 90.0)
    completion = clamp(retention * 0.82 + entertainment * 0.1, 10.0, 95.0)
    share = clamp((entertainment * 0.4 + hook_q * 0.35 + retention * 0.25) / 100.0, 0.05, 0.9)
    like = clamp((entertainment * 0.45 + retention * 0.35 + scores.get("educational_value", 70) * 0.2) / 100.0, 0.08, 0.92)
    comment = clamp((hook_q * 0.4 + entertainment * 0.3 + (10 if "?" in str(axes.get("hook") or "") else 0)) / 100.0, 0.03, 0.7)
    subscribe = clamp((scores.get("educational_value", 70) * 0.35 + completion * 0.4 + retention * 0.25) / 100.0, 0.02, 0.55)

    reasons = []
    if hook_q >= 90:
        reasons.append("Strong hook quality lifts predicted CTR")
    if retention >= 90:
        reasons.append("High retention score supports completion rate")
    if seo >= 90:
        reasons.append("SEO packaging improves discoverability / CTR")
    if axes.get("thumbnail") in ("question_overlay", "stat_callout"):
        reasons.append(f"Thumbnail layout '{axes.get('thumbnail')}' historically aids clicks")
    if axes.get("narration") == "high_energy_host":
        reasons.append("High-energy narration supports share/like probability")
    if not reasons:
        reasons.append("Predictions blend historical analogs with variant scores")

    conf = float(base.get("confidence") or 0.45)
    conf = clamp(conf + (0.1 if scores.get("overall", 0) >= 95 else 0), 0.2, 0.95)

    return {
        "ctr_pct": round(ctr, 2),
        "average_view_duration_sec": round(avd, 1),
        "completion_rate_pct": round(completion, 1),
        "share_probability": round(share, 3),
        "like_probability": round(like, 3),
        "comment_probability": round(comment, 3),
        "subscriber_conversion": round(subscribe, 3),
        "confidence": round(conf, 3),
        "confidence_interval": {
            "ctr_pct": {"low": round(ctr * 0.75, 2), "high": round(ctr * 1.25, 2)},
            "completion_rate_pct": {"low": round(completion * 0.8, 1), "high": round(min(98, completion * 1.15), 1)},
        },
        "reasons": reasons,
        "base_prediction": {
            "expected_views": base.get("expected_views"),
            "expected_ctr": base.get("expected_ctr"),
            "confidence": base.get("confidence"),
        },
    }
