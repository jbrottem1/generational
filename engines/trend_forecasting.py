"""Trend Forecasting engine — Agent 11 (key: trend_forecasting).

Stage 2 of the intelligence pipeline: runs immediately after Opportunity
Ranking, inside the same "trend" orchestrator stage. It consumes the
ranked opportunities and enriches the shared context with predictive
intelligence — never content:

- trend_forecasts:            time to peak, lifespan, trajectory,
                              saturation risk, publishing window/frequency,
                              future opportunity score, forecast confidence
- trend_classifications:      lifecycle / content-type / market-reach labels
- opportunity_recommendations: platform, hook direction, psychology
                              strategy, duration, format, thumbnail/title
                              direction, SEO guidance, ROI, risk, priority
- trend_intelligence_report:  quality-control results, classification
                              histogram, historical-performance factor,
                              the top recommendation

All context keys are additive (DATA_CONTRACTS.md §2); the keys written by
Trend Discovery and Opportunity Ranking are never modified. Logic lives in
`services/trend_intelligence/`; this module is the thin pipeline adapter.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.contracts import ContractEngine
from services.trend_intelligence.config import get_trend_intelligence_config
from services.trend_intelligence.feed import enrich_opportunity
from services.trend_intelligence.history import historical_performance_for
from services.trend_intelligence.quality import review_trends
from services.trends.models import Opportunity, Trend

logger = get_logger(__name__)


def _histogram(values) -> dict:
    counts: dict = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


class TrendForecastingEngine(ContractEngine):
    key = "trend_forecasting"
    label = "Trend Forecasting"
    icon = "🔮"
    description = "Forecast, classify, and recommend action on ranked opportunities before any content is made."
    version = "1.0.0"
    input_contract = ["trend_opportunities"]
    output_contract = [
        "trend_forecasts",
        "trend_classifications",
        "opportunity_recommendations",
        "trend_intelligence_report",
    ]
    dependencies = ["trend_discovery", "opportunity_ranking"]
    capabilities = [
        "forecasting", "classification", "recommendation",
        "quality-control", "learning-integration",
    ]

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        config = get_trend_intelligence_config()

        # Quality control over the full raw signal batch (report only —
        # the ranked selection itself remains Opportunity Ranking's call).
        trends = [Trend.from_dict(item) for item in context.get("trends", [])]
        _, quality_report = review_trends(trends, config)

        opportunities = [
            Opportunity.from_dict(item)
            for item in context.get("trend_opportunities", [])
        ]
        performance = historical_performance_for(context.get("trend_category", "general"))
        enriched = [enrich_opportunity(opp, config) for opp in opportunities]
        enriched.sort(key=lambda item: item["recommendation"]["priority_score"], reverse=True)

        report = {
            "opportunities": len(enriched),
            "quality": quality_report.to_dict(),
            "historical_performance": performance,
            "lifecycles": _histogram(e["classification"]["lifecycle"] for e in enriched),
            "content_types": _histogram(e["classification"]["content_type"] for e in enriched),
            "market_reach": _histogram(e["classification"]["market_reach"] for e in enriched),
            "top_recommendation": enriched[0]["recommendation"] if enriched else {},
            "average_priority": (
                round(sum(e["recommendation"]["priority_score"] for e in enriched) / len(enriched))
                if enriched else 0
            ),
        }

        log_event(
            logger, "trend_forecasting.completed",
            opportunities=len(enriched),
            top_priority=report["top_recommendation"].get("priority_score", 0),
            dropped=report["quality"]["dropped_total"],
        )
        return {
            "trend_forecasts": [e["forecast"] for e in enriched],
            "trend_classifications": [e["classification"] for e in enriched],
            "opportunity_recommendations": [e["recommendation"] for e in enriched],
            "trend_intelligence_report": report,
        }
