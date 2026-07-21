"""Content routing — Trend → GenOS opportunity → best Channel Profile.

Advisory match only. Does not redesign engines.
"""

from __future__ import annotations

from typing import Any

from services.channel_os.store import get_profile, list_profiles


def _tokens(text: str) -> set[str]:
    return {t for t in "".join(ch if ch.isalnum() else " " for ch in text.lower()).split() if len(t) > 2}


def score_channel_fit(opportunity: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    """Score how well an opportunity fits a channel profile (0–100)."""
    if profile.get("status") not in (None, "active"):
        return {"score": 0.0, "reasons": ["channel_not_active"]}

    cats = {str(c).lower().replace(" ", "_") for c in (profile.get("topic_categories") or [])}
    world = profile.get("world_preferences") or {}
    domains = {str(d).lower() for d in (world.get("domains") or [])}

    topic = str(opportunity.get("topic") or opportunity.get("title") or "")
    category = str(
        opportunity.get("category")
        or opportunity.get("domain")
        or opportunity.get("niche")
        or ""
    ).lower().replace(" ", "_")
    tags = opportunity.get("tags") or opportunity.get("topics") or []
    tag_set = {str(t).lower().replace(" ", "_") for t in tags} | _tokens(topic)

    score = 0.0
    reasons: list[str] = []

    cat_list = [str(c).lower().replace(" ", "_") for c in (profile.get("topic_categories") or [])]
    if category and category in cats:
        score += 45
        reasons.append(f"category_match:{category}")
        # Primary niche boost — prefer specialist channels over broad multi-niche brands
        if cat_list and cat_list[0] == category:
            score += 20
            reasons.append("primary_category")
        if len(cats) <= 3:
            score += 10
            reasons.append("specialist_channel")
    elif category and any(category in c or c in category for c in cats):
        score += 30
        reasons.append(f"category_partial:{category}")

    overlap = (cats | domains) & tag_set
    if overlap:
        score += min(25, 8 * len(overlap))
        reasons.append(f"topic_overlap:{','.join(sorted(overlap)[:5])}")

    # Domain preference match (world)
    if category and category in domains:
        score += 15
        reasons.append(f"world_domain:{category}")

    # Platform affinity
    opp_platform = str(opportunity.get("platform") or "youtube_shorts")
    platforms = set(profile.get("platforms") or [])
    if opp_platform in platforms or not platforms:
        score += 10
        reasons.append("platform_ok")

    # Opportunity score boost if present
    try:
        opp_score = float(opportunity.get("opportunity_score") or opportunity.get("score") or 0)
        if opp_score >= 70:
            score += 10
            reasons.append("high_opportunity")
    except (TypeError, ValueError):
        pass

    # Tone / audience soft bonus when brief fields align
    audience = str(opportunity.get("target_audience") or opportunity.get("audience") or "").lower()
    if audience and any(tok in audience for tok in _tokens(str(profile.get("target_audience") or ""))):
        score += 5
        reasons.append("audience_affinity")

    return {"score": round(min(100.0, score), 1), "reasons": reasons, "channel_id": profile.get("channel_id")}


def route_opportunity(
    opportunity: dict[str, Any],
    *,
    profiles: list[dict[str, Any]] | None = None,
    min_score: float = 25.0,
) -> dict[str, Any]:
    """
    Select the best Channel Profile for an opportunity.

    Returns ranked matches + selected profile id.
    """
    profiles = profiles if profiles is not None else list_profiles(status="active")
    ranked = []
    for p in profiles:
        fit = score_channel_fit(opportunity, p)
        ranked.append(
            {
                "channel_id": p.get("channel_id"),
                "brand_name": p.get("brand_name"),
                "score": fit["score"],
                "reasons": fit["reasons"],
            }
        )
    ranked.sort(key=lambda r: -float(r["score"]))
    selected = ranked[0] if ranked and float(ranked[0]["score"]) >= min_score else None
    profile = get_profile(selected["channel_id"]) if selected else None
    return {
        "ok": profile is not None,
        "selected_channel_id": (selected or {}).get("channel_id"),
        "selected_brand": (selected or {}).get("brand_name"),
        "selected_score": (selected or {}).get("score"),
        "ranked": ranked[:10],
        "profile": profile,
        "opportunity_topic": opportunity.get("topic") or opportunity.get("title"),
    }


def profile_to_ops_kwargs(profile: dict[str, Any], *, topic: str, length_sec: int = 45) -> dict[str, Any]:
    """Map a Channel Profile into run_studio_ops kwargs (constraints/context injection)."""
    platforms = list(profile.get("platforms") or ["youtube_shorts"])
    platform = platforms[0]
    narrator = str(profile.get("narrator_profile") or "professor")
    voice = str(profile.get("voice_profile") or narrator)
    world = profile.get("world_preferences") or {}
    style = str(world.get("style") or "educational")
    categories = list(profile.get("topic_categories") or [])
    category = categories[0] if categories else "general"

    constraints = {
        "channel_id": profile.get("channel_id"),
        "brand_id": profile.get("channel_id"),
        "brand_name": profile.get("brand_name"),
        "brand_voice": profile.get("tone") or profile.get("brand_voice"),
        "audience": profile.get("target_audience"),
        "niche": profile.get("niche"),
        "topic_categories": categories,
        "visual_style": profile.get("visual_style"),
        "thumbnail_style": profile.get("thumbnail_style"),
        "world_preferences": world,
        "hashtag_strategy": profile.get("hashtag_strategy") or [],
        "seo_rules": profile.get("seo_rules") or {},
        "intro_outro_rules": profile.get("intro_outro_rules") or {},
        "style_profile": style,
        "publishing_enabled": False,
        "channel_os": True,
    }
    context = {
        "channel_id": profile.get("channel_id"),
        "brand_id": profile.get("channel_id"),
        "brand_name": profile.get("brand_name"),
        "audience": profile.get("target_audience"),
        "niche": profile.get("niche"),
        "domain": category,
        "category": category,
        "tone": profile.get("tone"),
        "visual_style": profile.get("visual_style"),
        "world_preferences": world,
        "channel_profile": {
            "channel_id": profile.get("channel_id"),
            "brand_name": profile.get("brand_name"),
            "narrator_profile": narrator,
            "voice_profile": voice,
            "visual_style": profile.get("visual_style"),
            "world_preferences": world,
            "thumbnail_style": profile.get("thumbnail_style"),
        },
        "publishing_enabled": False,
        "channel_os": True,
        "candidate_count": 1,
        "video_count": 1,
    }
    return {
        "topic": topic,
        "platform": platform,
        "length_sec": length_sec,
        "style": "educational" if "educational" in style or style.endswith("_world") else style,
        "narrator": narrator,
        "voice": voice,
        "quality_target": 98,
        "constraints": constraints,
        "context": context,
    }
