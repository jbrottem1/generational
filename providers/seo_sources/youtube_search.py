"""YouTube Search signal provider — deterministic placeholder until live API wiring."""

from __future__ import annotations

from providers.seo_sources._demo import make_keyword_signal
from providers.seo_sources.base import SeoSourceProvider


class YouTubeSearchProvider(SeoSourceProvider):
    key = "youtube_search"
    label = "YouTube Search (placeholder)"
    capability = "search"

    def keyword_signals(self, topic, *, country="US", language="en", limit=5):
        return [
            make_keyword_signal(self.key, topic, i, base_volume=30_000, base_confidence=0.7)
            for i in range(limit)
        ]
