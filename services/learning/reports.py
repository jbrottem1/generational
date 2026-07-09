"""Reporting engine — daily / weekly / monthly performance reports.

Machine-readable (PERFORMANCE_REPORT_FIELDS dict) and human-readable
(`render_report_text`) views over the analytics store: totals, top and
worst content, per-engine recommendations, trending opportunities, and
optimization priorities — each with confidence scores. Building a report
never mutates any store and never raises.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from core.log import get_logger, log_event
from services.analytics.models import MetricsStatus, engagement_rate, performance_score
from services.learning.models import LEARNING_REPORT_VERSION, REPORT_PERIODS
from services.learning.patterns import mine_patterns, scored_records
from services.learning.recommendations import build_recommendations, recommendations_by_engine

logger = get_logger(__name__)

_PERIOD_DAYS = {"daily": 1, "weekly": 7, "monthly": 30}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _window(period: str, now: "datetime | None") -> "tuple[str, str]":
    end = now or _now()
    start = end - timedelta(days=_PERIOD_DAYS[period])
    return start.isoformat(), end.isoformat()


def _content_entry(record: dict) -> dict:
    metrics = record.get("metrics", {})
    return {
        "record_id": record.get("record_id", ""),
        "project_id": record.get("project_id", ""),
        "title": record.get("title", ""),
        "hook": record.get("hook", ""),
        "platform": record.get("platform", ""),
        "topic": record.get("topic", ""),
        "performance_score": performance_score(metrics),
        "views": metrics.get("views", 0),
        "audience_retention": metrics.get("audience_retention", 0),
        "ctr": metrics.get("ctr", 0),
        "engagement_rate": engagement_rate(metrics),
        "post_url": record.get("post_url", ""),
    }


def _totals(records: list) -> dict:
    collected = [r for r in records if r.get("metrics_status") == MetricsStatus.COLLECTED]
    views = sum(r.get("metrics", {}).get("views", 0) for r in collected)
    scores = [performance_score(r.get("metrics", {})) for r in collected]
    return {
        "records": len(records),
        "collected": len(collected),
        "pending": len(records) - len(collected),
        "platforms": sorted({r.get("platform", "") for r in records if r.get("platform")}),
        "views": views,
        "watch_time_sec": sum(r.get("metrics", {}).get("watch_time_sec", 0) for r in collected),
        "likes": sum(r.get("metrics", {}).get("likes", 0) for r in collected),
        "comments": sum(r.get("metrics", {}).get("comments", 0) for r in collected),
        "shares": sum(r.get("metrics", {}).get("shares", 0) for r in collected),
        "saves": sum(r.get("metrics", {}).get("saves", 0) for r in collected),
        "followers_gained": sum(r.get("metrics", {}).get("followers_gained", 0) for r in collected),
        "average_performance_score": int(round(sum(scores) / len(scores))) if scores else 0,
    }


def _trending_opportunities(insights: list, limit: int = 5) -> list:
    """Rising signals: positive lift but not yet enough samples to be
    strategy — worth deliberately producing more of to confirm."""
    rising = [
        {
            "dimension": i["dimension"],
            "value": i["value"],
            "lift": i["lift"],
            "samples": i["samples"],
            "confidence": i["confidence"],
            "suggestion": f"Promising {i['dimension']} signal — produce more to confirm.",
        }
        for i in insights
        if i["lift"] > 0 and i["samples"] < 3
    ]
    rising.sort(key=lambda r: r["lift"], reverse=True)
    return rising[:limit]


def _optimization_priorities(insights: list, limit: int = 5) -> list:
    """The most damaging confirmed patterns — fix these first."""
    losers = [
        {
            "dimension": i["dimension"],
            "value": i["value"],
            "lift": i["lift"],
            "samples": i["samples"],
            "confidence": i["confidence"],
            "priority": index + 1,
        }
        for index, i in enumerate(
            sorted(
                (i for i in insights if i["lift"] < 0 and i["samples"] >= 2),
                key=lambda i: i["lift"],
            )
        )
    ]
    return losers[:limit]


def build_performance_report(
    records: list,
    period: str = "daily",
    now: "datetime | None" = None,
) -> dict:
    """One structured performance report over the given analytics records.

    `records` is the full history (e.g. `get_analytics_store().list_records()`);
    the report windows it by `collected_at` for the requested period.
    """
    if period not in REPORT_PERIODS:
        raise ValueError(f"Unknown report period '{period}'. Valid: {list(REPORT_PERIODS)}")

    start, end = _window(period, now)
    windowed = [r for r in records if start <= r.get("collected_at", "") <= end]
    scored = scored_records(windowed)
    scored.sort(key=lambda r: r["_score"], reverse=True)

    insights = mine_patterns(windowed)
    recommendations = build_recommendations(insights)
    confidences = [r["confidence"] for r in recommendations]

    report = {
        "report_version": LEARNING_REPORT_VERSION,
        "period": period,
        "window": {"start": start, "end": end},
        "totals": _totals(windowed),
        "top_content": [_content_entry(r) for r in scored[:5]],
        "worst_content": [_content_entry(r) for r in reversed(scored[-5:])] if scored else [],
        "engine_recommendations": recommendations_by_engine(recommendations),
        "trending_opportunities": _trending_opportunities(insights),
        "optimization_priorities": _optimization_priorities(insights),
        "confidence": int(round(sum(confidences) / len(confidences))) if confidences else 0,
        "generated_at": _now().isoformat(),
    }
    log_event(
        logger, "learning.report_built",
        period=period, records=len(windowed),
        recommendations=len(recommendations),
    )
    return report


def render_report_text(report: dict) -> str:
    """The human-readable view of a performance report."""
    totals = report.get("totals", {})
    lines = [
        f"# {report.get('period', '').title()} Performance Report",
        f"Window: {report.get('window', {}).get('start', '')[:16]} → "
        f"{report.get('window', {}).get('end', '')[:16]} UTC",
        "",
        "## Totals",
        f"- Content tracked: {totals.get('records', 0)} "
        f"({totals.get('collected', 0)} with metrics, {totals.get('pending', 0)} pending)",
        f"- Views: {totals.get('views', 0):,} · Watch time: {totals.get('watch_time_sec', 0):,}s",
        f"- Engagement: {totals.get('likes', 0):,} likes · {totals.get('comments', 0):,} comments · "
        f"{totals.get('shares', 0):,} shares · {totals.get('saves', 0):,} saves",
        f"- Followers gained: {totals.get('followers_gained', 0):,}",
        f"- Average performance score: {totals.get('average_performance_score', 0)}/100",
    ]

    if report.get("top_content"):
        lines += ["", "## Top Performing Content"]
        for entry in report["top_content"]:
            lines.append(
                f"- [{entry['performance_score']}/100] {entry['title'] or entry['hook'][:60]} "
                f"({entry['platform']}, {entry['views']:,} views, "
                f"{entry['audience_retention']}% retention)"
            )

    if report.get("worst_content"):
        lines += ["", "## Worst Performing Content"]
        for entry in report["worst_content"]:
            lines.append(
                f"- [{entry['performance_score']}/100] {entry['title'] or entry['hook'][:60]} "
                f"({entry['platform']})"
            )

    engine_recs = report.get("engine_recommendations", {})
    flat = [rec for recs in engine_recs.values() for rec in recs]
    if flat:
        lines += ["", "## Engine Recommendations"]
        for rec in flat[:10]:
            lines.append(
                f"- [{rec['confidence']}% confidence → {rec['target_engine']}] {rec['action']}"
            )

    if report.get("trending_opportunities"):
        lines += ["", "## Trending Opportunities"]
        for opp in report["trending_opportunities"]:
            lines.append(f"- {opp['dimension']} = {opp['value']} (+{opp['lift']} lift) — {opp['suggestion']}")

    if report.get("optimization_priorities"):
        lines += ["", "## Optimization Priorities"]
        for item in report["optimization_priorities"]:
            lines.append(
                f"- P{item['priority']}: {item['dimension']} = {item['value']} "
                f"({item['lift']} lift over {item['samples']} samples)"
            )

    lines += ["", f"Overall confidence: {report.get('confidence', 0)}/100"]
    return "\n".join(lines)
