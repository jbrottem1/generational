"""Generational Knowledge Atlas — permanent visual knowledge library."""

from services.knowledge_atlas.catalog import AtlasAsset, get_asset, load_atlas
from services.knowledge_atlas.feedback import record_lesson_visuals
from services.knowledge_atlas.planner import plan_visual_evidence
from services.knowledge_atlas.search import search_visuals

__all__ = [
    "AtlasAsset",
    "get_asset",
    "load_atlas",
    "plan_visual_evidence",
    "record_lesson_visuals",
    "search_visuals",
]
