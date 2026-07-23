"""Package assembly — one optimization pass over one content item.

`optimize_content` is the single entry point the Global Content
Optimization Engine calls per item. It accepts either a pipeline idea dict
or a canonical ContentPackage dict, runs every optimization module, and
returns three artifacts:

- the ENRICHED seo_package (base refinement-stage fields untouched, new
  fields added — the additive contract from engines/seo/README.md),
- the standardized PublishingPackage for the Publishing Engine (Agent 7),
- the per-item Optimization Report.
"""

from __future__ import annotations

from datetime import datetime, timezone

from services.seo.descriptions import build_description_package
from services.seo.hashtags import build_hashtag_package, flat_hashtags
from services.seo.localization import build_localization_package
from services.seo.models import PUBLISHING_PACKAGE_VERSION
from services.seo.report import build_optimization_report
from services.seo.thumbnails import rank_thumbnail_concepts
from services.seo.titles import generate_title_candidates
from services.seo.windows import recommend_publish_windows

# Pipeline platform ids → optimization platform keys.
_PLATFORM_ALIASES = {
    "youtube_shorts": "youtube",
    "youtube_long": "youtube",
    "twitter": "x",
    "instagram_reels": "instagram",
    "facebook_reels": "facebook",
}


def _normalize_platform(platform: str) -> str:
    return _PLATFORM_ALIASES.get(platform, platform)


def _snapshot(item: dict, context: dict) -> dict:
    """Uniform view over an idea dict OR a ContentPackage dict."""
    seo = item.get("seo_package") or {}
    trend = context.get("top_opportunity", {}).get("trend", {})
    platforms = (
        item.get("target_platforms")
        or item.get("platforms")
        or [context.get("target_platform", "youtube_shorts")]
    )
    thumbnails = (
        item.get("thumbnail_plan")
        or item.get("thumbnail_concepts")
        or ([{"source": "seo", "concept": item.get("thumbnail_concept", "")}]
            if item.get("thumbnail_concept") or seo.get("thumbnail_concept") else [])
    )
    behavioral = item.get("behavioral_intelligence", {})
    return {
        "title": seo.get("title") or item.get("title", ""),
        "description": seo.get("description") or item.get("description", ""),
        "keywords": list(seo.get("keywords") or item.get("keywords") or []),
        "hashtags": list(seo.get("hashtags") or item.get("hashtags") or []),
        "base_seo_score": int(seo.get("seo_score") or item.get("seo_score") or 0),
        "topic": item.get("topic") or context.get("subject") or seo.get("title") or item.get("title", ""),
        "hook": item.get("hook", ""),
        "script": item.get("script", ""),
        "niche": context.get("niche", ""),
        "platforms": list(dict.fromkeys(_normalize_platform(p) for p in platforms)),
        "country": item.get("target_country") or trend.get("country") or "US",
        "language": item.get("target_language") or item.get("language") or trend.get("language") or "en",
        "thumbnails": thumbnails,
        "psychology_score": int(item.get("psychology_score", 0)),
        "retention_prediction": int(
            behavioral.get("retention_prediction")
            or item.get("attention_graph", {}).get("attention_score")
            or 50
        ),
        "competition_score": int(
            item.get("competition_score")
            or round((1 - float(trend.get("competition", 0.5))) * 100)
        ),
        "trend_strength": int(
            item.get("trend_score")
            or context.get("top_opportunity", {}).get("opportunity_score")
            or 50
        ),
        "trend_velocity": float(trend.get("velocity", 0.5)),
        "project_id": item.get("project_id", ""),
    }


