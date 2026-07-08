"""Trend Discovery — the front door of the autonomous media operating system."""

from services.trends.models import Opportunity, Trend
from services.trends.scorer import rank_opportunities, score_opportunity

__all__ = [
    "Trend",
    "Opportunity",
    "score_opportunity",
    "rank_opportunities",
    "TrendDiscoveryManager",
    "get_trend_manager",
]


def __getattr__(name: str):
    # Lazy manager import keeps provider discovery out of module import time.
    if name in ("TrendDiscoveryManager", "get_trend_manager"):
        from services.trends.manager import TrendDiscoveryManager, get_trend_manager

        return {"TrendDiscoveryManager": TrendDiscoveryManager, "get_trend_manager": get_trend_manager}[name]
    raise AttributeError(name)
