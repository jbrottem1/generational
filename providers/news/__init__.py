"""News intelligence providers for Generational discovery + research."""

from __future__ import annotations

from providers.news.google_news_provider import (
    ArticleScores,
    DiscoveryItem,
    GoogleNewsProvider,
    get_google_news_provider,
)
from providers.news.research import NewsProvider

__all__ = [
    "ArticleScores",
    "DiscoveryItem",
    "GoogleNewsProvider",
    "NewsProvider",
    "get_google_news_provider",
]
