"""Trend Intelligence — forecasting, classification, recommendation, QC.

Agent 11's subsystem. It sits ON TOP of the existing Trend Discovery
subsystem (Agent 1: providers → universal Trend → opportunity scoring) and
answers the questions the raw scores cannot:

- What will likely trend tomorrow? (`forecaster`)
- What kind of opportunity is this? (`classifier`)
- Exactly how should we act on it? (`recommender`)
- Which signals are trustworthy? (`quality`)
- What does our own history say? (`history`)
- What should the pipeline create next? (`feed` — the query surface)

It NEVER generates content. It returns structured opportunities only.
"""

from __future__ import annotations

from services.trend_intelligence.classifier import classify_opportunity
from services.trend_intelligence.config import (
    TrendIntelligenceConfig,
    configure,
    get_trend_intelligence_config,
    reset_trend_intelligence_config,
)
from services.trend_intelligence.feed import (
    OpportunityFeed,
    enrich_opportunity,
    get_opportunity_feed,
)
from services.trend_intelligence.forecaster import forecast_opportunity
from services.trend_intelligence.history import historical_performance_for
from services.trend_intelligence.models import (
    CLASSIFICATION_FIELDS,
    FORECAST_FIELDS,
    RECOMMENDATION_FIELDS,
    OpportunityRecommendation,
    TrendForecast,
)
from services.trend_intelligence.quality import QualityReport, review_trends
from services.trend_intelligence.recommender import recommend_opportunity

__all__ = [
    "TrendIntelligenceConfig",
    "get_trend_intelligence_config",
    "configure",
    "reset_trend_intelligence_config",
    "TrendForecast",
    "OpportunityRecommendation",
    "FORECAST_FIELDS",
    "RECOMMENDATION_FIELDS",
    "CLASSIFICATION_FIELDS",
    "forecast_opportunity",
    "classify_opportunity",
    "recommend_opportunity",
    "QualityReport",
    "review_trends",
    "historical_performance_for",
    "OpportunityFeed",
    "get_opportunity_feed",
    "enrich_opportunity",
]
