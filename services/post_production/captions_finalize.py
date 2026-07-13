"""Caption finalization — enriches render caption_render_plan with styling and exports."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.post_production.config import PostProductionConfig

# Style presets mirrored from render captions (enriched, not replaced).
_STYLE_PRESETS = {
    "bold_pop": {
        "preset": "bold_pop",
        "font": "Montserrat ExtraBold",
        "size_pct": 4.8,
        "fill": "#FFFFFF",
        "stroke": "#000000",
        "stroke_width_px": 6,
        "emphasis_fill": "#FFD400",
        "animation": "word pop 1.08x on entry",
        "position": "bottom_center",
        "safe_area": {"top_pct": 12.0, "bottom_pct": 20.0, "left_pct": 6.0, "right_pct": 12.0},
    },
    "clean_minimal": {
        "preset": "clean_minimal",
        "font": "Inter SemiBold",
        "size_pct": 4.0,
        "fill": "#FFFFFF",
        "stroke": "#00000088",
        "stroke_width_px": 3,
        "emphasis_fill": "#FFFFFF",
        "animation": "fade per sentence",
        "position": "bottom_center",
        "safe_area": {"top_pct": 12.0, "bottom_pct": 20.0, "left_pct": 6.0, "right_pct": 12.0},
    },
    "karaoke_highlight": {
        "preset": "karaoke_highlight",
        "font": "Poppins Bold",
        "size_pct": 4.4,
        "fill": "#FFFFFFB3",
        "stroke": "#000000",
        "stroke_width_px": 4,
        "emphasis_fill": "#4DE1FF",
        "animation": "active word highlighted karaoke-style",
        "position": "bottom_center",
        "safe_area": {"top_pct": 12.0, "bottom_pct": 20.0, "left_pct": 6.0, "right_pct": 12.0},
    },
    "documentary_lower_third": {
        "preset": "documentary_lower_third",
        "font": "Source Serif Pro Semibold",
        "size_pct": 3.6,
        "fill": "#F5F1E8",
        "stroke": "#1A1A1A",
        "stroke_width_px": 3,
        "emphasis_fill": "#E8C468",
        "animation": "slide up per sentence",
        "position": "lower_third",
        "safe_area": {"top_pct": 12.0, "bottom_pct": 20.0, "left_pct": 6.0, "right_pct": 12.0},
    },
}


def finalize_captions(
    render_package: dict,
    config: "PostProductionConfig | None" = None,
) -> tuple[dict, dict]:
    """Build caption timeline and subtitle styling from render caption_render_plan."""
    from services.post_production.config import get_post_production_config

    config = config or get_post_production_config()
    caption_plan = render_package.get("caption_render_plan") or {}
    theme = config.caption_theme
    styling = dict(_STYLE_PRESETS.get(theme, _STYLE_PRESETS["bold_pop"]))

    mode = caption_plan.get("mode", "word_by_word")
    entries = []

    for cue in caption_plan.get("cues", []) or caption_plan.get("word_cues", []):
        text = str(cue.get("text", ""))
        highlight = _extract_highlights(text, cue.get("emphasis_words", []))
        entries.append({
            "entry_id": cue.get("cue_id", cue.get("word_id", "")),
            "start_time": float(cue.get("start_time", cue.get("start_sec", 0.0))),
            "end_time": float(cue.get("end_time", cue.get("end_sec", 0.0))),
            "text": text,
            "highlight_words": highlight,
            "emoji": cue.get("emoji", ""),
            "style_override": cue.get("style_override", ""),
        })

    timeline = {
        "mode": mode,
        "language": config.multi_language[0] if config.multi_language else "en",
        "entries": entries,
        "theme": theme,
        "burn_in": True,
        "export_formats": ["srt", "vtt", "ass", "burned"],
    }

    return timeline, styling


def _extract_highlights(text: str, emphasis: list) -> list:
    if emphasis:
        return list(emphasis)
    words = re.findall(r"\b[A-Z][a-z]+\b|\b\w{5,}\b", text)
    return words[:3]
