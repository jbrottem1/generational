"""Learning engine (planned) — self-improvement loop.

Will mine the Knowledge Base + analytics data for winning patterns and feed
them back into ideation prompts and channel strategy.
"""

from __future__ import annotations

from engines.base import PlannedEngine


class LearningEngine(PlannedEngine):
    key = "learning"
    label = "Learning"
    icon = "🧠"
    description = "Learn from performance data to improve future content."
