"""Video engine (planned) — assemble voice + visuals into finished videos."""

from __future__ import annotations

from engines.base import PlannedEngine


class VideoEngine(PlannedEngine):
    key = "video"
    label = "Video"
    icon = "🎬"
    description = "Assemble and edit finished videos."
