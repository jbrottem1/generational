"""Learning Engine — Agent 9's self-improvement stage (key: learning).

Mines the cumulative analytics store for winning and losing patterns
(hooks, psychological strategies, thumbnail styles, narration pacing,
posting times, content categories, video lengths, titles, keywords,
platform-specific performance), converts them into confidence-scored
recommendations routed to the engines that own each decision, grows the
append-only long-term strategy memory, and writes every ContentPackage
`learning_metadata` slot — so each published video makes the next one
more intelligent.

Pipeline position (PIPELINE_SPEC.md):

    Analytics Collection → Learning Feedback → (next run's inputs)

Recommendations flow back upstream via the `learning_recommendations`
context key and the per-engine guidance adapters in
`services/learning/recommendations.py` — this engine never imports or
calls another engine (Architecture Directive #1).

This module graduates the former planned stub (same key, additive output).
"""

from __future__ import annotations

from engines.contracts import ContractEngine
from services.analytics.models import LEARNING_ENGINE_VERSION
from services.learning.loop import run_learning


class LearningEngine(ContractEngine):
    """Agent 9 — continuous learning over historical performance data."""

    key = "learning"
    label = "Learning"
    icon = "🧠"
    description = (
        "Mine historical performance for winning patterns, score them with "
        "confidence, and feed recommendations back to every upstream engine."
    )
    version = LEARNING_ENGINE_VERSION
    input_contract = ["analytics_summary"]
    output_contract = ["learning_report", "learning_recommendations"]
    dependencies = ["analytics"]
    capabilities = [
        "learning", "pattern-mining", "recommendations", "feedback-loop",
        "long-term-memory", "experimentation", "reporting",
    ]

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        return run_learning(context)
