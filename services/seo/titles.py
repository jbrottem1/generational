"""Title Optimization — multiple archetype titles, each fully ranked.

Generates one candidate per archetype (curiosity, authority, educational,
question, shock, list, contrarian, story, breaking news, scientific) and
scores every candidate on CTR prediction, SEO strength, psychology, and
confidence. Deterministic: same input, same ranking — provider-backed
generation can slot in later without changing the contract.
"""

from __future__ import annotations

from engines.heuristics import (
    CURIOSITY_WORDS,
    EMOTION_WORDS,
    IDENTITY_WORDS,
    SURPRISE_WORDS,
    clamp,
    count_hits,
    has_digit,
    stable_jitter,
    weighted_blend,
)
from services.seo.models import TITLE_ARCHETYPES

MAX_TITLE_LENGTH = 60

# Archetype → (template, inherent CTR bonus). {topic} is title-cased.
_TEMPLATES = {
    "curiosity": ("The Hidden Truth About {topic}", 8),
    "authority": ("What Experts Know About {topic} (And You Don't)", 6),
    "educational": ("{topic} Explained in 30 Seconds", 4),
    "question": ("Why Does {topic} Work Like This?", 5),
    "shock": ("This {topic} Fact Will Shock You", 9),
    "list": ("5 {topic} Facts Nobody Talks About", 7),
    "contrarian": ("Everything You Know About {topic} Is Wrong", 8),
    "story": ("How {topic} Changed Everything", 5),
    "breaking_news": ("New {topic} Discovery Changes Everything", 6),
    "scientific": ("The Science Behind {topic}, According to Research", 4),
}


def _fit(title: str) -> str:
    if len(title) <= MAX_TITLE_LENGTH:
        return title
    return title[: MAX_TITLE_LENGTH - 3].rstrip() + "..."


def _ctr_prediction(title: str, archetype: str) -> int:
    score = 46 + _TEMPLATES[archetype][1]
    score += count_hits(title, CURIOSITY_WORDS) * 6
    score += count_hits(title, EMOTION_WORDS) * 5
    score += count_hits(title, SURPRISE_WORDS) * 4
    if has_digit(title):
        score += 6
    if "?" in title:
        score += 4
    if 28 <= len(title) <= 55:
        score += 6
    return clamp(score + stable_jitter(title))


def _seo_score(title: str, keywords: list) -> int:
    score = 44
    lower = title.lower()
    matched = [kw for kw in keywords if kw and kw.lower() in lower]
    score += min(len(matched), 3) * 8
    if matched and lower.startswith(matched[0].lower().split()[0]):
        score += 6  # front-loaded primary keyword
    if 20 <= len(title) <= MAX_TITLE_LENGTH:
        score += 12
    return clamp(score + stable_jitter(title + "seo"))


def _psychology_score(title: str, base_psychology: int) -> int:
    score = 40
    score += count_hits(title, EMOTION_WORDS) * 7
    score += count_hits(title, CURIOSITY_WORDS) * 6
    score += count_hits(title, IDENTITY_WORDS) * 5
    score += count_hits(title, SURPRISE_WORDS) * 5
    if base_psychology:
        score = int(round(score * 0.6 + base_psychology * 0.4))
    return clamp(score + stable_jitter(title + "psy"))


def _confidence(ctr: int, seo: int, psychology: int) -> int:
    spread = max(ctr, seo, psychology) - min(ctr, seo, psychology)
    return clamp(78 - spread // 3, low=30, high=95)


def build_title_candidate(title: str, archetype: str, keywords: list, base_psychology: int = 0) -> dict:
    """Score one title on every ranking dimension (rank filled in later)."""
    title = _fit(title)
    ctr = _ctr_prediction(title, archetype)
    seo = _seo_score(title, keywords)
    psychology = _psychology_score(title, base_psychology)
    confidence = _confidence(ctr, seo, psychology)
    overall = weighted_blend(
        {"ctr": ctr, "seo": seo, "psychology": psychology, "confidence": confidence},
        {"ctr": 0.35, "seo": 0.30, "psychology": 0.25, "confidence": 0.10},
    )
    return {
        "title": title,
        "archetype": archetype,
        "ctr_prediction": ctr,
        "seo_score": seo,
        "psychology_score": psychology,
        "confidence": confidence,
        "overall": overall,
        "rank": 0,
    }


def generate_title_candidates(
    topic: str,
    base_title: str = "",
    keywords: "list | None" = None,
    base_psychology: int = 0,
) -> "list[dict]":
    """One ranked candidate per archetype, plus the existing base title.

    The refinement-stage title is scored alongside the archetype variants so
    downstream consumers can see exactly where it lands — it is never
    discarded or overwritten.
    """
    keywords = keywords or []
    subject = (topic or "this topic").strip()
    display = subject.title() if subject.islower() else subject

    candidates = [
        build_title_candidate(
            _TEMPLATES[archetype][0].format(topic=display), archetype, keywords, base_psychology
        )
        for archetype in TITLE_ARCHETYPES
    ]
    if base_title:
        candidates.append(build_title_candidate(base_title, "curiosity", keywords, base_psychology))

    candidates.sort(key=lambda c: (-c["overall"], c["title"]))
    for rank, candidate in enumerate(candidates, 1):
        candidate["rank"] = rank
    return candidates
