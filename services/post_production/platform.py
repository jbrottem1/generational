"""Platform optimization — aspect ratios, safe zones, caption placement, CTA timing."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.post_production.config import PostProductionConfig

# Per-platform safe zones (fractions of frame).
_PLATFORM_SAFE_ZONES = {
    "youtube": {"top": 0.08, "bottom": 0.12, "left": 0.05, "right": 0.05},
    "youtube_shorts": {"top": 0.12, "bottom": 0.20, "left": 0.06, "right": 0.12},
    "tiktok": {"top": 0.10, "bottom": 0.18, "left": 0.05, "right": 0.15},
    "instagram_reels": {"top": 0.10, "bottom": 0.16, "left": 0.05, "right": 0.12},
    "facebook": {"top": 0.08, "bottom": 0.14, "left": 0.05, "right": 0.08},
    "linkedin": {"top": 0.08, "bottom": 0.12, "left": 0.05, "right": 0.08},
    "x": {"top": 0.08, "bottom": 0.14, "left": 0.05, "right": 0.10},
}

_PLATFORM_ASPECT = {
    "youtube": "16:9",
    "youtube_shorts": "9:16",
    "tiktok": "9:16",
    "instagram_reels": "9:16",
    "facebook": "9:16",
    "linkedin": "16:9",
    "x": "16:9",
}

_CAPTION_ANCHOR = {
    "youtube_shorts": 68.0,
    "tiktok": 64.0,
    "instagram_reels": 66.0,
    "youtube": 85.0,
    "facebook": 65.0,
    "linkedin": 88.0,
    "x": 85.0,
}


def build_platform_exports(
    item: dict,
    export_presets: list,
    config: "PostProductionConfig | None" = None,
) -> list:
    """Prepare platform-specific export configurations."""
    from services.post_production.config import get_post_production_config

    config = config or get_post_production_config()
    platforms = config.target_platforms or item.get("platforms") or ["youtube_shorts"]

    exports = []
    for platform in platforms:
        aspect = _PLATFORM_ASPECT.get(platform, "9:16")
        preset_id = _match_preset(export_presets, aspect)

        exports.append({
            "platform": platform,
            "aspect_ratio": aspect,
            "safe_zones": _PLATFORM_SAFE_ZONES.get(platform, _PLATFORM_SAFE_ZONES["youtube_shorts"]),
            "caption_placement": {"anchor_y_pct": _CAPTION_ANCHOR.get(platform, 68.0)},
            "intro_length_sec": config.intro_length_sec,
            "outro_length_sec": config.outro_length_sec,
            "cta_timing": config.cta_timing_sec,
            "export_preset_id": preset_id,
        })

    return exports


def _match_preset(presets: list, aspect: str) -> str:
    for preset in presets:
        if preset.get("aspect_ratio") == aspect:
            return preset.get("preset_id", "")
    return presets[0].get("preset_id", "") if presets else ""
