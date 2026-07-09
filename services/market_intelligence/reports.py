"""Market Intelligence reporting — one report per run, executive first.

Builds the MARKET_REPORT_FIELDS dict: executive summary, opportunity
report, trend forecast report, competition report, ROI report, and
platform opportunity report, plus quality findings and the learning
calibration applied. Diagnostics only — building a report never mutates
state and never raises.
"""

from __future__ import annotations

from datetime import datetime, timezone

from services.market_intelligence.models import (
    MARKET_INTELLIGENCE_VERSION,
    MARKET_REPORT_FIELDS,  # noqa: F401 - re-exported contract
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _average(values) -> int:
    values = list(values)
    return int(round(sum(values) / len(values))) if values else 0


def _top(opportunities: "list[dict]", key: str, n: int = 3) -> "list[dict]":
    ranked = sorted(opportunities, key=lambda o: o.get(key, 0), reverse=True)
    return [
        {"topic": o.get("topic", ""), "platform": o.get("platform", ""), key: o.get(key, 0)}
        for o in ranked[:n]
    ]


def _executive_summary(opportunities: "list[dict]", validation: dict) -> dict:
    best = opportunities[0] if opportunities else {}
    return {
        "headline": (
            f"Top opportunity: '{best.get('topic', 'none')}' on "
            f"{best.get('platform', '-')} (priority {best.get('priority', 0)}/100)"
            if best else "No opportunities passed the quality gate this run."
        ),
        "opportunities_identified": len(opportunities),
        "signals_dropped": validation.get("dropped_total", 0),
        "average_priority": _average(o.get("priority", 0) for o in opportunities),
        "average_roi": _average(o.get("roi_estimate", 0) for o in opportunities),
        "average_confidence": round(
            sum(o.get("confidence", 0) for o in opportunities) / len(opportunities), 2
        ) if opportunities else 0.0,
        "immediate_actions": sum(
            1 for o in opportunities
            if "publish_immediately" in o.get("strategic_actions", [])
        ),
        "recommended_next_step": (
            f"Produce '{best.get('topic', '')}' as "
            f"{best.get('recommended_content_type', 'short_form')} within window "
            f"{best.get('recommended_publish_window', {}).get('start', '-')} → "
            f"{best.get('recommended_publish_window', {}).get('end', '-')}"
            if best else "Widen discovery scope or lower thresholds."
        ),
    }


def _histogram(values) -> dict:
    counts: dict = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def build_market_report(
    opportunities: "list[dict]",
    validation: "dict | None" = None,
    calibration: "dict | None" = None,
    topic: str = "",
    category: str = "general",
) -> dict:
    """One MARKET_REPORT_FIELDS dict — never raises."""
    validation = validation or {}
    calibration = calibration or {}
    try:
        forecasts = [o.get("forecast", {}) for o in opportunities]
        competitions = [o.get("competition", {}) for o in opportunities]
        return {
            "report_version": MARKET_INTELLIGENCE_VERSION,
            "generated_at": _now_iso(),
            "topic": topic,
            "category": category,
            "executive_summary": _executive_summary(opportunities, validation),
            "opportunity_report": {
                "count": len(opportunities),
                "by_nature": _histogram(o.get("content_nature", "") for o in opportunities),
                "by_platform": _histogram(o.get("platform", "") for o in opportunities),
                "by_content_type": _histogram(
                    o.get("recommended_content_type", "") for o in opportunities
                ),
                "top_priority": _top(opportunities, "priority"),
            },
            "trend_forecast_report": {
                "average_virality": _average(f.get("virality_potential", 0) for f in forecasts),
                "average_lifespan_days": _average(f.get("lifespan_days", 0) for f in forecasts),
                "average_confidence": round(
                    sum(f.get("forecast_confidence", 0) for f in forecasts) / len(forecasts), 2
                ) if forecasts else 0.0,
                "longevity": _histogram(f.get("expected_longevity", "") for f in forecasts),
                "trajectories": _histogram(f.get("trajectory", "") for f in forecasts),
                "model": forecasts[0].get("model", "momentum") if forecasts else "momentum",
            },
            "competition_report": {
                "average_difficulty": _average(
                    c.get("market_difficulty", 0) for c in competitions
                ),
                "average_content_gap": _average(
                    c.get("content_gap_score", 0) for c in competitions
                ),
                "levels": _histogram(f.get("competition_level", "") for f in forecasts),
                "best_gaps": _top(
                    [
                        {**o, "content_gap_score": o.get("competition", {}).get("content_gap_score", 0)}
                        for o in opportunities
                    ],
                    "content_gap_score",
                ),
            },
            "roi_report": {
                "average_roi": _average(o.get("roi_estimate", 0) for o in opportunities),
                "highest_roi": _top(opportunities, "roi_estimate"),
                "roi_calibration_applied": calibration.get("roi_calibration", 1.0),
            },
            "platform_opportunity_report": {
                platform: {
                    "count": len(group),
                    "average_priority": _average(o.get("priority", 0) for o in group),
                    "best_topic": group[0].get("topic", "") if group else "",
                }
                for platform, group in _group_by_platform(opportunities).items()
            },
            "quality": dict(validation),
            "learning": {
                "evidence_records": calibration.get("evidence_records", 0),
                "historical_performance": calibration.get("historical_performance", 0.5),
                "roi_calibration": calibration.get("roi_calibration", 1.0),
                "confidence_calibration": calibration.get("confidence_calibration", 1.0),
            },
        }
    except Exception as exc:  # noqa: BLE001 - reporting must never break the run
        return {
            "report_version": MARKET_INTELLIGENCE_VERSION,
            "generated_at": _now_iso(),
            "topic": topic,
            "category": category,
            "error": f"Market report generation failed safely: {exc}",
            "executive_summary": {},
            "opportunity_report": {},
            "trend_forecast_report": {},
            "competition_report": {},
            "roi_report": {},
            "platform_opportunity_report": {},
            "quality": dict(validation),
            "learning": {},
        }


def _group_by_platform(opportunities: "list[dict]") -> "dict[str, list[dict]]":
    groups: "dict[str, list[dict]]" = {}
    for opportunity in sorted(
        opportunities, key=lambda o: o.get("priority", 0), reverse=True
    ):
        groups.setdefault(opportunity.get("platform", ""), []).append(opportunity)
    return groups
