"""Ideation engine — the first live engine.

Parses a natural-language command, generates a content batch through the
active AI provider, and records the output into the Knowledge Base.
"""

from __future__ import annotations

from core import parsing
from core.ai import GenerationRequest, get_provider
from core.log import get_logger, log_event
from engines.base import Engine

logger = get_logger(__name__)


class IdeationEngine(Engine):
    key = "ideation"
    label = "Ideation"
    icon = "💡"
    description = "Turn a natural-language command into a batch of content ideas."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        command = context["command"]
        count = context.get("count", 10)
        model = context.get("model", "")

        niche = parsing.detect_niche(command)
        video_count = parsing.detect_video_count(command)
        subject = parsing.detect_subject(command, fallback=niche.lower())
        goal = parsing.build_goal(subject)

        provider = get_provider()
        log_event(logger, "ideation.run", provider=provider.name, niche=niche, count=count, model=model)
        generation = provider.generate_ideas(
            GenerationRequest(command=command, niche=niche, subject=subject, count=count, model=model)
        )

        self._record_knowledge(generation.ideas, niche, provider.name)

        updates = {
            "niche": niche,
            "video_count": video_count,
            "subject": subject,
            "goal": goal,
            "ideas": generation.ideas,
            "demo_mode": generation.demo_mode,
            "tokens_used": generation.tokens_used,
        }
        if generation.error:
            updates["error"] = generation.error
        return updates

    def _record_knowledge(self, ideas: list, niche: str, source: str) -> None:
        """Feed generated assets into the Knowledge Base for future learning."""
        from services.knowledge import CATEGORY, get_knowledge_base

        kb = get_knowledge_base()
        metadata = {"niche": niche, "source": source}
        try:
            for idea in ideas:
                if idea.get("hook"):
                    kb.add_entry(CATEGORY.HOOKS, idea["hook"], metadata)
                if idea.get("title"):
                    kb.add_entry(CATEGORY.TITLES, idea["title"], metadata)
                if idea.get("script"):
                    kb.add_entry(CATEGORY.SCRIPTS, idea["script"], metadata)
                if idea.get("thumbnail_concept"):
                    kb.add_entry(CATEGORY.THUMBNAILS, idea["thumbnail_concept"], metadata)
        except OSError as exc:
            log_event(logger, "ideation.knowledge_record_failed", level=30, error=str(exc))
