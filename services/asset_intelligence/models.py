"""Universal Asset Intelligence — metadata contracts (extends existing stores)."""

from __future__ import annotations

from typing import Any

PACKAGE_VERSION = "1.0.0"

# Supported asset kinds (mission vocabulary → internal class)
ASSET_KINDS = (
    "image",
    "video_clip",
    "animation",
    "render_3d",
    "chart",
    "scientific_diagram",
    "map",
    "background_loop",
    "particle_effect",
    "sound_effect",
    "music",
    "icon",
    "logo",
    "educational_graphic",
    "lower_third",
    "transition",
    "overlay",
)

COLLECTIONS = (
    "biology",
    "astronomy",
    "physics",
    "history",
    "finance",
    "medicine",
    "technology",
    "nature",
    "psychology",
    "engineering",
)

METADATA_FIELDS = (
    "asset_id",
    "kind",
    "topic",
    "keywords",
    "category",
    "collection",
    "scientific_accuracy",
    "visual_quality",
    "animation_quality",
    "resolution",
    "orientation",
    "duration_sec",
    "license",
    "color_palette",
    "motion_score",
    "historical_performance",
    "reuse_count",
    "last_usage",
    "creator",
    "uri",
    "source_system",
    "width",
    "height",
    "fingerprint",
)

QUALITY_FIELDS = (
    "visual_score",
    "educational_score",
    "retention_score",
    "motion_score",
    "thumbnail_usefulness",
    "overall_score",
)


def empty_metadata(**overrides: Any) -> dict[str, Any]:
    base = {k: ([] if k == "keywords" else (0 if k.endswith("_score") or k in ("reuse_count", "duration_sec", "width", "height", "historical_performance", "scientific_accuracy", "visual_quality", "animation_quality", "motion_score") else "")) for k in METADATA_FIELDS}
    base["keywords"] = []
    base.update(overrides)
    return base
