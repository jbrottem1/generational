"""Export system — resolution presets, orientations, HDR, archive, proxy."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.post_production.config import PostProductionConfig


def build_export_presets(
    config: "PostProductionConfig | None" = None,
) -> list:
    """Build export preset list from configuration."""
    from services.post_production.config import EXPORT_PRESETS, get_post_production_config

    config = config or get_post_production_config()
    presets = []

    for preset_id, spec in EXPORT_PRESETS.items():
        presets.append({
            "preset_id": preset_id,
            "name": preset_id.replace("_", " ").title(),
            "resolution": spec["resolution"],
            "aspect_ratio": spec["aspect_ratio"],
            "orientation": spec["orientation"],
            "container": "mp4",
            "video_codec": "h264" if not spec.get("hdr") else "hevc",
            "audio_codec": "aac",
            "fps": 30,
            "hdr": spec.get("hdr", False),
            "platform": "",
        })

    return presets
