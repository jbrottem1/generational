"""The Market Intelligence Department — the company's strategic front door.

One query surface answering "what should Generational create next?":

    department = get_market_intelligence()
    department.highest_priority_opportunity("sleep science")
    department.top_opportunities("sleep science", n=10)
    department.trending_opportunities("sleep science")
    department.evergreen_opportunities("sleep science")
    department.platform_opportunities("sleep science", "tiktok")
    department.localization_opportunities("sleep science")
    department.publishing_calendar("sleep science")
    department.content_roadmap("sleep science")
    department.market_report("sleep science")

Every answer is structured MarketOpportunity data — never scripts, never
creative assets. One discovery pass per topic feeds every query (cached
for the discovery layer's polling window), and each pass runs the full
chain: providers → signal QC → trend scoring → learning calibration →
competition analysis → forecasting → evergreen/strategy → validation →
roadmap + report.
"""

from __future__ import annotations

import time

from core.log import get_logger, log_event
from services.market_intelligence.config import (
    MarketIntelligenceConfig,
    get_market_intelligence_config,
)
from services.market_intelligence.learning_bridge import build_calibration
from services.market_intelligence.opportunities import build_market_opportunities
from services.market_intelligence.quality import validate_opportunities
from services.market_intelligence.reports import build_market_report
from services.market_intelligence.roadmap import build_roadmap
from services.market_intelligence.strategy import localization_targets
from services.trend_intelligence.config import get_trend_intelligence_config
from services.trend_intelligence.quality import review_trends
from services.trends.manager import TrendDiscoveryManager
from services.trends.scorer import rank_opportunities

logger = get_logger(__name__)


class MarketIntelligence:
    """The department: cached, query-able market analysis per topic."""

    def __init__(
        self,
        manager: "TrendDiscoveryManager | None" = None,
        config: "MarketIntelligenceConfig | None" = None,
        analytics_store=None,
        knowledge_base=None,
    ) -> None:
        self._manager = manager
        self._config = config
        self._analytics_store = analytics_store
        self._knowledge_base = knowledge_base
        # topic → (timestamp, opportunities, roadmap, report)
        self._cache: "dict[str, tuple[float, list[dict], dict, dict]]" = {}

    @property
    def config(self) -> MarketIntelligenceConfig:
        return self._config or get_market_intelligence_config()

    def _build_manager(self) -> TrendDiscoveryManager:
        if self._manager is not None:
            return self._manager
        from providers.trend_sources import get_trend_providers

        discovery_config = get_trend_intelligence_config()
        allowed = [
            provider for provider in get_trend_providers()
            if discovery_config.provider_allowed(provider.key)
        ]
        self._manager = TrendDiscoveryManager(providers=allowed)
        return self._manager

    # ------------------------------------------------------------ analysis

    def analyze(self, topic: str, category: str = "general") -> "list[dict]":
        """One full market-analysis pass; results cached per topic."""
        config = self.config
        discovery_config = get_trend_intelligence_config()

        trends = self._build_manager().discover(
            topic,
            category=category,
            country=(discovery_config.regions or ["US"])[0],
            language=(discovery_config.languages or ["en"])[0],
            limit_per_provider=discovery_config.limit_per_provider,
        )
        kept, signal_report = review_trends(trends, discovery_config)

        calibration = build_calibration(
            category, self._analytics_store, self._knowledge_base
        )
        scored = rank_opportunities(
            kept, historical_performance=calibration["historical_performance"]
        )
        scored = [s for s in scored if s.opportunity_score >= config.min_opportunity_score]

        market_opportunities = build_market_opportunities(scored, calibration, config)
        validated, validation_report = validate_opportunities(
            market_opportunities, config, provider_failures=0
        )

        opportunities = [opportunity.to_dict() for opportunity in validated]
        validation = validation_report.to_dict()
        validation["signal_quality"] = signal_report.to_dict()

        roadmap = build_roadmap(opportunities, topic=topic, config=config)
        report = build_market_report(
            opportunities, validation, calibration, topic=topic, category=category
        )

        self._cache[topic.lower()] = (time.time(), opportunities, roadmap, report)
        log_event(
            logger, "market_intelligence.analyzed",
            topic=topic, opportunities=len(opportunities),
            dropped=validation["dropped_total"],
            top_priority=opportunities[0]["priority"] if opportunities else 0,
        )
        return opportunities

    def _cached(self, topic: str, category: str) -> "tuple[list[dict], dict, dict]":
        key = topic.lower()
        cached = self._cache.get(key)
        window = get_trend_intelligence_config().poll_interval_minutes * 60
        if cached is None or time.time() - cached[0] > window:
            self.analyze(topic, category)
            cached = self._cache[key]
        return cached[1], cached[2], cached[3]

    # -------------------------------------------------------- query surface
    # Every method returns structured opportunity data — never content.

    def highest_priority_opportunity(self, topic: str, category: str = "general") -> dict:
        opportunities, _, _ = self._cached(topic, category)
        return opportunities[0] if opportunities else {}

    def top_opportunities(self, topic: str, n: int = 10, category: str = "general") -> "list[dict]":
        opportunities, _, _ = self._cached(topic, category)
        return opportunities[:n]

    def trending_opportunities(self, topic: str, category: str = "general", n: int = 10) -> "list[dict]":
        opportunities, _, _ = self._cached(topic, category)
        return [
            o for o in opportunities if o["content_nature"] in ("trending", "news")
        ][:n]

    def evergreen_opportunities(self, topic: str, category: str = "general", n: int = 10) -> "list[dict]":
        opportunities, _, _ = self._cached(topic, category)
        return [
            o for o in opportunities
            if o["content_nature"] in ("evergreen", "educational", "reference")
        ][:n]

    def platform_opportunities(
        self, topic: str, platform: str, category: str = "general", n: int = 10
    ) -> "list[dict]":
        opportunities, _, _ = self._cached(topic, category)
        platform = platform.lower()
        return [o for o in opportunities if o["platform"] == platform][:n]

    def localization_opportunities(
        self, topic: str, category: str = "general", n: int = 10
    ) -> "list[dict]":
        """Opportunities worth translating, with ranked language targets."""
        opportunities, _, _ = self._cached(topic, category)
        results = []
        for opportunity in opportunities:
            targets = localization_targets(
                opportunity["trend_score"], opportunity["content_nature"], self.config
            )
            if targets and "translate" in opportunity["strategic_actions"]:
                results.append({**opportunity, "localization_targets": targets})
        return results[:n]

    def publishing_calendar(self, topic: str, category: str = "general") -> "list[dict]":
        _, roadmap, _ = self._cached(topic, category)
        return list(roadmap.get("calendar", []))

    def content_roadmap(self, topic: str, category: str = "general") -> dict:
        _, roadmap, _ = self._cached(topic, category)
        return dict(roadmap)

    def market_report(self, topic: str, category: str = "general") -> dict:
        _, _, report = self._cached(topic, category)
        return dict(report)


_department: "MarketIntelligence | None" = None


def get_market_intelligence() -> MarketIntelligence:
    """The app-wide Market Intelligence Department singleton."""
    global _department
    if _department is None:
        _department = MarketIntelligence()
    return _department
