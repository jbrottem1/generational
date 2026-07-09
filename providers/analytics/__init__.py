"""Analytics provider registry — per-platform metric backends.

Real platform analytics APIs (YouTube Analytics, TikTok Business, Meta
Insights, ...) implement `AnalyticsProvider` and register here; the
Analytics Engine resolves providers per platform and never talks to a
vendor SDK directly. Until real APIs land, every platform resolves to the
deterministic `MockAnalyticsProvider` so the whole learning loop runs
end-to-end today.
"""

from __future__ import annotations

from providers.analytics.mock import MockAnalyticsProvider
from providers.analytics_provider import AnalyticsProvider

_mock = MockAnalyticsProvider()

# platform key → provider. Real adapters replace the mock per platform via
# register_analytics_provider() — nothing in the engine changes.
_providers: "dict[str, AnalyticsProvider]" = {}


def register_analytics_provider(platform: str, provider: AnalyticsProvider) -> None:
    _providers[platform] = provider


def get_analytics_provider(platform: str) -> AnalyticsProvider:
    """The provider serving a platform (deterministic mock by default)."""
    provider = _providers.get(platform)
    if provider is not None and provider.is_available():
        return provider
    return _mock


__all__ = [
    "AnalyticsProvider",
    "MockAnalyticsProvider",
    "get_analytics_provider",
    "register_analytics_provider",
]
