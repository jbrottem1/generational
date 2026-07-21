"""Discovery Engine — continuous content opportunity intelligence.

Runs BEFORE any script is written:
1. Discover trends across modular providers
2. Score with educational trust weights
3. Verify breaking news
4. YouTube Search Intelligence (active watch demand)
5. Cross-reference News / Trends / Reddit / Wikipedia / YouTube
6. Detect series opportunities
7. Package multi-platform metadata + Agent 3 production briefs
8. Persist / reorder the real-time production queue
"""

from __future__ import annotations

from typing import Any

from core.log import get_logger, log_event
from services.discovery.asset_availability import visual_asset_score
from services.discovery.breaking_news import gate_for_production, is_breaking_candidate
from services.discovery.cross_reference import agreeing_sources_for_topic, boost_multi_source_confidence
from services.discovery.platform_meta import build_platform_packages
from services.discovery.queue import defer_item, save_queue, upsert_items
from services.discovery.scoring import rank_discovery_opportunities
from services.discovery.series import detect_series
from services.discovery.models import QueueItem
from services.trends.manager import TrendDiscoveryManager, get_trend_manager
from services.trends.models import Trend

logger = get_logger(__name__)

_LENGTH_BY_TYPE = {
    "short": {"min": 30, "max": 55},
    "long_form": {"min": 480, "max": 720},
    "series": {"min": 300, "max": 600},
    "live_update": {"min": 30, "max": 90},
}


def _group_related(trends: list[Trend]) -> dict[str, list[Trend]]:
    groups: dict[str, list[Trend]] = {}
    for trend in trends:
        key = (trend.keywords[0].lower() if trend.keywords else trend.topic.lower().split()[0:2])
        if isinstance(key, list):
            key = " ".join(key)
        groups.setdefault(str(key), []).append(trend)
    return groups


