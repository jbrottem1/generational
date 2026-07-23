"""Multi-platform discovery packaging — distinct metadata per ecosystem.

Never reuse identical titles/hashtags/CTAs across YouTube, TikTok,
Instagram, Facebook, Pinterest, X, or LinkedIn.
"""

from __future__ import annotations

from services.discovery.models import PlatformPackage
from services.trends.models import Trend

# SEO helpers imported lazily inside build_platform_packages to avoid
# engines ↔ seo ↔ discovery circular imports at package load time.

PLATFORMS = (
    "youtube",
    "youtube_shorts",
    "tiktok",
    "instagram",
    "facebook",
    "pinterest",
    "x",
    "linkedin",
)

_LENGTHS = {
    "youtube": {"min": 480, "max": 720},
    "youtube_shorts": {"min": 30, "max": 55},
    "tiktok": {"min": 25, "max": 45},
    "instagram": {"min": 25, "max": 60},
    "facebook": {"min": 30, "max": 90},
    "pinterest": {"min": 20, "max": 40},
    "x": {"min": 20, "max": 45},
    "linkedin": {"min": 45, "max": 120},
}

_HOOKS = {
    "youtube": "Open with the question viewers already searched — then prove the answer.",
    "youtube_shorts": "First 1.5s: a surprising visual claim. Then the one-line takeaway.",
    "tiktok": "Native cold open — talk to camera, then cut to the demo.",
    "instagram": "Pattern interrupt frame + on-screen keyword, then reveal.",
    "facebook": "Relatable setup, then the educational punchline for shareability.",
    "pinterest": "Clear educational promise in text overlay — searchable, evergreen.",
    "x": "One sharp claim. One visual proof. One follow-up prompt.",
    "linkedin": "Professional curiosity hook — why this matters for informed people.",
}

_CTAS = {
    "youtube": "Subscribe for the next lesson in this series.",
    "youtube_shorts": "Follow for daily science explainers.",
    "tiktok": "Follow for the part-2 breakdown.",
    "instagram": "Save this — and share with someone who needs it.",
    "facebook": "Share if this changed how you see it.",
    "pinterest": "Pin for later — more explainers on the board.",
    "x": "Reply with the question you still have.",
    "linkedin": "Comment with how this shows up in your field.",
}

_ARCHETYPE_BY_PLATFORM = {
    "youtube": "educational",
    "youtube_shorts": "curiosity",
    "tiktok": "shock",
    "instagram": "question",
    "facebook": "story",
    "pinterest": "list",
    "x": "contrarian",
    "linkedin": "authority",
}

_TITLE_FALLBACKS = {
    "youtube": "{topic} Explained",
    "youtube_shorts": "The Hidden Truth About {topic}",
    "tiktok": "This {topic} Fact Will Shock You",
    "instagram": "Why Does {topic} Work Like This?",
    "facebook": "How {topic} Changed Everything",
    "pinterest": "{topic} — Quick Facts Worth Saving",
    "x": "Everything You Know About {topic} Is Wrong",
    "linkedin": "{topic}: What Informed People Should Know",
}


def _seo_platform(platform: str) -> str:
    if platform == "youtube_shorts":
        return "youtube"
    return platform


def _pick_title(candidates: list[dict], platform: str, topic: str) -> str:
    want = _ARCHETYPE_BY_PLATFORM.get(platform, "educational")
    for c in candidates:
        if c.get("archetype") == want and c.get("title"):
            return str(c["title"])
    fallback = _TITLE_FALLBACKS.get(platform, "{topic}").format(topic=topic.title())
    return fallback[:70]


def build_platform_packages(
    trend: Trend,
    *,
    hook: str = "",
    platforms: tuple[str, ...] | list[str] | None = None,
) -> dict[str, dict]:
    """Return distinct metadata packages keyed by platform."""
    from services.seo.hashtags import build_hashtag_package
    from services.seo.titles import generate_title_candidates

    targets = tuple(platforms or PLATFORMS)
    candidates = generate_title_candidates(
        trend.topic,
        keywords=list(trend.keywords or []),
        base_psychology=70,
    )
    seo_platforms = sorted({_seo_platform(p) for p in targets if _seo_platform(p) in (
        "youtube", "tiktok", "instagram", "facebook", "x", "linkedin", "pinterest"
    )})
    hashtag_pkg = build_hashtag_package(
        topic=trend.topic,
        niche=trend.category,
        keywords=list(trend.keywords or []),
        platforms=seo_platforms,
    )

    packages: dict[str, dict] = {}
    for platform in targets:
        title = _pick_title(candidates, platform, trend.topic)
        seo_key = _seo_platform(platform)
        tag_rows = list(hashtag_pkg.get(seo_key) or [])
        hashtags = [str(row.get("tag") or "") for row in tag_rows if row.get("tag")]
        # Ensure platform-unique extras
        extras = {
            "youtube_shorts": ["#Shorts", "#Explained"],
            "tiktok": ["#learnontiktok"],
            "instagram": ["#Reels"],
            "pinterest": ["#Facts"],
        }.get(platform, [])
        hashtags = list(dict.fromkeys(extras + hashtags))[:10]

        tags = list(dict.fromkeys(list(trend.keywords[:5]) + [platform.replace("_", " "), trend.category]))[:10]
        description = (
            f"{hook or trend.topic}. Educational explainer from Generational AI. "
            f"Built for {platform.replace('_', ' ')}. {_CTAS[platform]}"
        )
        if platform == "x":
            description = f"{title} {_CTAS[platform]}"[:260]

        pkg = PlatformPackage(
            platform=platform,
            title=title,
            description=description,
            keywords=list(trend.keywords[:8]),
            tags=tags,
            hashtags=hashtags,
            hook=hook or _HOOKS[platform],
            call_to_action=_CTAS[platform],
            thumbnail_concept=(
                f"Bold keyword '{(trend.keywords[0] if trend.keywords else trend.topic)}' "
                "+ one clear visual proof"
            ),
            recommended_length_sec=dict(_LENGTHS[platform]),
        )
        packages[platform] = pkg.to_dict()
    return packages
