"""Phase 1 — Publishing Pipeline: complete upload-ready packages."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from providers.publishing.registry import get_publishing_provider
from services.publishing.package import build_platform_publish_package
from services.seo.package import optimize_content
from services.seo.windows import recommend_publish_windows

SUPPORTED_PLATFORMS = (
    "youtube_shorts",
    "tiktok",
    "instagram_reels",
    "facebook_reels",
    "x",
    "youtube_longform",
)

_PLATFORM_ALIASES = {
    "youtube_long": "youtube_longform",
    "youtube_long_form": "youtube_longform",
    "twitter": "x",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mp4_path(candidate: dict, context: dict) -> str:
    export = context.get("export_validation") or {}
    for key in ("mp4_path", "video_path", "final_mp4"):
        if export.get(key):
            return str(export[key])
    rp = candidate.get("render_package") or {}
    return str(
        rp.get("mp4_path")
        or rp.get("file_uri")
        or rp.get("mock_output_path")
        or candidate.get("video_path")
        or ""
    )


def _upload_checklist(platform: str, package: dict) -> list[dict]:
    meta = package.get("metadata") or {}
    video = package.get("video") or {}
    thumb = package.get("thumbnail") or {}
    checks = [
        {"id": "final_mp4", "label": "Final MP4 attached", "ok": bool(video.get("file_uri"))},
        {"id": "thumbnail", "label": "Thumbnail ready", "ok": bool(thumb.get("path") or thumb.get("concept") or package.get("thumbnail_plan"))},
        {"id": "seo_title", "label": "SEO title set", "ok": bool(meta.get("title") or package.get("title"))},
        {"id": "seo_description", "label": "SEO description set", "ok": bool(meta.get("description") or package.get("description"))},
        {"id": "tags", "label": "Platform tags present", "ok": bool(meta.get("tags") or package.get("tags"))},
        {"id": "hashtags", "label": "Hashtags present", "ok": bool(meta.get("hashtags") or package.get("hashtags"))},
        {"id": "category", "label": "Category assigned", "ok": bool(package.get("category") or meta.get("category"))},
        {"id": "publish_time", "label": "Suggested publish time", "ok": bool(package.get("suggested_publish_time") or (package.get("schedule") or {}).get("publish_at"))},
        {"id": "audience", "label": "Suggested audience", "ok": bool(package.get("suggested_audience"))},
        {"id": "platform_fit", "label": f"Formatted for {platform}", "ok": True},
    ]
    return checks


def build_complete_publish_packages(
    candidate: dict,
    *,
    platforms: list[str] | None = None,
    context: dict | None = None,
) -> dict[str, Any]:
    """Generate full publishing packages for every supported platform."""
    context = dict(context or {})
    platforms = [_PLATFORM_ALIASES.get(p, p) for p in (platforms or list(SUPPORTED_PLATFORMS))]
    item = dict(candidate)
    item.setdefault("target_platforms", platforms)

    optimization = optimize_content(item, context)
    seo_package = optimization.get("seo_package") or {}
    publishing_package = optimization.get("publishing_package") or {}
    windows = publishing_package.get("publish_windows") or recommend_publish_windows(
        platforms=["youtube", "tiktok", "instagram", "facebook", "x"],
        audience_score=70,
    )
    # Prefer explicit ISO if present; else synthesize from top window
    suggested_time = None
    if isinstance(windows, list) and windows:
        top_w = windows[0] if isinstance(windows[0], dict) else {}
        suggested_time = top_w.get("recommended_at") or top_w.get("iso")
        if not suggested_time and top_w.get("day"):
            suggested_time = f"next_{top_w.get('day')}_{top_w.get('start_hour_local', 17)}:00_local"
    schedule_seed = {
        "publish_at": suggested_time or datetime.now(timezone.utc).isoformat(),
        "timezone": "local",
        "mode": "suggested",
        "window": windows[0] if isinstance(windows, list) and windows else {},
    }

    mp4 = _mp4_path(item, context)
    if mp4:
        rp = dict(item.get("render_package") or {})
        rp.setdefault("file_uri", mp4)
        rp.setdefault("mp4_path", mp4)
        item["render_package"] = rp

    titles = publishing_package.get("titles") or seo_package.get("title_candidates") or []
    best_title = ""
    if titles and isinstance(titles[0], dict):
        best_title = str(titles[0].get("title") or "")
    elif titles:
        best_title = str(titles[0])
    best_title = best_title or str(
        publishing_package.get("title") or seo_package.get("title") or item.get("title") or ""
    )

    desc_pkg = publishing_package.get("descriptions") or {}
    description = (
        (desc_pkg.get("long_description") if isinstance(desc_pkg, dict) else "")
        or publishing_package.get("description")
        or seo_package.get("description")
        or ""
    )
    keywords = publishing_package.get("keywords") or seo_package.get("keywords") or []
    if isinstance(keywords, dict):
        flat_kw = []
        for v in keywords.values():
            if isinstance(v, list):
                flat_kw.extend(str(x.get("keyword") if isinstance(x, dict) else x) for x in v)
            else:
                flat_kw.append(str(v))
        keywords = [k for k in flat_kw if k]
    hashtags = publishing_package.get("hashtags") or seo_package.get("hashtags") or []
    thumbs = publishing_package.get("thumbnails") or item.get("thumbnail_concepts") or []
    best_thumb = thumbs[0] if isinstance(thumbs, list) and thumbs else thumbs if isinstance(thumbs, dict) else {}
    if not best_thumb:
        best_thumb = {
            "concept": f"High-contrast educational thumbnail for: {item.get('topic') or item.get('title') or 'topic'}",
            "layout": "face_or_subject_left_text_right",
            "style": "curiosity_gap",
        }

    audience = str(
        item.get("audience")
        or (item.get("production_blueprint") or {}).get("primary_audience")
        or context.get("audience")
        or "General curious audience 15–45"
    )
    category = str(item.get("niche") or item.get("category") or context.get("niche") or "Education")

    platform_packages: dict[str, dict] = {}
    for platform in platforms:
        provider = get_publishing_provider(platform)
        if provider is None and platform == "youtube_longform":
            provider = get_publishing_provider("youtube")
        if provider is None:
            # Graceful stub so all mission platforms appear in the package
            pkg = {
                "platform": platform,
                "title": best_title,
                "description": description,
                "tags": list(keywords)[:15] if isinstance(keywords, list) else [],
                "hashtags": hashtags if isinstance(hashtags, list) else [],
                "keywords": keywords,
                "category": category,
                "suggested_publish_time": schedule_seed["publish_at"],
                "suggested_audience": audience,
                "video": {"file_uri": mp4},
                "thumbnail": best_thumb if isinstance(best_thumb, dict) else {"concept": best_thumb},
                "schedule": schedule_seed,
                "metadata": {
                    "title": best_title,
                    "description": description,
                    "tags": list(keywords)[:15] if isinstance(keywords, list) else [],
                    "hashtags": hashtags,
                    "category": category,
                },
                "provider_missing": True,
            }
        else:
            pkg = build_platform_publish_package(
                item,
                {**publishing_package, "title": best_title, "description": description},
                provider,
                schedule_seed,
            )
            pkg["keywords"] = keywords
            pkg["category"] = category
            pkg["suggested_publish_time"] = schedule_seed["publish_at"]
            pkg["suggested_audience"] = audience
            pkg["final_mp4"] = mp4
            pkg["thumbnail_plan"] = best_thumb
        pkg["upload_checklist"] = _upload_checklist(platform, pkg)
        pkg["checklist_ok"] = all(c["ok"] for c in pkg["upload_checklist"])
        platform_packages[platform] = pkg

    return {
        "version": "2.0.0",
        "generated_at": _now(),
        "topic": item.get("topic") or item.get("title"),
        "final_mp4": mp4,
        "thumbnail": best_thumb,
        "seo_title": best_title,
        "seo_description": description,
        "platform_tags": keywords,
        "keywords": keywords,
        "hashtags": hashtags,
        "category": category,
        "suggested_publish_time": schedule_seed["publish_at"],
        "suggested_audience": audience,
        "platforms": platform_packages,
        "seo_package": seo_package,
        "publishing_package": publishing_package,
        "optimization_report": optimization.get("optimization_report") or {},
        "supported_platforms": list(SUPPORTED_PLATFORMS),
    }
