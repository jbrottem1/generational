"""Motion graphics — intros, outros, CTAs, branding, end screens."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.post_production.config import PostProductionConfig


def build_motion_graphics(
    item: dict,
    edit_timeline: dict,
    config: "PostProductionConfig | None" = None,
) -> list:
    """Plan motion graphics from brand context and timeline."""
    from services.post_production.config import get_post_production_config

    config = config or get_post_production_config()
    if not config.enable_motion_graphics:
        return []

    total_duration = float(edit_timeline.get("total_duration_sec") or 0.0)
    brand = item.get("brand") or item.get("brand_id") or ""
    graphics = []

    # Intro sequence.
    if config.intro_length_sec > 0:
        graphics.append({
            "graphic_id": uuid.uuid4().hex[:10],
            "graphic_type": "intro",
            "start_time": 0.0,
            "end_time": config.intro_length_sec,
            "template": "channel_intro",
            "content": {"brand": brand, "title": item.get("title", "")},
            "animation": "fade_in_logo",
        })

    # Outro / end screen.
    if config.outro_length_sec > 0 and total_duration > config.outro_length_sec:
        outro_start = total_duration - config.outro_length_sec
        graphics.append({
            "graphic_id": uuid.uuid4().hex[:10],
            "graphic_type": "outro",
            "start_time": outro_start,
            "end_time": total_duration,
            "template": "end_screen",
            "content": {"cta": "subscribe", "brand": brand},
            "animation": "slide_up_cta",
        })

        graphics.append({
            "graphic_id": uuid.uuid4().hex[:10],
            "graphic_type": "end_screen",
            "start_time": outro_start,
            "end_time": total_duration,
            "template": "end_screen_cards",
            "content": {"cards": ["subscribe", "watch_next"]},
            "animation": "fade_in_cards",
        })

    # CTA timing — subscribe/like animation before outro.
    if total_duration > config.cta_timing_sec + config.outro_length_sec:
        cta_time = total_duration - config.outro_length_sec - config.cta_timing_sec
        graphics.append({
            "graphic_id": uuid.uuid4().hex[:10],
            "graphic_type": "cta",
            "start_time": cta_time,
            "end_time": cta_time + config.cta_timing_sec,
            "template": "subscribe_animation",
            "content": {"action": "subscribe"},
            "animation": "bounce_in",
        })

    # Watermark.
    graphics.append({
        "graphic_id": uuid.uuid4().hex[:10],
        "graphic_type": "watermark",
        "start_time": config.intro_length_sec,
        "end_time": total_duration - config.outro_length_sec,
        "template": "corner_logo",
        "content": {"brand": brand, "opacity": 0.6},
        "animation": "static",
    })

    return graphics
