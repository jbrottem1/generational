"""Research engine — stage 1 of the intelligence pipeline.

Delegates to the v5.0 Knowledge Engine (services/research/) to gather,
score, and summarize data from multiple research providers before any
content is generated. Falls back to heuristics if all providers fail.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.base import Engine
from services.research.manager import build_research_context
from services.research.models import ResearchSettings

logger = get_logger(__name__)


class ResearchEngine(Engine):
    key = "research"
    label = "Research"
    icon = "🔍"
    description = "Knowledge Engine — multi-source research, scoring, and summary."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        settings_data = context.get("research_settings")
        settings = ResearchSettings.from_dict(settings_data) if settings_data else None
        project_name = context.get("project_name")

        result = build_research_context(
            context["command"],
            settings=settings,
            project_name=project_name,
        )

        research = result["research"]
        log_event(
            logger,
            "research.completed",
            niche=result["niche"],
            subject=result["subject"],
            sources=research.get("source_count", 0),
            cached=research.get("cached", False),
            fallback=research.get("fallback", False),
        )
        return result
