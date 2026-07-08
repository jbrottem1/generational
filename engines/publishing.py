"""Publishing engine (planned) — auto-post to connected platforms per channel schedule."""

from __future__ import annotations

from engines.base import PlannedEngine


class PublishingEngine(PlannedEngine):
    key = "publishing"
    label = "Publish"
    icon = "📤"
    description = "Auto-post content to connected platforms."
