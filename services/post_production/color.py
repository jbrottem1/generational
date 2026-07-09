"""Color grading plan — correction, grading, brand LUTs, HDR prep."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.post_production.config import PostProductionConfig

_COLOR_PRESETS = {
    "neutral": {"brightness": 0.0, "contrast": 1.0, "saturation": 1.0, "lut": ""},
    "vibrant": {"brightness": 0.05, "contrast": 1.1, "saturation": 1.15, "lut": "vibrant_pop"},
    "cinematic_warm": {"brightness": -0.02, "contrast": 1.05, "saturation": 0.95, "lut": "cinematic_warm"},
    "documentary_cool": {"brightness": 0.0, "contrast": 1.08, "saturation": 0.9, "lut": "doc_cool"},
    "brand": {"brightness": 0.0, "contrast": 1.0, "saturation": 1.0, "lut": "brand_custom"},
}


def build_color_grading(
    render_package: dict,
    creative_package: dict | None = None,
    config: "PostProductionConfig | None" = None,
) -> dict:
    """Plan color grading from render package and creative direction."""
    from services.post_production.config import get_post_production_config

    config = config or get_post_production_config()
    creative_package = creative_package or {}
    preset_name = config.color_preset
    preset = _COLOR_PRESETS.get(preset_name, _COLOR_PRESETS["neutral"])

    blueprint = creative_package.get("creative_blueprint") or {}
    color_palette = blueprint.get("color_palette") or {}

    brand_lut = config.brand_lut or preset.get("lut", "")

    segments = (render_package.get("timeline") or {}).get("segments") or []
    corrections = []
    for segment in segments:
        scene_id = segment.get("scene_id", 0)
        corrections.append({
            "scene_id": scene_id,
            "brightness": preset["brightness"],
            "contrast": preset["contrast"],
            "saturation": preset["saturation"],
        })

    return {
        "preset": preset_name,
        "lut": brand_lut or preset.get("lut", ""),
        "brightness": preset["brightness"],
        "contrast": preset["contrast"],
        "saturation": preset["saturation"],
        "white_balance": {"temperature": 6500, "tint": 0},
        "hdr_prep": {"enabled": False, "tone_mapping": "hlg_to_sdr"},
        "brand_lut": brand_lut,
        "corrections": corrections,
        "color_palette": color_palette,
    }
