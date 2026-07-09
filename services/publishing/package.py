"""Platform publish package assembly — one item × one platform → one package.

Merges the three upstream artifacts the Publishing Engine consumes:

- the RenderPackage (Agent 6) — video file, duration, captions, readiness,
- the optimization PublishingPackage (Agent 8) — titles, descriptions,
  keywords, hashtags, thumbnails, publish windows, localization,
- the scheduler decision — publish time, timezone, mode,

into the platform-ready package defined by PLATFORM_PUBLISH_PACKAGE_FIELDS,
with metadata fitted to the platform's constraints by its provider adapter.
"""

from __future__ import annotations

from datetime import datetime, timezone

from services.publishing.models import PUBLISH_PACKAGE_VERSION


def _video_of(render_package: dict) -> dict:
    return {
        "file_uri": render_package.get("file_uri") or render_package.get("mock_output_path", ""),
        "duration_sec": float(render_package.get("duration_sec", 0.0) or 0.0),
        "resolution": render_package.get("resolution", ""),
        "aspect_ratio": render_package.get("aspect_ratio", ""),
        "mock": bool(render_package.get("mock", True)),
    }


def _captions_of(render_package: dict, item: dict) -> dict:
    captions = render_package.get("caption_render_plan") or item.get("captions") or {}
    return captions if isinstance(captions, dict) else {"segments": captions}


def _flat_tags(entries: list) -> list:
    """Plain hashtag strings from ranked hashtag dicts or raw strings."""
    tags = [e.get("tag", "") if isinstance(e, dict) else str(e) for e in entries]
    return [tag for tag in tags if tag]


def _hashtags_for(optimization: dict, provider) -> list:
    """Per-platform hashtags from the optimization hashtag package.

    The optimization package keys hashtags by SEO platform id ("youtube",
    "instagram", ...); the provider's key and aliases bridge the naming.
    """
    hashtags = optimization.get("hashtags", {})
    if isinstance(hashtags, dict):
        for key in (provider.key, *provider.aliases):
            per_platform = hashtags.get(key)
            if isinstance(per_platform, list):
                return _flat_tags(per_platform)
        flat = [tags for tags in hashtags.values() if isinstance(tags, list)]
        return list(dict.fromkeys(tag for tags in flat for tag in _flat_tags(tags)))
    return _flat_tags(list(hashtags or []))


def build_platform_publish_package(
    item: dict,
    optimization: dict,
    provider,
    schedule: dict,
    account: "dict | None" = None,
    visibility: str = "public",
) -> dict:
    """The platform-ready publish package for one item on one platform.

    `provider` is the platform's PublishingProvider adapter; `optimization`
    is Agent 8's PublishingPackage for the item ({} degrades gracefully to
    the item's base seo_package fields).
    """
    render_package = item.get("render_package") or {}
    seo = item.get("seo_package") or {}
    platform_key = provider.key

    base = {
        "title": optimization.get("title") or seo.get("title") or item.get("title", ""),
        "description": optimization.get("description") or seo.get("description") or item.get("description", ""),
        "hashtags": _hashtags_for(optimization, provider) or list(seo.get("hashtags") or []),
    }
    formatted = provider.format_metadata(base)

    thumbnail = optimization.get("thumbnail") or {}
    if not thumbnail and item.get("thumbnail_plan"):
        thumbnail = {"source": "thumbnail_plan", "concept": item["thumbnail_plan"][0]}

    diagnostics = {
        "format_warnings": formatted["format_warnings"],
        "provider_problems": [],
        "production_readiness_score": render_package.get("production_readiness_score", 0),
        "ready_for_publishing": bool(
            render_package.get("render_manifest", {}).get("ready_for_publishing", False)
        ),
        "optimization_status": optimization.get("status", "missing"),
    }

    package = {
        "package_version": PUBLISH_PACKAGE_VERSION,
        "project_id": optimization.get("project_id") or item.get("project_id", ""),
        "video": _video_of(render_package),
        "thumbnail": thumbnail,
        "title": formatted["title"],
        "description": formatted["description"],
        "hashtags": formatted["hashtags"],
        "keywords": list(optimization.get("keywords") or seo.get("keywords") or []),
        "captions": _captions_of(render_package, item),
        "language": optimization.get("language") or item.get("target_language") or "en",
        "country": optimization.get("country") or item.get("target_country") or "US",
        "platform": platform_key,
        "provider": provider.name or platform_key,
        "account": dict(account or {}),
        "publish_time": schedule.get("publish_time", ""),
        "timezone": schedule.get("timezone", "UTC+00:00"),
        "visibility": visibility,
        "playlist": {"placeholder": True, "playlist_id": ""},   # future playlist routing
        "category": {"placeholder": True, "category_id": ""},   # future category mapping
        "status": "prepared",
        "diagnostics": diagnostics,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    problems = provider.validate(package)
    package["diagnostics"]["provider_problems"] = problems
    if problems:
        package["status"] = "blocked"
    return package
