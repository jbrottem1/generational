"""Trend Discovery Manager — the front door of the operating system.

Queries every registered trend provider, normalizes results into the
universal Trend model, and ranks them into Opportunities. Providers that
fail are skipped and logged; the pipeline never crashes on a bad source.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from services.trends.models import Opportunity, Trend
from services.trends.scorer import rank_opportunities

logger = get_logger(__name__)


class TrendDiscoveryManager:
    def __init__(self, providers: "list | None" = None) -> None:
        # Injectable for tests; lazy default avoids import cycles.
        self._providers = providers

    @property
    def providers(self) -> list:
        if self._providers is None:
            from providers.trend_sources import get_trend_providers

            self._providers = get_trend_providers()
        return self._providers

    def discover(
        self,
        topic: str,
        category: str = "general",
        country: str = "US",
        language: str = "en",
        limit_per_provider: int = 3,
    ) -> list[Trend]:
        """Collect normalized trends from every available provider."""
        trends: list[Trend] = []
        failures = 0
        for provider in self.providers:
            if not provider.is_available():
                continue
            try:
                found = provider.discover(
                    topic, category=category, country=country,
                    language=language, limit=limit_per_provider,
                )
                trends.extend(found)
            except Exception as exc:
                failures += 1
                log_event(
                    logger, "trends.provider_failed", level=30,
                    provider=provider.key, error=str(exc),
                )
        log_event(
            logger, "trends.discovered",
            topic=topic, trends=len(trends), failures=failures,
        )
        return trends

    def discover_opportunities(
        self,
        topic: str,
        category: str = "general",
        country: str = "US",
        language: str = "en",
        top_n: int = 5,
        historical_performance: float = 0.5,
    ) -> list[Opportunity]:
        """Full front-door flow: discover → score → rank → top N."""
        trends = self.discover(topic, category=category, country=country, language=language)
        return rank_opportunities(trends, historical_performance, top_n=top_n)


_manager: "TrendDiscoveryManager | None" = None


def get_trend_manager() -> TrendDiscoveryManager:
    global _manager
    if _manager is None:
        _manager = TrendDiscoveryManager()
    return _manager
