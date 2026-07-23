"""Modular provider facade — wraps existing TrendSourceProvider contracts.

Future APIs plug in via providers/trend_sources without changing this architecture.
"""

from __future__ import annotations

from typing import Any, Protocol


class TrendSignalProvider(Protocol):
    """Clean interface for Trend & Opportunity Intelligence ingest."""

    key: str
    label: str
    platform: str

    def is_available(self) -> bool: ...

    def discover(
        self,
        topic: str,
        category: str = "general",
        country: str = "US",
        language: str = "en",
        limit: int = 3,
    ) -> list[Any]: ...


# Map mission names → existing registry keys
PROVIDER_ALIASES: dict[str, tuple[str, ...]] = {
    "youtube_trending": ("youtube_trending",),
    "youtube_search": ("youtube_search_trends", "youtube_trending"),
    "google_trends": ("google_trends",),
    "google_news": ("google_news", "news_api"),
    "reddit": ("reddit_trends",),
    "tiktok_trending": ("tiktok_trends",),
    "instagram_trends": ("instagram_trends",),
    "x_twitter": ("x_trends",),
    "rss_feeds": ("rss_feeds", "blog_feeds"),
}


def list_provider_interfaces() -> list[dict[str, Any]]:
    """Status of modular data sources (existing providers + stubs)."""
    registered: dict[str, Any] = {}
    try:
        from providers.trend_sources import get_trend_providers

        for p in get_trend_providers():
            registered[p.key] = p
    except Exception:  # noqa: BLE001
        registered = {}

    rows = []
    for mission_key, aliases in PROVIDER_ALIASES.items():
        hit = None
        for alias in aliases:
            if alias in registered:
                hit = registered[alias]
                break
        rows.append(
            {
                "mission_key": mission_key,
                "provider_key": hit.key if hit else aliases[0],
                "label": hit.label if hit else aliases[0].replace("_", " ").title(),
                "platform": hit.platform if hit else mission_key.split("_")[0],
                "available": bool(hit and hit.is_available()),
                "implemented": hit is not None,
                "note": "Existing TrendSourceProvider" if hit else "Interface reserved — add providers/trend_sources adapter",
            }
        )
    return rows


def discover_signals(
    subject: str,
    *,
    category: str = "science",
    country: str = "US",
    language: str = "en",
    limit_per_provider: int = 3,
) -> dict[str, Any]:
    """Collect Internet signals via existing TrendDiscoveryManager (no new engines)."""
    from services.trends.manager import get_trend_manager

    mgr = get_trend_manager()
    trends = mgr.discover(
        subject,
        category=category,
        country=country,
        language=language,
        limit_per_provider=limit_per_provider,
    )
    by_source: dict[str, int] = {}
    for t in trends:
        src = str(getattr(t, "source", "") or "unknown")
        by_source[src] = by_source.get(src, 0) + 1
    return {
        "subject": subject,
        "category": category,
        "trend_count": len(trends),
        "by_source": by_source,
        "trends": trends,
        "provider_interfaces": list_provider_interfaces(),
    }
