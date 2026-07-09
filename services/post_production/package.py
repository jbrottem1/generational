"""PostProductionPackage assembly — the engine's single deliverable."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from services.post_production.audio_finalize import finalize_audio_mix
from services.post_production.captions_finalize import finalize_captions
from services.post_production.color import build_color_grading
from services.post_production.editing import compute_scene_cuts
from services.post_production.effects import build_effects, build_transitions
from services.post_production.export import build_export_presets
from services.post_production.models import (
    POST_PRODUCTION_ENGINE_VERSION,
    POST_PRODUCTION_PACKAGE_VERSION,
    PackageReadiness,
)
from services.post_production.motion_graphics import build_motion_graphics
from services.post_production.platform import build_platform_exports
from services.post_production.quality import package_readiness, validate_post_production
from services.post_production.timeline import build_edit_timeline

if TYPE_CHECKING:
    from services.post_production.config import PostProductionConfig


def collect_post_production_items(context: dict) -> tuple[list, str]:
    """Items to post-produce, preferring unified_packages."""
    packages = context.get("unified_packages") or []
    if packages:
        return list(packages), "unified_packages"
    for key in ("ideas", "selected_ideas"):
        items = context.get(key) or []
        if items:
            return list(items), key
    return [], ""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_post_production_package(
    item: dict,
    context: dict | None = None,
    config: "PostProductionConfig | None" = None,
) -> dict:
    """One PostProductionPackage for one content item. Never raises."""
    from services.post_production.config import get_post_production_config

    config = config or get_post_production_config()
    context = context or {}

    try:
        return _build_package(item, context, config)
    except Exception as exc:  # noqa: BLE001 - post-production must degrade, never crash
        return _safe_fallback_package(item, str(exc))


def _build_package(item: dict, context: dict, config) -> dict:

    render_package = item.get("render_package") or {}
    audio_package = item.get("audio_package") or {}
    creative_package = item.get("creative_package") or {}
    asset_package = item.get("asset_package") or {}

    scene_cuts = compute_scene_cuts(render_package, audio_package, config)
    edit_timeline = build_edit_timeline(render_package, scene_cuts, config)
    audio_mix = finalize_audio_mix(render_package, audio_package, config)
    caption_timeline, subtitle_styling = finalize_captions(render_package, config)
    transitions = build_transitions(render_package, scene_cuts, config)
    effects = build_effects(render_package, scene_cuts, config)
    color_grading = build_color_grading(render_package, creative_package, config)
    motion_graphics = build_motion_graphics(item, edit_timeline, config)
    export_presets = build_export_presets(config)
    platform_exports = build_platform_exports(item, export_presets, config)

    publishing_metadata = _publishing_metadata(item, context)
    provider_instructions = _provider_instructions(config, edit_timeline)

    package = {
        "post_production_package_version": POST_PRODUCTION_PACKAGE_VERSION,
        "engine_version": POST_PRODUCTION_ENGINE_VERSION,
        "project_id": str(item.get("project_id", "")),
        "title": item.get("title", ""),
        "edit_timeline": edit_timeline,
        "scene_cuts": scene_cuts,
        "audio_mix": audio_mix,
        "caption_timeline": caption_timeline,
        "subtitle_styling": subtitle_styling,
        "motion_graphics": motion_graphics,
        "transitions": transitions,
        "effects": effects,
        "color_grading": color_grading,
        "quality_report": {},
        "publishing_metadata": publishing_metadata,
        "provider_instructions": provider_instructions,
        "platform_exports": platform_exports,
        "export_presets": export_presets,
        "production_readiness": {},
        "validation": {},
        "generated_at": _now_iso(),
    }

    quality_report = validate_post_production(package, render_package)
    package["quality_report"] = quality_report
    package["production_readiness"] = package_readiness(quality_report)
    package["validation"] = {
        "asset_package_present": bool(asset_package),
        "render_package_present": bool(render_package),
        "checks": quality_report.get("checks_passed", 0),
    }

    return package


def _safe_fallback_package(item: dict, error: str) -> dict:
    """Minimal package when planning fails — keeps the pipeline green."""
    return {
        "post_production_package_version": POST_PRODUCTION_PACKAGE_VERSION,
        "engine_version": POST_PRODUCTION_ENGINE_VERSION,
        "project_id": str(item.get("project_id", "")),
        "title": item.get("title", ""),
        "edit_timeline": {},
        "scene_cuts": [],
        "audio_mix": {},
        "caption_timeline": {},
        "subtitle_styling": {},
        "motion_graphics": [],
        "transitions": [],
        "effects": [],
        "color_grading": {},
        "quality_report": {
            "status": "fail",
            "score": 0,
            "issues": [{"issue_id": "fallback", "severity": "error", "category": "timing",
                        "message": error, "time": 0.0, "scene_id": 0}],
            "checks_passed": 0,
            "checks_failed": 1,
            "ready_for_export": False,
        },
        "publishing_metadata": {},
        "provider_instructions": [],
        "platform_exports": [],
        "export_presets": [],
        "production_readiness": {"status": PackageReadiness.INCOMPLETE, "score": 0},
        "validation": {"error": error},
        "generated_at": _now_iso(),
    }


def post_produce_items(
    items: list,
    context: dict | None = None,
    config: "PostProductionConfig | None" = None,
) -> list:
    """Post-produce every item and write post_production_package slot."""
    from services.post_production.config import get_post_production_config

    config = config or get_post_production_config()
    context = context or {}
    packages = []

    for item in items:
        package = build_post_production_package(item, context, config)
        item["post_production_package"] = package
        packages.append(package)

    return packages


def _publishing_metadata(item: dict, context: dict) -> dict:
    seo = item.get("seo_package") or {}
    return {
        "title": seo.get("title") or item.get("title", ""),
        "description": seo.get("description") or item.get("description", ""),
        "tags": seo.get("hashtags") or item.get("hashtags") or [],
        "chapters": [],
        "end_screen": {"enabled": True, "cards": ["subscribe", "watch_next"]},
        "cards": [],
        "platform_overrides": {},
    }


def _provider_instructions(config, edit_timeline: dict) -> list:
    return [
        {
            "provider": config.default_provider,
            "operation": "assemble_timeline",
            "parameters": {
                "timeline_id": edit_timeline.get("timeline_id"),
                "track_count": len(edit_timeline.get("tracks", [])),
            },
            "priority": 1,
            "notes": "Primary assembly via configured post-production provider",
        },
        {
            "provider": "ffmpeg",
            "operation": "export",
            "parameters": {"format": "mp4", "codec": "h264"},
            "priority": 2,
            "notes": "Fallback export via FFmpeg adapter",
        },
    ]
