"""Continuous Learning Engine — pre-production consult + self-improvement.

Runs early so every downstream engine receives historical guidance before
it creates. Post-publish mining remains in the `learning` engine.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.base import Engine
from services.learning.consult import consult_context

logger = get_logger(__name__)


class ContinuousLearningEngine(Engine):
    key = "continuous_learning"
    label = "Continuous Learning"
    icon = "🧠"
    description = (
        "Pre-production learning consult — search history, compare winners vs losers, "
        "predict performance, and feed recommendations into every downstream engine."
    )
    version = "1.0.0"

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        topic = str(
            context.get("subject")
            or context.get("topic")
            or context.get("command")
            or ""
        )
        platform = str(
            context.get("target_platform")
            or (context.get("platforms") or ["youtube_shorts"])[0]
        )
        runtime = int(context.get("target_runtime_sec") or context.get("video_length_sec") or 60)
        niche = str(context.get("niche") or context.get("category") or "")

        updates = consult_context(
            topic,
            niche=niche,
            platform=platform,
            runtime_sec=runtime,
            context=context,
        )
        # Attach brief onto candidates so Script / Psychology see it inline
        for candidate in context.get("candidates") or []:
            if isinstance(candidate, dict):
                candidate["learning_brief"] = updates.get("learning_brief")
                candidate["learning_predictions"] = updates.get("learning_predictions")

        log_event(
            logger,
            "continuous_learning.consulted",
            topic=topic[:80],
            status=(updates.get("learning_brief") or {}).get("status"),
            improvements=len(updates.get("suggested_improvements") or []),
        )
        return updates
