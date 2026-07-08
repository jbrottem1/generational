"""Citation engine — stage 8: source-backed claim analysis for every script."""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.base import Engine
from services.research.citation import analyze_citations
from services.research.models import ResearchDocument

logger = get_logger(__name__)


class CitationEngine(Engine):
    key = "citation"
    label = "Citation"
    icon = "📎"
    description = "Map scripts to research sources; flag unsupported claims."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        selected = context.get("selected_ideas", [])
        research = context.get("research", {})
        documents = [ResearchDocument.from_dict(d) for d in research.get("documents", [])]

        for idea in selected:
            citations = analyze_citations(
                idea.get("hook", ""),
                idea.get("script", ""),
                research,
                documents,
            )
            idea["citations"] = citations
            idea["references"] = {
                "sources": citations["supporting_sources"],
                "facts_used": research.get("important_facts", [])[:5],
                "urls": [c["url"] for c in citations["citation_list"] if c.get("url")],
                "citation_list": citations["citation_list"],
            }

        log_event(logger, "citation.analyzed", scripts=len(selected))
        return {"selected_ideas": selected}