def run_discovery(
    subject: str = "science education",
    *,
    category: str = "science",
    country: str = "US",
    language: str = "en",
    limit_per_provider: int = 2,
    top_n: int = 25,
    manager: TrendDiscoveryManager | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    """Full discovery pass → ranked queue + series + deferred breaking news."""
    mgr = manager or get_trend_manager()
    trends = mgr.discover(
        subject,
        category=category,
        country=country,
        language=language,
        limit_per_provider=limit_per_provider,
    )

    youtube_meta: dict[str, Any] = {"configured": False, "live": False}
    youtube_intelligence: dict[str, Any] = {"live": False}
    try:
        from services.providers.youtube_provider import get_youtube_provider
        from services.providers.youtube_search_intelligence import get_youtube_search_intelligence

        yt = get_youtube_provider()
        youtube_meta["configured"] = yt.is_configured()
        youtube_meta["masked_key"] = yt.masked_key() if yt.is_configured() else "(missing)"
        if yt.is_configured():
            xref_seed = agreeing_sources_for_topic(subject, trends)
            intel = get_youtube_search_intelligence()
            report = intel.analyze_topic(
                subject,
                category=category,
                country=country,
                language=language,
                limit=max(5, limit_per_provider * 2),
                cross_reference=xref_seed,
            )
            youtube_meta["live"] = report.live
            youtube_meta["quota"] = report.quota
            youtube_meta["sample_titles"] = [v.title for v in report.videos[:5]]
            youtube_intelligence = report.to_dict()
            # Trends already include youtube_search_trends via adapter;
            # attach structured intelligence only — no raw API payloads.
    except Exception as exc:  # noqa: BLE001
        youtube_meta["error"] = str(exc)[:200]
        log_event(logger, "discovery.youtube_integration_error", level=30, error=str(exc)[:200])

    google_news_meta: dict[str, Any] = {"configured": True, "live": False}
    try:
        from providers.news.google_news_provider import get_google_news_provider

        gn = get_google_news_provider()
        google_news_meta.update(gn.validate())
        live_items = gn.discover_for_topic(
            subject,
            category=category,
            country=country,
            language=language,
            limit=max(3, limit_per_provider),
        )
        if live_items:
            google_news_meta["live"] = True
            google_news_meta["article_count"] = len(live_items)
            google_news_meta["sample"] = [
                {
                    "title": it.title,
                    "publisher": it.publisher,
                    "category": it.category,
                    "publish_time": it.publish_time,
                    "scores": it.scores.to_dict(),
                    "provider": it.provider,
                    "url": it.url,
                }
                for it in live_items[:5]
            ]
            google_news_meta["last_pull"] = gn.last_pull_meta
    except Exception as exc:  # noqa: BLE001
        google_news_meta["error"] = str(exc)[:200]
        log_event(logger, "discovery.google_news_integration_error", level=30, error=str(exc)[:200])

    # Multi-provider agreement → higher confidence (News × YouTube × Reddit × Wiki …)
    boost_multi_source_confidence(trends)

    related_map = _group_related(trends)
    ranked = rank_discovery_opportunities(trends, top_n=top_n)

    queue_items: list[QueueItem] = []
    deferred: list[dict[str, Any]] = []
    ready_opportunities = []

    yt_brief = (youtube_intelligence.get("brief") or {}) if isinstance(youtube_intelligence, dict) else {}
    yt_market = (youtube_intelligence.get("market") or {}) if isinstance(youtube_intelligence, dict) else {}

    for opportunity, discovery in ranked:
        trend = opportunity.trend
        peers = related_map.get(
            (trend.keywords[0].lower() if trend.keywords else trend.topic.lower()),
            [trend],
        )
        if trend not in peers:
            peers = [trend] + list(peers)

        verification = gate_for_production(trend, related=peers)
        asset = visual_asset_score(trend)
        from services.discovery.scoring import score_discovery_opportunity

        opportunity, discovery = score_discovery_opportunity(
            trend,
            verification_confidence=verification.confidence,
            visual_asset_score=asset,
        )

        xref = agreeing_sources_for_topic(trend.topic, trends)
        # Prefer subject-level YT brief when this trend is the subject / youtube-sourced
        brief = dict(yt_brief) if yt_brief else {}
        if brief:
            brief = {
                **brief,
                "cross_reference": xref,
                "unified_discovery_score": int(
                    round(0.55 * int(brief.get("overall_opportunity_score") or 0) + 0.45 * discovery.total)
                ),
                "market": yt_market,
            }
        else:
            brief = {
                "overall_opportunity_score": opportunity.opportunity_score,
                "confidence": float(verification.confidence),
                "reasoning": f"Discovery score {discovery.total} from {trend.source}.",
                "recommended_video_type": "short",
                "estimated_audience": int(trend.search_volume),
                "expected_click_through_potential": int(discovery.virality_potential or 50),
                "expected_watch_time_sec": 45,
                "estimated_competition": float(trend.competition),
                "unified_discovery_score": discovery.total,
                "target_platform": "youtube_shorts",
                "cross_reference": xref,
            }

        # Per-item confidence: blend verification + YT brief + multi-source
        conf = float(verification.confidence)
        if brief.get("confidence"):
            conf = min(1.0, 0.5 * conf + 0.5 * float(brief["confidence"]))
        if int(xref.get("agreeing_sources") or 0) >= 2:
            conf = min(1.0, conf + 0.05 * (int(xref["agreeing_sources"]) - 1))
        brief["confidence"] = round(conf, 4)

        vtype = str(brief.get("recommended_video_type") or "short")
        packages = build_platform_packages(trend)
        primary_length = _LENGTH_BY_TYPE.get(vtype) or packages.get("youtube_shorts", {}).get(
            "recommended_length_sec"
        ) or {"min": 30, "max": 55}
        if vtype in ("long_form", "series") and "youtube" in packages:
            # Prefer long-form package lengths when recommended
            primary_length = packages.get("youtube", {}).get("recommended_length_sec") or primary_length

        overall = int(brief.get("overall_opportunity_score") or opportunity.opportunity_score)
        unified = int(brief.get("unified_discovery_score") or discovery.total)

        priority = int(
            0.40 * unified
            + 0.25 * overall
            + 0.20 * discovery.factual_confidence
            + 0.15 * (conf * 100)
        )

        peer_sources = sorted({p.source for p in peers if p.source})

        item = QueueItem(
            topic=trend.topic,
            trend_score=opportunity.opportunity_score,
            discovery_score=unified,
            estimated_audience=int(brief.get("estimated_audience") or trend.search_volume),
            growth_rate=float(trend.growth_pct),
            competition=float(brief.get("estimated_competition") or trend.competition),
            recommended_length_sec=dict(primary_length),
            publishing_priority=priority,
            confidence_score=conf,
            category=trend.category,
            lifecycle="breaking" if is_breaking_candidate(trend) else "emerging",
            verification=verification.to_dict(),
            platform_packages=packages,
            sources=peer_sources or [trend.source],
            factors=discovery.to_dict(),
            status="ready" if verification.production_allowed else "deferred",
            production_brief=brief,
            recommended_video_type=vtype,
            overall_opportunity_score=overall,
        )

        # Audience Intelligence enrichment layer (does not replace discovery scoring)
        try:
            from services.audience_intelligence import analyze_topic

            ai_report = analyze_topic(
                trend.topic,
                category=trend.category or category,
                angle=str(brief.get("reasoning") or ""),
                discovery_type=vtype,
                youtube_intelligence=youtube_intelligence if isinstance(youtube_intelligence, dict) else None,
                google_news=google_news_meta,
                production_brief=brief,
                cross_reference=xref,
            )
            item.audience_intelligence = ai_report.to_dict()
            item.human_attention_score = ai_report.human_attention_score
            # Prefer AI length when format differs meaningfully
            if ai_report.creative.recommended_video_length_sec:
                item.recommended_length_sec = dict(ai_report.creative.recommended_video_length_sec)
        except Exception as exc:  # noqa: BLE001
            log_event(logger, "discovery.audience_intelligence_error", level=30, error=str(exc)[:200])

        if verification.production_allowed:
            queue_items.append(item)
            ready_opportunities.append(opportunity)
        else:
            deferred.append(
                {
                    "topic": trend.topic,
                    "verification": verification.to_dict(),
                    "discovery_score": unified,
                    "production_brief": brief,
                }
            )
            if persist:
                defer_item(trend.topic, verification.defer_reason or verification.status, verification.to_dict())

    series = detect_series(ready_opportunities or [o for o, _ in ranked], min_episodes=2)
    for plan in series:
        for item in queue_items:
            if item.topic in plan.episode_topics:
                item.series_id = plan.series_id
                if item.recommended_video_type == "short":
                    item.recommended_video_type = "series"
                    item.production_brief["recommended_video_type"] = "series"

    payload = {
        "ok": True,
        "subject": subject,
        "category": category,
        "discovered": len(trends),
        "ranked": len(ranked),
        "ready": len(queue_items),
        "deferred_count": len(deferred),
        "youtube": youtube_meta,
        "youtube_search_intelligence": youtube_intelligence,
        "google_news": google_news_meta,
        "queue": [i.to_dict() for i in sorted(queue_items, key=lambda x: x.publishing_priority, reverse=True)],
        "deferred": deferred,
        "series": [s.to_dict() for s in series],
        "top": None,
        "script_handoff": None,
    }
    if payload["queue"]:
        payload["top"] = payload["queue"][0]
        from services.discovery.script_handoff import queue_item_to_script_context

        payload["script_handoff"] = queue_item_to_script_context(payload["top"])
        payload["audience_intelligence"] = (payload["top"] or {}).get("audience_intelligence") or {}
        payload["human_attention_score"] = int((payload["top"] or {}).get("human_attention_score") or 0)

    if persist:
        upsert_items(queue_items)
        from services.discovery.queue import load_queue

        stored = load_queue()
        stored["series"] = payload["series"]
        stored["deferred"] = (stored.get("deferred") or [])[-50:] + deferred
        stored["deferred"] = stored["deferred"][-100:]
        if youtube_intelligence.get("live"):
            stored["youtube_search_intelligence"] = {
                "topic": youtube_intelligence.get("topic"),
                "brief": youtube_intelligence.get("brief"),
                "market": youtube_intelligence.get("market"),
                "video_count": len(youtube_intelligence.get("videos") or []),
            }
        save_queue(stored)
        payload["queue_path"] = str(
            __import__("services.discovery.queue", fromlist=["QUEUE_PATH"]).QUEUE_PATH
        )

    log_event(
        logger,
        "discovery.completed",
        subject=subject,
        discovered=len(trends),
        ready=len(queue_items),
        deferred=len(deferred),
        series=len(series),
        youtube_intel=bool(youtube_intelligence.get("live")),
    )
    return payload
