"""Audience Intelligence — psychological enrichment + learning layer for productions.

Composes (does not duplicate): Psychology, Research, Publishing Intelligence, Creative Performance Lab.
"""

from __future__ import annotations

from services.audience_intelligence.adapters import (
    apply_guidance_to_script_context,
    script_generation_guidance,
)
from services.audience_intelligence.analytics_interfaces import (
    list_analytics_interfaces,
    get_analytics_provider,
)
from services.audience_intelligence.brief import attach_brief_to_candidate, build_creative_brief
from services.audience_intelligence.builder import analyze_topic, enrich_candidate, enrich_queue_item
from services.audience_intelligence.memory import (
    KNOWLEDGE_CATEGORIES,
    add_lesson,
    load_knowledge,
    search_lessons,
    seed_bootstrap_lessons,
)
from services.audience_intelligence.models import (
    FORMATS,
    PSYCH_FIELDS,
    AudienceIntelligenceReport,
    AudienceProfile,
    CreativeDirectives,
    EngagementEstimates,
    PsychologicalDrivers,
)
from services.audience_intelligence.post_review import review_production_audience

__all__ = [
    "FORMATS",
    "KNOWLEDGE_CATEGORIES",
    "PSYCH_FIELDS",
    "AudienceIntelligenceReport",
    "AudienceProfile",
    "CreativeDirectives",
    "EngagementEstimates",
    "PsychologicalDrivers",
    "add_lesson",
    "analyze_topic",
    "apply_guidance_to_script_context",
    "attach_brief_to_candidate",
    "build_creative_brief",
    "enrich_candidate",
    "enrich_queue_item",
    "get_analytics_provider",
    "list_analytics_interfaces",
    "load_knowledge",
    "review_production_audience",
    "script_generation_guidance",
    "search_lessons",
    "seed_bootstrap_lessons",
]
