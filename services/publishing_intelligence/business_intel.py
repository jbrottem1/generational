"""Phase 7 — Business Intelligence projections (until real monetization data lands)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.analytics.store import get_analytics_store
from services.publishing_intelligence.analytics_layer import list_intelligence_records


def estimate_business_metrics(
    *,
    productions_per_week: float = 14.0,
    avg_cost_per_video_usd: float = 2.5,
    avg_minutes_per_video: float = 18.0,
    automation_rate: float = 0.92,
    manual_edit_minutes: float = 4.0,
    rpm_usd: float = 2.0,
    avg_views_per_video: float | None = None,
) -> dict[str, Any]:
    """Estimate cost, speed, and revenue — projections until real data dominates."""
    records = list(get_analytics_store().list_records())
    intel = list_intelligence_records(limit=200)
    views = []
    for r in records:
        m = r.get("metrics") or {}
        if m.get("views") is not None:
            views.append(float(m["views"]))
    for r in intel:
        m = r.get("actual_metrics") or {}
        if m.get("views") is not None:
            views.append(float(m["views"]))
    if avg_views_per_video is None:
        avg_views_per_video = sum(views) / len(views) if views else 8_000.0

    monthly_output = productions_per_week * 4.3
    monthly_cost = monthly_output * avg_cost_per_video_usd
    monthly_views = monthly_output * avg_views_per_video
    revenue_per_thousand = rpm_usd
    expected_monthly_revenue = (monthly_views / 1000.0) * revenue_per_thousand
    expected_annual_revenue = expected_monthly_revenue * 12
    time_per_video = avg_minutes_per_video
    automation = max(0.0, min(1.0, automation_rate))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0",
        "mode": "projection" if not views else "projection_with_partial_actuals",
        "production_cost_usd_per_video": round(avg_cost_per_video_usd, 2),
        "time_per_video_minutes": round(time_per_video, 1),
        "automation_rate": round(automation, 3),
        "manual_editing_time_minutes": round(manual_edit_minutes, 1),
        "expected_revenue_usd_per_video": round((avg_views_per_video / 1000.0) * rpm_usd, 2),
        "revenue_per_thousand_views_usd": round(revenue_per_thousand, 2),
        "estimated_monthly_output": round(monthly_output, 1),
        "estimated_monthly_cost_usd": round(monthly_cost, 2),
        "estimated_monthly_earnings_usd": round(expected_monthly_revenue, 2),
        "estimated_annual_earnings_usd": round(expected_annual_revenue, 2),
        "avg_views_assumption": round(avg_views_per_video, 1),
        "sample_published_with_views": len(views),
        "notes": [
            "RPM/earnings are projections until monetization APIs provide real RPM.",
            "Costs assume local-first compute + provider TTS/API spend averages.",
        ],
    }
