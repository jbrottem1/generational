"""Creative Excellence Scorecard — separate from engineering / ops quality."""

from __future__ import annotations

from typing import Any

from services.creative_excellence.models import CREATIVE_SCORE_DIMENSIONS
from services.creative_excellence.timeline import review_timeline_segments
from services.creative_excellence.v2_quality import build_v2_quality_block


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return float(max(low, min(high, value)))


def _psych(candidate: dict) -> dict:
    p = candidate.get("psychology") or {}
    if isinstance(p.get("dimensions"), dict):
        return p["dimensions"]
    return p if isinstance(p, dict) else {}


def build_creative_excellence_scorecard(
    candidate: dict | None = None,
    *,
    production_report: dict | None = None,
    export_validation: dict | None = None,
) -> dict[str, Any]:
    """Build the mission Creative Excellence score (attention craft)."""
    candidate = dict(candidate or {})
    report = dict(production_report or {})
    export = dict(export_validation or report.get("export_validation") or {})
    timeline = review_timeline_segments(candidate, report=report)
    segs = timeline["segments"]
    craft = timeline["craft"]
    psych = _psych(candidate)

    # Engineering Quality — contrast only (export/ops), not creative grade
    eng = 55.0
    if export.get("ok"):
        eng += 25
    if not (export.get("hard_fails") or []):
        eng += 10
    if report.get("platform_readiness"):
        eng += 5
    eng += min(5.0, float(report.get("stages_completed") or 0) / 4.0)
    engineering_quality = _clamp(eng, 0, 100)

    creative_quality = _clamp(
        0.35 * segs["first_3_seconds"]
        + 0.25 * segs["first_6_seconds"]
        + 0.15 * craft["visual_movement"]
        + 0.15 * craft["narration_energy"]
        + 0.10 * craft["curiosity"],
        0,
        100,
    )
    viewer_retention = _clamp(
        0.40 * segs["first_3_seconds"]
        + 0.25 * segs["first_15_seconds"]
        + 0.20 * segs["middle_pacing"]
        + 0.15 * segs["ending"],
        0,
        100,
    )
    educational_value = _clamp(
        float(report.get("educational_accuracy") or psych.get("educational_clarity") or 78),
        0,
        100,
    )
    entertainment = _clamp(
        0.35 * craft["viewer_emotion"]
        + 0.25 * craft["visual_movement"]
        + 0.25 * segs["first_6_seconds"]
        + 0.15 * float(report.get("shareability") or 70),
        0,
        100,
    )
    shareability = _clamp(
        float(report.get("shareability") or psych.get("share_likelihood") or craft["viewer_emotion"]),
        0,
        100,
    )
    emotional_impact = _clamp(craft["viewer_emotion"], 0, 100)
    curiosity = _clamp(craft["curiosity"], 0, 100)

    dimensions = {
        "engineering_quality": round(engineering_quality, 1),
        "creative_quality": round(creative_quality, 1),
        "viewer_retention": round(viewer_retention, 1),
        "educational_value": round(educational_value, 1),
        "entertainment": round(entertainment, 1),
        "shareability": round(shareability, 1),
        "emotional_impact": round(emotional_impact, 1),
        "curiosity": round(curiosity, 1),
    }

    # Creative Excellence overall IGNORES engineering_quality by design
    creative_keys = [k for k in CREATIVE_SCORE_DIMENSIONS if k != "engineering_quality"]
    creative_excellence_score = round(sum(dimensions[k] for k in creative_keys) / len(creative_keys), 1)

    # Viewer outcome probabilities (heuristic stop/finish/share/subscribe)
    stop = _clamp(segs["first_3_seconds"] / 100.0, 0, 1)
    finish = _clamp(viewer_retention / 100.0 * (0.85 + 0.15 * stop), 0, 1)
    share_p = _clamp(shareability / 100.0 * (0.55 + 0.45 * finish), 0, 1)
    subscribe_p = _clamp(
        (0.35 * emotional_impact + 0.35 * educational_value + 0.30 * finish * 100) / 100.0 * 0.55,
        0,
        1,
    )

    v2 = build_v2_quality_block(
        candidate,
        production_report=report,
        timeline=segs,
        craft=craft,
        dimensions=dimensions,
    )

    return {
        "version": "2.0.0",
        "creative_excellence_score": creative_excellence_score,
        "dimensions": dimensions,
        "v2_quality": v2,
        "timeline": segs,
        "craft": craft,
        "timeline_notes": timeline.get("notes") or {},
        "viewer_outcomes": {
            "would_stop_scrolling": round(stop, 3),
            "would_finish_watching": round(finish, 3),
            "would_share": round(share_p, 3),
            "would_subscribe": round(subscribe_p, 3),
            "judgments": {
                "would_stop_scrolling": stop >= 0.75,
                "would_finish_watching": finish >= 0.70,
                "would_share": share_p >= 0.45,
                "would_subscribe": subscribe_p >= 0.28,
            },
        },
        "engineering_vs_creative": {
            "engineering_quality": dimensions["engineering_quality"],
            "creative_excellence_score": creative_excellence_score,
            "v2_overall_professionalism": (v2.get("scores") or {}).get("overall_professionalism"),
            "note": "High engineering does not equal stop-scroll creative power.",
        },
    }
