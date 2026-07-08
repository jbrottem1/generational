"""Opportunity Ranking engine — stage 1 of the intelligence pipeline.

Scores every discovered trend 0-100 and gates the pipeline: only the
highest-ranked opportunities move forward. Also aggregates the signals the
Trend Dashboard displays (countries, platforms, languages, velocity).
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.base import Engine
from services.trends.models import Trend
from services.trends.scorer import rank_opportunities

logger = get_logger(__name__)

TOP_OPPORTUNITIES = 5


def _dashboard_summary(opportunities: list) -> dict:
    """Aggregate view for the Trend Dashboard panel."""
    trends = [opp.trend for opp in opportunities]
    return {
        "top_score": opportunities[0].opportunity_score if opportunities else 0,
        "average_score": (
            round(sum(o.opportunity_score for o in opportunities) / len(opportunities))
            if opportunities else 0
        ),
        "countries": sorted({t.country for t in trends}),
        "platforms": sorted({t.platform for t in trends if t.platform}),
        "languages": sorted({t.language for t in trends}),
        "average_growth_pct": (
            round(sum(t.growth_pct for t in trends) / len(trends), 1) if trends else 0.0
        ),
        "average_velocity": (
            round(sum(t.velocity for t in trends) / len(trends), 2) if trends else 0.0
        ),
        "discovered_at": trends[0].timestamp if trends else "",
    }


class OpportunityRankingEngine(Engine):
    key = "opportunity_ranking"
    label = "Opportunity Ranking"
    icon = "🏆"
    description = "Score trends 0-100; only top opportunities move forward."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        trends = [Trend.from_dict(item) for item in context.get("trends", [])]
        opportunities = rank_opportunities(trends, top_n=TOP_OPPORTUNITIES)

        top = opportunities[0] if opportunities else None
        trend_keywords = sorted({
            keyword
            for opp in opportunities
            for keyword in opp.trend.keywords
        })[:12]

        log_event(
            logger,
            "opportunity_ranking.completed",
            candidates=len(trends),
            selected=len(opportunities),
            top_score=top.opportunity_score if top else 0,
        )
        return {
            "trend_opportunities": [opp.to_dict() for opp in opportunities],
            "top_opportunity": top.to_dict() if top else {},
            "trend_keywords": trend_keywords,
            "trend_dashboard": _dashboard_summary(opportunities),
        }
