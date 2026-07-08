"""Analytics engine (planned) — pull performance data back from platforms."""

from __future__ import annotations

from engines.base import PlannedEngine


class AnalyticsEngine(PlannedEngine):
    key = "analytics"
    label = "Analytics"
    icon = "📊"
    description = "Collect performance metrics from platforms."
