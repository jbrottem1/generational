"""Shared deterministic text-analysis helpers (core — import-cycle safe).

Pure helpers used by scripts, psychology, critic, SEO, and demo fallbacks.
Lives in ``core`` so services can import without loading ``engines`` package
registration (avoids circular imports with AI Director / script_generation).

``engines.heuristics`` re-exports this module for backward compatibility.
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

# Word/phrase banks for the Psychology & Virality Engine (engines/psychology.py).
# Each list backs one attention-science dimension of the ViralScore.
NOVELTY_WORDS = [
    "never seen", "brand new", "first time", "unprecedented", "breakthrough",
    "just discovered", "nobody has", "unique", "revolutionary", "new study",
    "just found", "for the first time",
]

FEAR_WORDS = [
    "danger", "warning", "deadly", "risk", "threat", "kill", "destroy",
    "before it's too late", "scared", "terrifying", "avoid", "toxic", "dying",
]

HUMOR_WORDS = [
    "funny", "hilarious", "lol", "joke", "ridiculous", "awkward", "cringe",
    "meme", "comedy", "prank", "roast",
]

SATISFACTION_WORDS = [
    "finally", "satisfying", "perfect", "oddly satisfying", "relief",
    "solved", "complete", "the answer", "closure", "clicked", "makes sense now",
]

CONTROVERSY_WORDS = [
    "controversial", "unpopular opinion", "debate", "everyone is wrong",
    "banned", "argument", "disagree", "hot take", "wrong about", "not what you think",
]

VISUAL_WORDS = [
    "watch", "see", "look", "picture", "imagine", "visual", "shows",
    "reveal", "footage", "before and after",
]

COMMUNITY_WORDS = [
    "we", "us", "together", "community", "our", "join", "tribe",
    "you're not alone", "people like you",
]

IDENTITY_WORDS = [
    "if you're", "if you are", "you're the type", "for people who",
    "as a", "you know you", "type of person", "kind of person",
]

# Word/phrase banks for the Attention Graph (engines/attention_graph.py, Phase 2).
STORY_TENSION_WORDS = [
    "but then", "until", "suddenly", "everything changed", "right before",
    "at the last moment", "just when", "then it all", "the moment",
    "unravels", "unfolds", "turns into", "spiraled",
]

# "Dopenness" = how quickly and openly the concept opens an anticipatory
# reward loop for a broad audience — an easy, low-jargon promise of payoff.
DOPENNESS_WORDS = [
    "what if", "here's what happens", "let's see", "watch what happens",
    "here's the twist", "guess what", "wait for it", "keep watching",
    "you'll want to see this", "here's why",
]

VISUAL_NOVELTY_WORDS = [
    "transform", "before and after", "time-lapse", "close-up", "zoom in",
    "slow motion", "unbelievable footage", "watch this happen",
    "visual proof", "side by side",
]

# Word/phrase banks for Psychology Threat Detection (engines/threat_detection.py,
# Phase 3). These flag production/attention failure modes rather than reward
# viral potential — the inverse framing of the banks above.
PAYOFF_WORDS = [
    "here's why", "here's how", "the reason", "turns out", "the answer",
    "because", "revealed", "here's what happened", "the truth is",
    "explains why", "so here's", "which means",
]

GENERIC_OPENER_PHRASES = [
    "in this video", "today we're going to", "let's talk about",
    "so basically", "as we all know", "welcome back", "hey guys",
    "without further ado", "let's get into it", "today i want to talk about",
]

POLICY_RISK_WORDS = [
    "kill", "suicide", "self harm", "self-harm", "drugs", "weapon", "gun",
    "violence", "hate", "nudity", "illegal", "explicit", "abuse", "terrorist",
]

MANIPULATIVE_WORDS = [
    "you'll regret", "everyone is doing it", "don't miss out", "act now",
    "only you", "before it's too late", "you need to", "you must",
    "last chance", "or else", "you have to", "trust me",
]

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


def weighted_blend(values: dict, weights: dict, low: int = 5, high: int = 98) -> int:
    """Blend a dimension-score dict into one 0-100 score via weighted sum.

    Every "many dimensions -> one headline score" engine (Psychology's
    ViralScore, the Attention Graph's Attention Score, Threat Detection's
    Threat Score) used to duplicate this exact `clamp(sum(values[k] * w ...))`
    formula. It now lives here once; callers only supply their own
    `values`/`weights` dicts and, if needed, their own clamp bounds (Threat
    Detection blends to the full 0-100 range; Psychology/Attention Graph keep
    the engine-wide default 5-98 range).
    """
    return clamp(sum(values[key] * weight for key, weight in weights.items()), low=low, high=high)


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