def optimize_content(item: dict, context: "dict | None" = None) -> dict:
    """Run the full optimization pass; returns seo_package/publishing_package/report."""
    from services.seo.keywords import build_keyword_package, collect_keyword_signals, flatten_keywords

    context = context or {}
    snap = _snapshot(item, context)

    signals = collect_keyword_signals(snap["topic"], country=snap["country"], language=snap["language"])
    keyword_package = build_keyword_package(
        snap["topic"],
        hook=snap["hook"],
        script=snap["script"],
        base_keywords=snap["keywords"],
        niche=snap["niche"],
        signals=signals,
    )
    titles = generate_title_candidates(
        snap["topic"],
        base_title=snap["title"],
        keywords=keyword_package["primary"],
        base_psychology=snap["psychology_score"],
    )
    hashtag_package = build_hashtag_package(
        snap["topic"], niche=snap["niche"],
        keywords=keyword_package["primary"], platforms=None,
    )
    description_package = build_description_package(
        snap["topic"], snap["hook"], titles[0]["title"],
        keyword_package, hashtag_package, niche=snap["niche"],
    )
    thumbnails = rank_thumbnail_concepts(snap["thumbnails"])
    localization = build_localization_package(
        snap["country"], snap["language"],
        keywords=flatten_keywords(keyword_package, limit=10),
        hashtags=flat_hashtags(hashtag_package, snap["platforms"][0]) if snap["platforms"] else [],
        platform=snap["platforms"][0] if snap["platforms"] else "youtube",
    )
    windows = recommend_publish_windows(
        platforms=snap["platforms"],
        country=snap["country"],
        language=snap["language"],
        audience_score=max(snap["psychology_score"], 50),
        competition_score=snap["competition_score"],
        trend_velocity=snap["trend_velocity"],
    )
    report = build_optimization_report(
        titles, keyword_package, description_package, hashtag_package,
        thumbnails, localization, windows,
        signals={
            "base_seo_score": snap["base_seo_score"],
            "retention_prediction": snap["retention_prediction"],
            "competition_score": snap["competition_score"],
            "trend_strength": snap["trend_strength"],
        },
    )

    # Additive enrichment: base refinement-stage fields are never touched.
    enriched = dict(item.get("seo_package") or {})
    enriched.update({
        "optimized_titles": titles,
        "recommended_title": titles[0]["title"] if titles else snap["title"],
        "description_package": description_package,
        "keyword_package": keyword_package,
        "hashtag_package": hashtag_package,
        "thumbnail_recommendations": thumbnails,
        "localization": localization,
        "publish_windows": windows,
        "optimization_report": report,
        "optimization_version": PUBLISHING_PACKAGE_VERSION,
    })

    publishing_package = build_publishing_package(snap, enriched, report)
    return {
        "seo_package": enriched,
        "publishing_package": publishing_package,
        "report": report,
    }


def build_publishing_package(snap: dict, seo_package: dict, report: dict) -> dict:
    """The standardized PublishingPackage the Publishing Engine consumes.

    See PUBLISHING_PACKAGE_FIELDS — additive-only from version 1.0 on.
    """
    from services.seo.keywords import flatten_keywords

    titles = seo_package.get("optimized_titles", [])
    descriptions = seo_package.get("description_package", {})
    thumbnails = seo_package.get("thumbnail_recommendations", [])
    return {
        "package_version": PUBLISHING_PACKAGE_VERSION,
        "project_id": snap["project_id"],
        "title": seo_package.get("recommended_title", snap["title"]),
        "titles": titles,
        "description": descriptions.get("long_description", snap["description"]),
        "descriptions": descriptions,
        "keywords": flatten_keywords(seo_package.get("keyword_package", {})),
        "keyword_package": seo_package.get("keyword_package", {}),
        "hashtags": seo_package.get("hashtag_package", {}),
        "thumbnail": thumbnails[0] if thumbnails else {},
        "thumbnails": thumbnails,
        "publish_windows": seo_package.get("publish_windows", []),
        "localization": seo_package.get("localization", {}),
        "platforms": snap["platforms"],
        "language": snap["language"],
        "country": snap["country"],
        "optimization_report": report,
        "status": "optimized",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
