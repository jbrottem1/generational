"""Publishing engine (planned) — auto-post to connected platforms per channel schedule.

Live posting stays disabled until AUTONOMOUS_PUBLISHING_ENABLED is explicitly
turned on and every quality gate passes. This engine remains a PlannedEngine
so the workflow spine is ready without enabling public automation.
"""

from __future__ import annotations

from core.constants import AUTONOMOUS_PUBLISHING_ENABLED
from engines.base import PlannedEngine


class PublishingEngine(PlannedEngine):
    key = "publishing"
    label = "Publish"
    icon = "📤"
    description = (
        "Auto-post content to connected platforms "
        f"(autonomous publishing {'ENABLED' if AUTONOMOUS_PUBLISHING_ENABLED else 'DISABLED'})."
    )

    def is_ready(self) -> bool:
        # Never ready while the kill-switch is off — even after providers exist.
        return False
