"""Description Engine — long/short/platform descriptions, CTA, and comments.

Everything is generated from the idea's own hook, topic, and keyword
package, so descriptions stay on-message with the script rather than
generic. Per-platform variants respect each platform's length and tone.
"""

from __future__ import annotations

from services.seo.hashtags import flat_hashtags

_PLATFORM_LIMITS = {
    "youtube": 4500,
    "tiktok": 2200,
    "instagram": 2200,
    "facebook": 2000,
    "x": 280,
    "linkedin": 1300,
    "pinterest": 500,
}


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def build_call_to_action(topic: str, platform: str = "youtube") -> str:
    if platform in ("tiktok", "instagram"):
        return f"Follow for more {topic} you won't hear anywhere else."
    if platform == "linkedin":
        return f"Follow for practical breakdowns of {topic} and what it means for your field."
    return f"Subscribe for more — we break down {topic} like this every week."


def build_description_package(
    topic: str,
    hook: str,
    title: str,
    keyword_package: dict,
    hashtag_package: dict,
    niche: str = "",
    platforms: "list | None" = None,
) -> dict:
    """The full description package (see DESCRIPTION_PACKAGE_FIELDS)."""
    platforms = platforms or list(_PLATFORM_LIMITS)
    primary = keyword_package.get("primary", [])
    questions = keyword_package.get("question", [])
    keyword_line = ", ".join(primary[:5])

    long_description = (
        f"{hook} In this video we break down {topic} — what it is, why it matters, "
        f"and the details most people never hear. "
        f"{'We answer: ' + questions[0] + '. ' if questions else ''}"
        f"Watch to the end for the part that changes how you see {topic}."
        + (f"\n\nTopics covered: {keyword_line}." if keyword_line else "")
        + (f"\nNiche: {niche}." if niche else "")
    )
    short_description = _truncate(f"{hook} The {topic} breakdown you haven't heard.", 150)
    call_to_action = build_call_to_action(topic)

    platform_descriptions: "dict[str, str]" = {}
    for platform in platforms:
        limit = _PLATFORM_LIMITS.get(platform, 1000)
        tags = " ".join(flat_hashtags(hashtag_package, platform))
        if platform == "x":
            body = f"{hook} {tags}"
        elif platform == "linkedin":
            body = (
                f"{hook}\n\nA quick, evidence-minded look at {topic} and why it matters. "
                f"{build_call_to_action(topic, platform)}\n\n{tags}"
            )
        elif platform in ("tiktok", "instagram"):
            body = f"{hook} {build_call_to_action(topic, platform)}\n{tags}"
        else:
            body = f"{long_description}\n\n{build_call_to_action(topic, platform)}\n{tags}"
        platform_descriptions[platform] = _truncate(body, limit)

    first_comment = (
        f"{questions[0].capitalize()}? Tell us what you think below."
        if questions
        else f"What surprised you most about {topic}? Tell us below."
    )
    pinned_comment = (
        f"The part everyone misses about {topic} is at the end — "
        f"drop a comment with your take and we'll reply."
    )

    return {
        "long_description": long_description,
        "short_description": short_description,
        "platform_descriptions": platform_descriptions,
        "call_to_action": call_to_action,
        "first_comment": first_comment,
        "pinned_comment": pinned_comment,
    }
