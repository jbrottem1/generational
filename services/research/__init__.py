"""Knowledge Engine — modular research platform for data-backed content."""

from services.research.models import ResearchDocument, ResearchIntent, ResearchSettings, ResearchSummary

__all__ = [
    "ResearchDocument",
    "ResearchIntent",
    "ResearchSettings",
    "ResearchSummary",
    "ResearchManager",
    "get_research_manager",
    "run_research",
]


def __getattr__(name: str):
    if name in ("ResearchManager", "get_research_manager", "run_research"):
        from services.research.manager import ResearchManager, get_research_manager, run_research

        return {"ResearchManager": ResearchManager, "get_research_manager": get_research_manager, "run_research": run_research}[name]
    raise AttributeError(name)
