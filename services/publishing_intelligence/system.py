"""Intelligence cycle orchestrator — publish packages → analytics → learn → improve."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.learning.predictions import predict_performance
from services.publishing_intelligence.analytics_layer import (
    build_intelligence_analytics_record,
    persist_intelligence_record,
)
from services.publishing_intelligence.business_intel import estimate_business_metrics
from services.publishing_intelligence.calibration import (
    apply_priors_to_prediction,
    build_calibration_report,
    recalibrate_priors,
)
from services.publishing_intelligence.creative_library import (
    recommend_creative_patterns,
    update_creative_library,
)
from services.publishing_intelligence.dashboard import build_studio_intelligence_dashboard
from services.publishing_intelligence.improvement import recommend_highest_impact_improvement
from services.publishing_intelligence.pipeline import SUPPORTED_PLATFORMS, build_complete_publish_packages

ROOT = Path(__file__).resolve().parents[2]
CYCLE_DIR = ROOT / "data" / "analytics" / "intelligence_cycles"


def run_intelligence_cycle(
    candidate: dict | None = None,
    *,
    platforms: list[str] | None = None,
    context: dict | None = None,
    quality_scores: dict | None = None,
    actual_metrics: dict | None = None,
    seed_demo_actuals: bool = False,
) -> dict[str, Any]:
    """Run Phases 1–7 for one production (or system-wide refresh if no candidate)."""
    context = dict(context or {})
    candidate = dict(candidate or {})
    topic = str(candidate.get("topic") or candidate.get("title") or context.get("topic") or "Educational short")
    platform = str(
        (platforms[0] if platforms else None)
        or candidate.get("platform")
        or context.get("platform")
        or "youtube_shorts"
    )

    # Phase 1 — publishing packages
    publish_packages = build_complete_publish_packages(
        candidate or {"topic": topic, "title": topic, "platform": platform},
        platforms=platforms or list(SUPPORTED_PLATFORMS),
        context=context,
    )

    # Predictions (with calibration priors)
    prediction = predict_performance(
        topic=topic,
        niche=str(candidate.get("niche") or candidate.get("category") or ""),
        platform=platform,
        runtime_sec=int(candidate.get("duration_sec") or publish_packages.get("platforms", {}).get(platform, {}).get("video", {}).get("duration_sec") or 60),
        psychology_score=float(candidate.get("psychology_score") or (candidate.get("psychology") or {}).get("viral_score") or 70),
        seo_score=float((candidate.get("seo_package") or {}).get("score") or 70),
        qa_score=float(candidate.get("quality_score") or 80),
    )
    prediction = apply_priors_to_prediction(prediction)
    predicted = {
        "hook_score": candidate.get("hook_score") or (quality_scores or {}).get("hook_strength"),
        "ctr": prediction.get("expected_ctr"),
        "completion": prediction.get("expected_audience_retention"),
        "retention": prediction.get("expected_audience_retention"),
        "shareability": (quality_scores or {}).get("shareability") or candidate.get("shareability"),
        "views": prediction.get("expected_views"),
        "expected_ctr": prediction.get("expected_ctr"),
        "expected_completion_rate": prediction.get("expected_audience_retention"),
    }

    actual = dict(actual_metrics or {})
    if seed_demo_actuals and not actual:
        # Deterministic demo actuals for offline calibration smoke (not real publish)
        ctr = float(predicted.get("ctr") or 5.0)
        actual = {
            "views": 12500,
            "impressions": 210000,
            "ctr": max(1.0, ctr * 0.92),
            "audience_retention": max(35.0, float(predicted.get("completion") or 50) * 0.95),
            "average_view_duration": 28.0,
            "likes": 640,
            "comments": 48,
            "shares": 92,
            "subscribers": 35,
            "watch_time": 12500 * 28,
        }

    # Phase 2 — analytics record
    record = build_intelligence_analytics_record(
        candidate={**candidate, "topic": topic, "platform": platform},
        platform=platform,
        publish_package=publish_packages,
        predicted=predicted,
        actual=actual or None,
        quality_scores=quality_scores or {},
    )
    persist_intelligence_record(record)

    # Phase 3 — calibration
    calibration = build_calibration_report()
    priors = recalibrate_priors(calibration)

    # Phase 4 — creative library
    library = update_creative_library()
    creative_recs = recommend_creative_patterns(topic=topic, platform=platform)

    # Phase 5 — one improvement
    improvement = recommend_highest_impact_improvement(
        quality_scores=quality_scores or {},
        calibration=calibration,
        topic=topic,
        platform=platform,
    )

    # Phase 6/7 — dashboard + BI
    dashboard = build_studio_intelligence_dashboard()
    business = estimate_business_metrics()

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0",
        "topic": topic,
        "platform": platform,
        "publish_packages": publish_packages,
        "prediction": prediction,
        "analytics_record_id": record.get("record_id"),
        "calibration": {
            "average_prediction_accuracy_pct": calibration.get("average_prediction_accuracy_pct"),
            "videos_calibrated": calibration.get("videos_calibrated"),
            "divergences": calibration.get("divergence_highlights"),
            "priors": priors,
        },
        "creative_recommendations": creative_recs,
        "highest_impact_improvement": improvement,
        "dashboard_snapshot": {
            "confidence_score": dashboard.get("confidence_score"),
            "average_quality_score": dashboard.get("average_quality_score"),
            "videos_published": dashboard.get("videos_published"),
        },
        "business_intelligence": business,
        "library_winners": len(library.get("winning_combinations") or []),
    }

    CYCLE_DIR.mkdir(parents=True, exist_ok=True)
    path = CYCLE_DIR / f"cycle_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    result["cycle_path"] = str(path)
    return result
