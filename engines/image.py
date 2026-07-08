"""Image engine (planned) — thumbnails and visual assets."""

from __future__ import annotations

from engines.base import PlannedEngine


class ImageEngine(PlannedEngine):
    key = "image"
    label = "Image"
    icon = "🖼️"
    description = "Generate thumbnails and visual assets."
