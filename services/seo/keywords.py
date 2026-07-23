"""Keyword Engine — six keyword classes plus search-intent classification.

Merges deterministic on-text extraction with normalized signals from any
available SEO source provider (`providers/seo_sources/`). Providers are
optional: the engine produces a complete keyword package with zero
providers configured.
"""

from __future__ import annotations

from core.heuristics import content_words
from services.seo.models import KEYWORD_CLASSES, SEARCH_INTENTS

_QUESTION_STARTERS = ("what", "how", "why", "is", "are", "can", "does", "should", "when", "where")
_COMMERCIAL_MARKERS = ("best", "top", "review", "vs", "comparison", "cheap", "deal")
_TRANSACTIONAL_MARKERS = ("buy", "price", "discount", "order", "subscribe", "download")


def collect_keyword_signals(topic: str, country: str = "US", language: str = "en", limit: int = 5) -> "list[dict]":
    """Pull normalized keyword signals from every available SEO provider."""
    from providers.seo_sources import get_seo_providers

    signals: "list[dict]" = []
    for provider in get_seo_providers():
        if not provider.is_available():
            continue
        try:
            signals.extend(provider.keyword_signals(topic, country=country, language=language, limit=limit))
        except Exception:  # noqa: BLE001 - one bad provider never blocks keywords
            continue
    return signals


def classify_intent(keyword: str) -> str:
    """Map one keyword onto the four-way search-intent taxonomy."""
    lower = keyword.lower().strip()
    words = lower.split()
    if any(marker in lower for marker in _TRANSACTIONAL_MARKERS):
        return "transactional"
    if any(marker in lower for marker in _COMMERCIAL_MARKERS):
        return "commercial"
    if words and words[0] in _QUESTION_STARTERS:
        return "informational"
    if len(words) == 1 and keyword.strip()[:1].isupper():
        return "navigational"
    return "informational"


def _dedupe(values: "list[str]", limit: int) -> "list[str]":
    return list(dict.fromkeys(v.strip().lower() for v in values if v and v.strip()))[:limit]


def build_keyword_package(
    topic: str,
    hook: str = "",
    script: str = "",
    base_keywords: "list | None" = None,
    niche: str = "",
    signals: "list[dict] | None" = None,
) -> dict:
    """Full keyword package: six classes + per-intent classification."""
    base_keywords = base_keywords or []
    signals = signals or []
    topic_words = [w for w in (topic or "").lower().split() if len(w) > 2]

    by_kind: "dict[str, list[str]]" = {"semantic": [], "long_tail": [], "question": [], "entity": []}
    for signal in signals:
        kind = signal.get("kind", "semantic")
        if kind in by_kind:
            by_kind[kind].append(signal.get("keyword", ""))

    primary = _dedupe([topic] + base_keywords[:4], 5)
    secondary = _dedupe(
        [kw for kw in base_keywords if kw.lower() not in primary]
        + content_words(hook)[:4]
        + ([niche.lower()] if niche else []),
        8,
    )
    semantic = _dedupe(
        by_kind["semantic"]
        + [f"{topic} explained", f"{topic} meaning", f"understanding {topic}"]
        + content_words(script)[:4],
        8,
    )
    long_tail = _dedupe(
        by_kind["long_tail"]
        + [
            f"what nobody tells you about {topic}",
            f"{topic} for beginners",
            f"the truth about {topic}",
        ],
        8,
    )
    entity = _dedupe(
        by_kind["entity"]
        + [word for word in (topic or "").split() if word[:1].isupper()]
        + ([niche] if niche else []),
        6,
    )
    question = _dedupe(
        by_kind["question"]
        + [f"what is {topic}", f"how does {topic} work", f"why does {topic} matter"],
        6,
    )

    classes = {
        "primary": primary,
        "secondary": secondary,
        "semantic": semantic,
        "long_tail": long_tail,
        "entity": entity,
        "question": question,
    }

    intent_map: "dict[str, list[str]]" = {intent: [] for intent in SEARCH_INTENTS}
    for keywords in classes.values():
        for keyword in keywords:
            intent_map[classify_intent(keyword)].append(keyword)
    dominant = max(SEARCH_INTENTS, key=lambda intent: len(intent_map[intent]))

    package = dict(classes)
    package["search_intent"] = {"by_intent": intent_map, "dominant": dominant}
    package["signal_sources"] = sorted({s.get("source", "") for s in signals if s.get("source")})
    return package


def flatten_keywords(package: dict, limit: int = 20) -> "list[str]":
    """All keyword classes flattened in priority order (primary first)."""
    ordered: "list[str]" = []
    for cls in KEYWORD_CLASSES:
        ordered.extend(package.get(cls, []))
    return list(dict.fromkeys(ordered))[:limit]
