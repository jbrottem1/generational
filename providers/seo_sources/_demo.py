"""Deterministic demo keyword-signal factory shared by placeholder providers.

Signals are seeded from (provider, topic, index) so results are stable
across runs and testable, while still varying realistically by provider.
When a provider gains a live API integration it stops using this module —
nothing else changes.
"""

from __future__ import annotations

import hashlib

_KINDS = ("semantic", "long_tail", "question", "entity")

_INTENTS = ("informational", "informational", "commercial", "navigational", "transactional")

_PATTERNS = {
    "semantic": ("{topic} explained", "{topic} meaning", "{topic} basics", "understanding {topic}"),
    "long_tail": (
        "what nobody tells you about {topic}",
        "{topic} for beginners step by step",
        "the real story behind {topic}",
        "{topic} mistakes everyone makes",
    ),
    "question": ("what is {topic}", "how does {topic} work", "why does {topic} matter", "is {topic} real"),
    "entity": ("{topic}", "{topic} research", "{topic} experts", "{topic} history"),
}


def _seed(provider: str, topic: str, index: int) -> int:
    raw = f"{provider}:{topic}:{index}"
    return int(hashlib.md5(raw.encode()).hexdigest()[:8], 16)


def make_keyword_signal(
    provider_key: str,
    topic: str,
    index: int,
    *,
    base_volume: int = 5_000,
    base_confidence: float = 0.6,
) -> dict:
    seed = _seed(provider_key, topic, index)
    kind = _KINDS[seed % len(_KINDS)]
    pattern = _PATTERNS[kind][seed % len(_PATTERNS[kind])]
    return {
        "keyword": pattern.format(topic=topic.lower()),
        "kind": kind,
        "search_volume": base_volume * (1 + seed % 30),
        "competition": round(0.2 + (seed % 60) / 100, 2),
        "intent": _INTENTS[seed % len(_INTENTS)],
        "confidence": round(min(0.95, base_confidence + (seed % 25) / 100), 2),
        "source": provider_key,
    }
