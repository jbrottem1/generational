"""Hashtag Engine — platform-specific, ranked, with estimated usefulness.

Every platform gets its own tag mix: broad discovery tags (high reach, low
specificity), niche tags, and topic tags (low reach, high specificity).
Usefulness blends reach and specificity per the platform's discovery model
— TikTok/Instagram reward broad tags more than YouTube or LinkedIn do.
"""

from __future__ import annotations

from engines.heuristics import clamp, stable_jitter, weighted_blend
from services.seo.models import HASHTAG_PLATFORMS

# Platform → (discovery tags, max tags, reach weight). The reach weight is
# how much raw reach matters vs. specificity on that platform's algorithm.
_PLATFORM_PROFILES = {
    "youtube": (["#Shorts", "#YouTube"], 4, 0.40),
    "tiktok": (["#fyp", "#foryou", "#viral"], 6, 0.60),
    "instagram": (["#reels", "#explore", "#instagood"], 8, 0.55),
    "facebook": (["#video", "#reels"], 4, 0.45),
    "x": (["#trending"], 3, 0.50),
    "linkedin": (["#learning", "#industry"], 5, 0.30),
    "pinterest": (["#ideas", "#inspiration"], 6, 0.45),
}


def _tagify(text: str) -> str:
    cleaned = "".join(part.title() for part in text.replace("&", " ").split())
    return "#" + "".join(ch for ch in cleaned if ch.isalnum())


def _score_tag(tag: str, platform: str, specificity: int, reach: int) -> dict:
    reach_weight = _PLATFORM_PROFILES[platform][2]
    usefulness = weighted_blend(
        {"reach": reach, "specificity": specificity},
        {"reach": reach_weight, "specificity": 1 - reach_weight},
    )
    return {
        "tag": tag,
        "reach": reach,
        "specificity": specificity,
        "usefulness": clamp(usefulness + stable_jitter(tag + platform, span=6)),
        "rank": 0,
    }


def build_hashtag_package(
    topic: str,
    niche: str = "",
    keywords: "list | None" = None,
    platforms: "list | None" = None,
) -> dict:
    """Ranked hashtags per platform: {platform: [tag dicts sorted by rank]}."""
    keywords = keywords or []
    platforms = [p for p in (platforms or list(HASHTAG_PLATFORMS)) if p in _PLATFORM_PROFILES]

    topic_tags = [_tagify(topic)] if topic else []
    niche_tags = [_tagify(niche)] if niche else []
    keyword_tags = [_tagify(kw) for kw in keywords[:4] if kw]

    package: "dict[str, list[dict]]" = {}
    for platform in platforms:
        discovery_tags, max_tags, _ = _PLATFORM_PROFILES[platform]
        scored = (
            [_score_tag(tag, platform, specificity=85, reach=35) for tag in topic_tags]
            + [_score_tag(tag, platform, specificity=70, reach=50) for tag in niche_tags]
            + [_score_tag(tag, platform, specificity=75, reach=40) for tag in keyword_tags]
            + [_score_tag(tag, platform, specificity=25, reach=90) for tag in discovery_tags]
        )
        deduped: "dict[str, dict]" = {}
        for item in scored:
            if item["tag"] not in deduped:
                deduped[item["tag"]] = item
        ranked = sorted(deduped.values(), key=lambda t: (-t["usefulness"], t["tag"]))[:max_tags]
        for rank, item in enumerate(ranked, 1):
            item["rank"] = rank
        package[platform] = ranked
    return package


def flat_hashtags(package: dict, platform: str) -> "list[str]":
    return [item["tag"] for item in package.get(platform, [])]
