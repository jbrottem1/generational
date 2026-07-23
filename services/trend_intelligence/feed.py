"""Opportunity Feed — the query surface the Production Pipeline consumes.

One front door for "what should we create?":

    feed = get_opportunity_feed()
    feed.top_opportunity("sleep science")
    feed.top("sleep science", n=10)
    feed.emerging("sleep science")
    feed.evergreen("sleep science")
    feed.for_platform("sleep science", "tiktok")
    feed.highest_roi("sleep science")
    feed.highest_confidence("sleep science")

Every result is an enriched opportunity dict: the scored opportunity plus
its forecast, classification, and recommendation. The feed returns
structured opportunities ONLY — it never generates scripts or content.

Discovery flow per refresh: providers (config-filtered) → quality control
→ historical-performance-aware ranking → forecast → classify → recommend.
Results are cached for `poll_interval_minutes` so repeated pipeline
queries within one polling window reuse one discovery pass.
"""

from __future__ import annotations

import time

from core.log import get_logger, log_event
from services.trend_intelligence.classifier import classify_opportunity
from services.trend_intelligence.config import (
    TrendIntelligenceConfig,
    get_trend_intelligence_config,
)
from services.trend_intelligence.forecaster import forecast_opportunity
from services.trend_intelligence.history import historical_performance_for
from services.trend_intelligence.quality import review_trends
from services.trend_intelligence.recommender import recommend_opportunity
from services.trends.manager import TrendDiscoveryManager
from services.trends.models import Opportunity
from services.trends.scorer import rank_opportunities

logger = get_logger(__name__)


def enrich_opportunity(
    opportunity: Opportunity,
    config: "TrendIntelligenceConfig | None" = None,
) -> dict:
    """One scored opportunity → opportunity + forecast + classification +
    recommendation, as one JSON-safe dict. Shared by the feed and the
    Trend Forecasting engine so both surfaces emit identical shapes."""
    config = config or get_trend_intelligence_config()
    forecast = forecast_opportunity(opportunity, config)
    classification = classify_opportunity(opportunity, config)
    recommendation = recommend_opportunity(opportunity, forecast, classification, config)
    return {
        **opportunity.to_dict(),
        "forecast": forecast.to_dict(),
        "classification": classification,
        "recommendation": recommendation.to_dict(),
    }


class OpportunityFeed:
    """Continuously-refreshable, query-able opportunity intelligence."""

    def __init__(
        self,
        manager: "TrendDiscoveryManager | None" = None,
        config: "TrendIntelligenceConfig | None" = None,
        knowledge_base=None,
    ) -> None:
        self._manager = manager
        self._config = config
        self._knowledge_base = knowledge_base
        self._cache: "dict[str, tuple[float, list[dict], dict]]" = {}

    @property
    def config(self) -> TrendIntelligenceConfig:
        return self._config or get_trend_intelligence_config()

    def _build_manager(self) -> TrendDiscoveryManager:
        if self._manager is not None:
            return self._manager
        from providers.trend_sources import get_trend_providers

        allowed = [p for p in get_trend_providers() if self.config.provider_allowed(p.key)]
        self._manager = TrendDiscoveryManager(providers=allowed)
        return self._manager

    # ---------------------------------------------------------- discovery

    def needs_refresh(self, topic: str) -> bool:
        cached = self._cache.get(topic.lower())
        if cached is None:
            return True
        age_seconds = time.time() - cached[0]
        return age_seconds > self.config.poll_interval_minutes * 60

    def refresh(self, topic: str, category: str = "general") -> "list[dict]":
        """Run one full discovery pass and cache the enriched results."""
        config = self.config
        manager = self._build_manager()
        trends = manager.discover(
            topic,
            category=category,
            country=(config.regions or ["US"])[0],
            language=(config.languages or ["en"])[0],
            limit_per_provider=config.limit_per_provider,
        )
        kept, quality_report = review_trends(trends, config)
        performance = historical_performance_for(category, self._knowledge_base)
        opportunities = rank_opportunities(kept, historical_performance=performance)
        enriched = [enrich_opportunity(opp, config) for opp in opportunities]

        meta = {
            "quality": quality_report.to_dict(),
            "historical_performance": performance,
            "category": category,
        }
        self._cache[topic.lower()] = (time.time(), enriched, meta)
        log_event(
            logger, "trend_intelligence.feed_refreshed",
            topic=topic, opportunities=len(enriched),
            dropped=quality_report.to_dict()["dropped_total"],
        )
        return enriched

    def discover(self, topic: str, category: str = "general") -> "list[dict]":
        """Cached discovery — refreshes only when the polling window lapses."""
        if self.needs_refresh(topic):
            return self.refresh(topic, category=category)
        return list(self._cache[topic.lower()][1])

    def last_quality_report(self, topic: str) -> dict:
        cached = self._cache.get(topic.lower())
        return dict(cached[2]["quality"]) if cached else {}

    # ------------------------------------------------------- query surface
    # Every method returns structured opportunity dicts — never content.

    def top_opportunity(self, topic: str, category: str = "general") -> dict:
        results = self.discover(topic, category)
        return results[0] if results else {}

    def top(self, topic: str, n: int = 10, category: str = "general") -> "list[dict]":
        return self.discover(topic, category)[:n]

    def emerging(self, topic: str, category: str = "general", n: int = 10) -> "list[dict]":
        wanted = {"emerging", "breaking", "exploding"}
        return [
            item for item in self.discover(topic, category)
            if item["classification"]["lifecycle"] in wanted
        ][:n]

    def evergreen(self, topic: str, category: str = "general", n: int = 10) -> "list[dict]":
        return [
            item for item in self.discover(topic, category)
            if item["classification"]["content_type"] == "evergreen"
        ][:n]

    def for_platform(self, topic: str, platform: str, category: str = "general", n: int = 10) -> "list[dict]":
        platform = platform.lower()
        return [
            item for item in self.discover(topic, category)
            if item["trend"]["platform"] == platform
            or item["recommendation"]["recommended_platform"] == platform
        ][:n]

    def highest_roi(self, topic: str, category: str = "general", n: int = 10) -> "list[dict]":
        results = self.discover(topic, category)
        return sorted(results, key=lambda i: i["recommendation"]["estimated_roi"], reverse=True)[:n]

    def highest_confidence(self, topic: str, category: str = "general", n: int = 10) -> "list[dict]":
        results = self.discover(topic, category)
        return sorted(
            results, key=lambda i: i["recommendation"]["confidence_score"], reverse=True
        )[:n]


_feed: "OpportunityFeed | None" = None


def get_opportunity_feed() -> OpportunityFeed:
    """The app-wide opportunity feed singleton."""
    global _feed
    if _feed is None:
        _feed = OpportunityFeed()
    return _feed
