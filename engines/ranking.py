"""Ranking engine — stage 4: weighted ranking of scored candidates.

Combines each candidate's psychology score with the research opportunity
score and selects the top N (the requested video count) for production.
Weights are data, not code — tune RANKING_WEIGHTS without touching logic.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.base import Engine

logger = get_logger(__name__)

RANKING_WEIGHTS = {
    "psychology": 0.65,
    "opportunity": 0.35,
}


class RankingEngine(Engine):
    key = "ranking"
    label = "Ranking"
    icon = "🏆"
    description = "Rank candidates with weighted scoring and select the best."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        candidates = context.get("candidates", [])
        opportunity = context.get("research", {}).get("opportunity_score", 60)

        for candidate in candidates:
            candidate["rank_score"] = round(
                RANKING_WEIGHTS["psychology"] * candidate.get("psychology_score", 50)
                + RANKING_WEIGHTS["opportunity"] * opportunity,
                1,
            )

        ranked = sorted(candidates, key=lambda c: c["rank_score"], reverse=True)
        select_count = max(1, min(context.get("video_count", 10), len(ranked)))
        selected = ranked[:select_count]

        log_event(
            logger, "ranking.completed",
            candidates=len(ranked), selected=len(selected),
            top_score=ranked[0]["rank_score"] if ranked else 0,
        )
        return {"ranked_candidates": ranked, "selected_ideas": selected}
