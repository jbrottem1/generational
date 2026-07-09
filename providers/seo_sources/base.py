"""SEO signal source provider interface.

Every SEO signal provider — Google Search, Google Trends, YouTube Search,
TikTok Search, Reddit, news APIs, keyword APIs, or future proprietary
sources — implements exactly this contract and returns only normalized
keyword-signal dicts. Nothing downstream may depend on a specific vendor:
the Global Content Optimization Engine consumes whatever the registry
exposes and works fully without any provider at all.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

# The normalized shape every provider must return. Values are plain and
# JSON-safe; "kind" tells the Keyword Engine which class the signal feeds.
KEYWORD_SIGNAL_FIELDS = (
    "keyword",         # the suggested search term/phrase
    "kind",            # semantic | long_tail | question | entity
    "search_volume",   # estimated monthly searches (int)
    "competition",     # 0.0-1.0 — how contested the term is
    "intent",          # informational | navigational | commercial | transactional
    "confidence",      # 0.0-1.0 — provider's confidence in the signal
    "source",          # provider key that produced the signal
)


class SeoSourceProvider(ABC):
    """Contract for all SEO/keyword signal providers."""

    key: str = ""         # unique registry key, e.g. "google_search"
    label: str = ""       # human-readable name for UI/logs
    capability: str = ""  # signal family: search | trends | keywords | community | news

    def is_available(self) -> bool:
        """Whether the provider can currently serve requests (keys, quota)."""
        return True

    @abstractmethod
    def keyword_signals(
        self,
        topic: str,
        *,
        country: str = "US",
        language: str = "en",
        limit: int = 5,
    ) -> "list[dict]":
        """Return normalized keyword signals (KEYWORD_SIGNAL_FIELDS dicts)."""
        raise NotImplementedError
