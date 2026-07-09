"""Market Intelligence engine — Agent 11 (key: market_intelligence).

Stage 3 of the intelligence pipeline: runs after Trend Forecasting, still
inside the "trend" orchestrator stage. It consumes the ranked trend
opportunities and turns them into the company's strategic plan — never
content:

- market_opportunities:        validated, priority-ranked MarketOpportunity
                               dicts (platform, audience, ROI, competition,
                               forecast, strategic actions, publish window)
- market_roadmap:              daily/weekly/monthly roadmaps, quarterly
                               strategy, evergreen/trending/high-ROI/
                               low-competition queues, publishing calendar
- market_intelligence_report:  executive summary + opportunity/forecast/
                               competition/ROI/platform reports + quality
                               findings + learning calibration applied

All context keys are additive (DATA_CONTRACTS.md §2); nothing written by
Trend Discovery, Opportunity Ranking, or Trend Forecasting is modified.
Logic lives in `services/market_intelligence/`; this module is the thin
pipeline adapter, and all coordination flows through the orchestrator.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.contracts import ContractEngine
from services.market_intelligence.config import get_market_intelligence_config
from services.market_intelligence.learning_bridge import build_calibration
from services.market_intelligence.opportunities import build_market_opportunities
from services.market_intelligence.quality import validate_opportunities
from services.market_intelligence.reports import build_market_report
from services.market_intelligence.roadmap import build_roadmap
from services.trends.models import Opportunity

logger = get_logger(__name__)


class MarketIntelligenceEngine(ContractEngine):
    key = "market_intelligence"
    label = "Market Intelligence"
    icon = "🛰️"
    description = "Turn ranked opportunities into the company's strategic plan: competition, ROI, roadmap, and reports."
    version = "1.0.0"
    input_contract = ["trend_opportunities"]
    output_contract = [
        "market_opportunities",
        "market_roadmap",
        "market_intelligence_report",
    ]
    dependencies = ["trend_discovery", "opportunity_ranking", "trend_forecasting"]
    capabilities = [
        "market-analysis", "competition-analysis", "roi-estimation",
        "strategic-planning", "roadmap-generation", "reporting",
        "learning-integration",
    ]

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        config = get_market_intelligence_config()
        topic = context.get("trend_subject", "") or context.get("topic", "")
        category = context.get("trend_category", "general")

        opportunities = [
            Opportunity.from_dict(item)
            for item in context.get("trend_opportunities", [])
        ]

        calibration = build_calibration(category)
        market_opportunities = build_market_opportunities(
            opportunities, calibration, config
        )
        validated, validation_report = validate_opportunities(
            market_opportunities, config
        )

        opportunity_dicts = [opportunity.to_dict() for opportunity in validated]
        validation = validation_report.to_dict()
        roadmap = build_roadmap(opportunity_dicts, topic=topic, config=config)
        report = build_market_report(
            opportunity_dicts, validation, calibration,
            topic=topic, category=category,
        )

        log_event(
            logger, "market_intelligence.completed",
            opportunities=len(opportunity_dicts),
            dropped=validation["dropped_total"],
            top_priority=opportunity_dicts[0]["priority"] if opportunity_dicts else 0,
            calendar_entries=len(roadmap["calendar"]),
        )
        return {
            "market_opportunities": opportunity_dicts,
            "market_roadmap": roadmap,
            "market_intelligence_report": report,
        }
