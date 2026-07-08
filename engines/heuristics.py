"""Shared deterministic text-analysis helpers for the intelligence pipeline.

These power the scoring engines (psychology, critic, SEO, quality) and the
Demo Mode fallbacks of the generative engines. Everything here is pure and
deterministic — the same input always produces the same scores — so the
pipeline is fully testable and works without any API key.
"""

from __future__ import annotations

import hashlib
import re

CURIOSITY_WORDS = [
    "secret", "truth", "hidden", "never", "why", "nobody", "mistake",
    "surprising", "weird", "banned", "won't believe", "what happens",
]

EMOTION_WORDS = [
    "shocking", "terrifying", "heartbreaking", "amazing", "unbelievable",
    "fear", "love", "hate", "regret", "instantly", "ruining", "destroying",
]

SURPRISE_WORDS = [
    "actually", "myth", "wrong", "opposite", "backwards", "turns out",
    "nobody talks about", "plot twist", "the real reason",
]

AUTHORITY_WORDS = ["study", "science", "research", "expert", "proven", "data", "psychologist"]

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "about", "your", "you", "this",
    "that", "with", "for", "from", "into", "what", "when", "how", "why",
    "are", "is", "was", "were", "will", "would", "could", "should", "have",
    "has", "had", "not", "them", "they", "their", "there", "here", "then",
    "than", "more", "most", "very", "just", "its", "it's", "these", "those",
}

BORING_REPLACEMENTS = {
    "in this video": "here's the deal —",
    "as we all know": "surprisingly,",
    "basically": "",
    "very ": "",
    "really ": "",
}

ABSOLUTE_CLAIMS = {
    "always": "almost always",
    "never fails": "rarely fails",
    "guaranteed": "highly likely",
    "everyone": "most people",
    "no one": "few people",
}


def clamp(value: float, low: int = 5, high: int = 98) -> int:
    return int(max(low, min(high, value)))


def stable_jitter(text: str, span: int = 8) -> int:
    """Deterministic pseudo-random 0..span-1 derived from the text itself."""
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % max(span, 1)


def count_hits(text: str, words: list) -> int:
    lower = text.lower()
    return sum(1 for word in words if word in lower)


def has_digit(text: str) -> bool:
    return bool(re.search(r"\d", text))


def sentences(text: str) -> list:
    return [chunk.strip() for chunk in re.split(r"(?<=[.!?])\s+", text) if chunk.strip()]


def content_words(text: str) -> list:
    return [
        word
        for word in re.findall(r"[a-z']+", text.lower())
        if len(word) > 4 and word not in STOPWORDS
    ]


def most_repeated_word(text: str) -> "tuple[str, int]":
    counts: dict = {}
    for word in content_words(text):
        counts[word] = counts.get(word, 0) + 1
    if not counts:
        return "", 0
    word = max(counts, key=lambda w: counts[w])
    return word, counts[word]
