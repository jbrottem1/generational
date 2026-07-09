"""Content roadmap — the department's publishing plan across time horizons.

From one validated, ranked opportunity batch it produces:

- daily roadmap        (act today — highest priority, urgent windows)
- weekly roadmap       (this week's plan)
- monthly roadmap      (the month's slate)
- quarterly strategy   (category/market direction, localization targets)
- four queues          (evergreen · trending · high ROI · low competition)
- a publishing calendar (dated entries the Publishing Engine can consume)

Everything is structured data (ROADMAP_FIELDS) — never content.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from services.market_intelligence.config import (
    MarketIntelligenceConfig,
    get_market_intelligence_config,
)
from services.market_intelligence.evergreen import LONG_LIVED_NATURES
from services.market_intelligence.strategy import localization_targets


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _slot(opportunity: dict) -> dict:
    """A compact roadmap slot for one opportunity dict."""
    return {
        "opportunity_id": opportunity.get("opportunity_id", ""),
        "topic": opportunity.get("topic", ""),
        "platform": opportunity.get("platform", ""),
        "content_type": opportunity.get("recommended_content_type", "short_form"),
        "content_nature": opportunity.get("content_nature", "trending"),
        "priority": opportunity.get("priority", 0),
        "roi_estimate": opportunity.get("roi_estimate", 0),
        "publish_window": dict(opportunity.get("recommended_publish_window", {})),
        "strategic_actions": list(opportunity.get("strategic_actions", [])),
    }


def _window_start_days(opportunity: dict) -> int:
    return int(opportunity.get("recommended_publish_window", {}).get("start_in_days", 0))


def _queues(opportunities: "list[dict]", size: int) -> dict:
    evergreen = [o for o in opportunities if o.get("content_nature") in LONG_LIVED_NATURES]
    trending = [o for o in opportunities if o.get("content_nature") in ("trending", "news")]
    high_roi = sorted(opportunities, key=lambda o: o.get("roi_estimate", 0), reverse=True)
    low_competition = sorted(
        opportunities, key=lambda o: o.get("competition_score", 0), reverse=True
    )
    return {
        "evergreen": [_slot(o) for o in evergreen[:size]],
        "trending": [_slot(o) for o in trending[:size]],
        "high_roi": [_slot(o) for o in high_roi[:size]],
        "low_competition": [_slot(o) for o in low_competition[:size]],
    }


def _quarterly_strategy(opportunities: "list[dict]", config) -> dict:
    """Category/market-level direction for the next quarter."""
    by_category: "dict[str, list[int]]" = {}
    for opportunity in opportunities:
        by_category.setdefault(opportunity.get("category", "general"), []).append(
            opportunity.get("priority", 0)
        )
    focus = sorted(
        (
            {
                "category": category,
                "opportunities": len(priorities),
                "average_priority": round(sum(priorities) / len(priorities)),
                "market_weight": config.market_weight(category),
            }
            for category, priorities in by_category.items()
        ),
        key=lambda entry: (entry["average_priority"] * entry["market_weight"]),
        reverse=True,
    )
    top_evergreen = [
        o for o in opportunities if o.get("content_nature") in LONG_LIVED_NATURES
    ][:3]
    localization = localization_targets(
        max((o.get("trend_score", 0) for o in opportunities), default=0),
        "evergreen", config,
    )
    return {
        "focus_categories": focus[:5],
        "series_candidates": [
            _slot(o) for o in opportunities
            if "expand_into_series" in o.get("strategic_actions", [])
        ][:5],
        "evergreen_investments": [_slot(o) for o in top_evergreen],
        "localization_targets": localization[:4],
    }


def _calendar(opportunities: "list[dict]", horizon_days: int = 30) -> "list[dict]":
    """Dated publish-calendar entries inside each opportunity's window."""
    start = _now().date()
    entries = []
    used_dates: "dict[str, int]" = {}
    for opportunity in sorted(opportunities, key=_window_start_days):
        window = opportunity.get("recommended_publish_window", {})
        offset = int(window.get("start_in_days", 0))
        if offset > horizon_days:
            continue
        date = (start + timedelta(days=offset)).isoformat()
        # Spread same-day pile-ups forward, staying inside the window.
        end_offset = int(window.get("end_in_days", offset + 1))
        while used_dates.get(date, 0) >= 2 and offset < min(end_offset, horizon_days):
            offset += 1
            date = (start + timedelta(days=offset)).isoformat()
        used_dates[date] = used_dates.get(date, 0) + 1
        entries.append({
            "date": date,
            "opportunity_id": opportunity.get("opportunity_id", ""),
            "topic": opportunity.get("topic", ""),
            "platform": opportunity.get("platform", ""),
            "content_type": opportunity.get("recommended_content_type", "short_form"),
            "priority": opportunity.get("priority", 0),
        })
    entries.sort(key=lambda e: (e["date"], -e["priority"]))
    return entries


def build_roadmap(
    opportunities: "list[dict]",
    topic: str = "",
    config: "MarketIntelligenceConfig | None" = None,
) -> dict:
    """One ROADMAP_FIELDS dict from a ranked opportunity batch."""
    config = config or get_market_intelligence_config()
    ranked = sorted(opportunities, key=lambda o: o.get("priority", 0), reverse=True)

    urgent = [o for o in ranked if _window_start_days(o) == 0]
    this_week = [o for o in ranked if _window_start_days(o) <= 7]
    this_month = [o for o in ranked if _window_start_days(o) <= 30]

    return {
        "generated_at": _now().isoformat(),
        "topic": topic,
        "daily": [_slot(o) for o in (urgent or ranked)[: config.daily_slots]],
        "weekly": [_slot(o) for o in (this_week or ranked)[: config.weekly_slots]],
        "monthly": [_slot(o) for o in (this_month or ranked)[: config.monthly_slots]],
        "quarterly_strategy": _quarterly_strategy(ranked, config),
        "queues": _queues(ranked, config.queue_size),
        "calendar": _calendar(ranked),
    }
