"""Trend & Opportunity Intelligence — executive layer for what to produce next."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.trend_opportunity.brief import build_content_strategy, build_production_brief
from services.trend_opportunity.learning import performance_adjustment, predict_performance
from services.trend_opportunity.library import (
    DB_PATH,
    ensure_db,
    production_count,
    upsert_opportunity,
)
from services.trend_opportunity.providers import discover_signals, list_provider_interfaces
from services.trend_opportunity.reports import (
    build_content_calendar,
    format_trend_report_md,
    write_outputs,
)
from services.trend_opportunity.scoring import score_opportunity_card
from services.trend_opportunity.validate import validate_opportunity


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed_science_topics() -> list[dict[str, Any]]:
    """Deterministic educational seeds when live providers return sparse results."""
    seeds = [
        "Why octopuses have three hearts",
        "How black holes bend time",
        "Why the ocean is salty",
        "How vaccines train the immune system",
        "Why leaves change color in autumn",
        "How CRISPR edits genes",
        "Why we dream",
        "How plants make oxygen",
        "Why the moon controls tides",
        "How neural networks learn",
        "Why volcanoes erupt",
        "How GPS satellites measure time",
        "Why bees are disappearing",
        "How coral reefs bleach",
        "Why quantum entanglement confuses physicists",
        "How cameras capture light",
        "Why magnets attract iron",
        "How the seasons work",
        "Why octopuses are so smart",
        "How memory forms in the brain",
        "Why plastics last centuries",
        "How telescopes see distant galaxies",
        "Why ice floats on water",
        "How enzymes speed up life",
        "Why birds can migrate thousands of miles",
        "How mRNA instructions build proteins",
        "Why Earth has a magnetic field",
        "How ears detect sound waves",
        "Why sugar fuels cells",
        "How photosynthesis stores solar energy",
    ]
    return [{"topic": t, "category": "science", "source": "seed_library", "search_volume": 50000 - i * 800, "growth_pct": 40 - i, "competition": 0.35 + i * 0.01, "confidence": 0.8} for i, t in enumerate(seeds)]


def run_trend_opportunity(
    subject: str = "science education",
    *,
    category: str = "science",
    country: str = "US",
    language: str = "en",
    limit_per_provider: int = 3,
    top_n: int = 25,
    brief_count: int = 10,
    high_confidence_count: int = 5,
    persist: bool = True,
    write_reports: bool = True,
    use_discovery_engine: bool = True,
) -> dict[str, Any]:
    """
    Discover → rank → strategy → briefs → library → reports.

    Composes Discovery Engine + trend providers + Audience Intelligence (soft).
    Does not replace Research, Audience Intelligence, or Publishing Intelligence.
    """
    ensure_db()
    interfaces = list_provider_interfaces()
    discovery_result: dict[str, Any] = {}
    queue_items: list[dict[str, Any]] = []

    if use_discovery_engine:
        try:
            from services.discovery import run_discovery

            discovery_result = run_discovery(
                subject,
                category=category,
                country=country,
                language=language,
                limit_per_provider=limit_per_provider,
                top_n=max(top_n, 25),
                persist=persist,
            )
            for item in discovery_result.get("queue") or discovery_result.get("items") or []:
                if hasattr(item, "to_dict"):
                    queue_items.append(item.to_dict())
                elif isinstance(item, dict):
                    queue_items.append(item)
            # Also ready_opportunities
            for item in discovery_result.get("ready_opportunities") or []:
                if isinstance(item, dict) and item not in queue_items:
                    queue_items.append(item)
        except Exception as exc:  # noqa: BLE001
            discovery_result = {"error": str(exc)[:200]}

    signals = discover_signals(
        subject,
        category=category,
        country=country,
        language=language,
        limit_per_provider=limit_per_provider,
    )

    # Normalize topics from queue + raw trends + seeds
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_cand(topic: str, **meta: Any) -> None:
        key = topic.strip().lower()
        if not key or key in seen:
            return
        seen.add(key)
        candidates.append({"topic": topic.strip(), "category": category, **meta})

    for item in queue_items:
        add_cand(
            str(item.get("topic") or ""),
            discovery_item=item,
            confidence=float(item.get("confidence_score") or item.get("confidence") or 0.7),
        )
    for trend in signals.get("trends") or []:
        topic = getattr(trend, "topic", None) or (trend.get("topic") if isinstance(trend, dict) else None)
        if not topic:
            continue
        add_cand(
            str(topic),
            source_signals={
                "search_volume": getattr(trend, "search_volume", 0) if not isinstance(trend, dict) else trend.get("search_volume"),
                "growth_pct": getattr(trend, "growth_pct", 0) if not isinstance(trend, dict) else trend.get("growth_pct"),
                "competition": getattr(trend, "competition", 0.5) if not isinstance(trend, dict) else trend.get("competition"),
                "source": getattr(trend, "source", "") if not isinstance(trend, dict) else trend.get("source"),
            },
            confidence=float(getattr(trend, "confidence", 0.7) if not isinstance(trend, dict) else trend.get("confidence") or 0.7),
        )

    # Ensure enough educational science candidates for ranking
    for seed in _seed_science_topics():
        add_cand(
            seed["topic"],
            source_signals=seed,
            confidence=seed.get("confidence", 0.8),
            seeded=True,
        )

    cards: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    # Soft Audience Intelligence only for non-seed / top discovery (compose, don't own)
    ai_budget = 12
    for cand in candidates:
        topic = cand["topic"]
        ai = {}
        if ai_budget > 0 and not cand.get("seeded"):
            try:
                from services.audience_intelligence import analyze_topic

                ai = analyze_topic(topic, category=category).to_dict()
                ai_budget -= 1
            except Exception:  # noqa: BLE001
                ai = {}
        elif ai_budget > 0 and cand.get("seeded") and len(queue_items) < 5:
            try:
                from services.audience_intelligence import analyze_topic

                ai = analyze_topic(topic, category=category).to_dict()
                ai_budget -= 1
            except Exception:  # noqa: BLE001
                ai = {}
        hist = performance_adjustment(topic, category)
        pcount = production_count(topic, category)
        scored = score_opportunity_card(
            topic,
            category=category,
            source_signals=cand.get("source_signals"),
            discovery_item=cand.get("discovery_item"),
            audience_intel=ai,
            historical_performance=hist,
            production_count=pcount,
        )
        strategy = build_content_strategy(
            topic,
            category=category,
            scores=scored,
            audience_intel=ai,
            platform="youtube_shorts",
        )
        brief = build_production_brief(topic, strategy=strategy, scores=scored, category=category)
        card = {
            "topic": topic,
            "category": category,
            "overall_opportunity_score": scored["overall_opportunity_score"],
            "scores": scored["scores"],
            "analysis": scored["analysis"],
            "confidence": float(cand.get("confidence") or ai.get("confidence") or 0.7),
            "strategy": strategy,
            "production_brief": brief,
            "predicted_performance": predict_performance({**scored, "overall_opportunity_score": scored["overall_opportunity_score"]}),
            "audience_intelligence": {
                "human_attention_score": ai.get("human_attention_score"),
                "confidence": ai.get("confidence"),
            },
            "seeded": bool(cand.get("seeded")),
            "previous_productions_count": pcount,
            "status": "ranked",
        }
        card["production_priority"] = int(
            round(
                0.55 * card["overall_opportunity_score"]
                + 0.25 * float(card["scores"].get("curiosity_score") or 0)
                + 0.20 * float(card["confidence"]) * 100
            )
        )
        gate = validate_opportunity(card)
        card["validation"] = gate
        if not gate["accepted"]:
            card["status"] = "rejected"
            rejected.append(card)
            continue
        card["status"] = "brief_ready"
        cards.append(card)

    cards.sort(key=lambda c: (-float(c.get("production_priority") or 0), -float(c.get("overall_opportunity_score") or 0)))
    top = cards[:top_n]
    briefs = [c["production_brief"] for c in top[:brief_count]]
    high_conf = [c for c in top if float(c.get("confidence") or 0) >= 0.72][:high_confidence_count]
    if len(high_conf) < high_confidence_count:
        # fill with highest scores
        for c in top:
            if c not in high_conf:
                high_conf.append(c)
            if len(high_conf) >= high_confidence_count:
                break

    for c in top:
        if persist:
            oid = upsert_opportunity(c)
            c["opportunity_id"] = oid

    calendar = build_content_calendar(top, days=14)
    opportunity_report = {
        "generated_at": _now(),
        "subject": subject,
        "category": category,
        "package_version": "1.0.0",
        "signal_count": signals.get("trend_count"),
        "sources": signals.get("by_source"),
        "discovery": {
            "error": discovery_result.get("error"),
            "queue_size": len(queue_items),
        },
        "ranked_count": len(top),
        "accepted_count": len(cards),
        "rejected_count": len(rejected),
        "top_opportunities": [
            {
                "topic": c["topic"],
                "overall_opportunity_score": c["overall_opportunity_score"],
                "production_priority": c["production_priority"],
                "confidence": c["confidence"],
                "working_title": (c.get("strategy") or {}).get("working_title"),
                "opportunity_id": c.get("opportunity_id"),
            }
            for c in top
        ],
        "top_production_briefs": [
            {"topic": b.get("topic"), "working_title": b.get("working_title"), "score": b.get("overall_opportunity_score")}
            for b in briefs
        ],
        "highest_confidence": [
            {"topic": c["topic"], "confidence": c["confidence"], "score": c["overall_opportunity_score"]}
            for c in high_conf
        ],
        "rejection_sample": [
            {"topic": r["topic"], "reasons": (r.get("validation") or {}).get("reject_reasons")}
            for r in rejected[:10]
        ],
        "provider_interfaces": interfaces,
        "opportunity_library_db": str(DB_PATH),
        "composes": [
            "discovery_engine",
            "trend_sources",
            "audience_intelligence",
            "world_builder",
            "visual_asset_director",
            "production_operations",
        ],
        "does_not_replace": [
            "research_engine",
            "audience_intelligence",
            "publishing_intelligence",
            "renderer",
        ],
    }

    paths = {}
    if write_reports:
        trend_md = format_trend_report_md(
            {
                **opportunity_report,
                "top_opportunities": opportunity_report["top_opportunities"],
            }
        )
        paths = write_outputs(
            top_opportunities=top,
            opportunity_report=opportunity_report,
            trend_report_md=trend_md,
            production_briefs=briefs,
            calendar=calendar,
        )

    return {
        "ok": True,
        "generated_at": _now(),
        "category": category,
        "top_opportunities": top,
        "production_briefs": briefs,
        "highest_confidence": high_conf,
        "rejected": rejected,
        "calendar": calendar,
        "opportunity_report": opportunity_report,
        "paths": paths,
        "opportunity_library_db": str(DB_PATH),
        "number_one": top[0] if top else None,
    }
