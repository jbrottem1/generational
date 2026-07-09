"""Market Intelligence — the strategic planning department (Agent 11).

Everything the company creates begins here. The department continuously
discovers, analyzes, predicts, prioritizes, and recommends the
highest-value content opportunities — and hands the Production Pipeline
structured MarketOpportunity objects only. It never generates content.

Layers (bottom-up):
    providers/trend_sources/       signal collection (18 sources)
    services/trends/               Agent 1 — normalize + base scoring
    services/trend_intelligence/   Agent 11 v1 — signal QC, base forecasts
    services/market_intelligence/  THIS — competition, market forecasting,
                                   ROI, strategy, roadmap, reports, queries
"""

from __future__ import annotations

from services.market_intelligence.competition import analyze_competition, competition_level
from services.market_intelligence.config import (
    MarketIntelligenceConfig,
    configure,
    get_market_intelligence_config,
    reset_market_intelligence_config,
)
from services.market_intelligence.department import (
    MarketIntelligence,
    get_market_intelligence,
)
from services.market_intelligence.evergreen import content_nature, split_by_nature
from services.market_intelligence.forecasting import (
    FORECAST_MODELS,
    build_market_forecast,
    forecast_score,
    register_forecast_model,
    validate_forecast,
)
from services.market_intelligence.learning_bridge import (
    build_calibration,
    historical_similarity,
)
from services.market_intelligence.models import (
    CALENDAR_ENTRY_FIELDS,
    COMPETITION_PROFILE_FIELDS,
    CONTENT_NATURES,
    MARKET_FORECAST_FIELDS,
    MARKET_INTELLIGENCE_VERSION,
    MARKET_OPPORTUNITY_FIELDS,
    MARKET_REPORT_FIELDS,
    MARKET_REPORT_SECTIONS,
    ROADMAP_FIELDS,
    ROADMAP_QUEUES,
    STRATEGIC_ACTION,
    MarketOpportunity,
)
from services.market_intelligence.opportunities import (
    build_market_opportunities,
    build_market_opportunity,
)
from services.market_intelligence.quality import ValidationReport, validate_opportunities
from services.market_intelligence.reports import build_market_report
from services.market_intelligence.roadmap import build_roadmap
from services.market_intelligence.strategy import (
    localization_targets,
    recommended_content_length,
    recommended_content_type,
    strategic_actions,
)

__all__ = [
    "CALENDAR_ENTRY_FIELDS",
    "COMPETITION_PROFILE_FIELDS",
    "CONTENT_NATURES",
    "FORECAST_MODELS",
    "MARKET_FORECAST_FIELDS",
    "MARKET_INTELLIGENCE_VERSION",
    "MARKET_OPPORTUNITY_FIELDS",
    "MARKET_REPORT_FIELDS",
    "MARKET_REPORT_SECTIONS",
    "ROADMAP_FIELDS",
    "ROADMAP_QUEUES",
    "STRATEGIC_ACTION",
    "MarketIntelligence",
    "MarketIntelligenceConfig",
    "MarketOpportunity",
    "ValidationReport",
    "analyze_competition",
    "build_calibration",
    "build_market_forecast",
    "build_market_opportunities",
    "build_market_opportunity",
    "build_market_report",
    "build_roadmap",
    "competition_level",
    "configure",
    "content_nature",
    "forecast_score",
    "get_market_intelligence",
    "get_market_intelligence_config",
    "historical_similarity",
    "localization_targets",
    "recommended_content_length",
    "recommended_content_type",
    "register_forecast_model",
    "reset_market_intelligence_config",
    "split_by_nature",
    "strategic_actions",
    "validate_forecast",
    "validate_opportunities",
]
