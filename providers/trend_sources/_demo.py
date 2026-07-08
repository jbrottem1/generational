"""Deterministic demo trend factory shared by placeholder trend providers.

Signals are seeded from (provider, topic, index) so results are stable
across runs and testable, while still varying realistically by provider.
When a provider gains a live API integration it stops using this module —
nothing else changes.
"""

from __future__ import annotations

import hashlib

from services.trends.models import Trend

_ANGLES = [
    "explained", "myths debunked", "what nobody tells you",
    "the science behind", "hidden history of", "future of",
]


def _seed(provider: str, topic: str, index: int) -> int:
    raw = f"{provider}:{topic}:{index}"
    return int(hashlib.md5(raw.encode()).hexdigest()[:8], 16)


def make_trend(
    provider_key: str,
    platform: str,
    topic: str,
    index: int,
    *,
    category: str = "general",
    country: str = "US",
    language: str = "en",
    base_volume: int = 10_000,
    base_confidence: float = 0.6,
) -> Trend:
    seed = _seed(provider_key, topic, index)
    angle = _ANGLES[seed % len(_ANGLES)]
    return Trend(
        topic=f"{topic} — {angle}" if index else topic,
        keywords=[topic.lower(), angle, category],
        growth_pct=round(20 + seed % 180, 1),
        search_volume=base_volume * (1 + seed % 40),
        velocity=round(0.3 + (seed % 60) / 100, 2),
        competition=round(0.25 + (seed % 55) / 100, 2),
        freshness=round(0.5 + (seed % 50) / 100, 2),
        category=category,
        country=country,
        language=language,
        platform=platform,
        source=provider_key,
        confidence=round(min(0.95, base_confidence + (seed % 25) / 100), 2),
    )
