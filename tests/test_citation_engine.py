"""Tests for v6.0 Citation Engine and enhanced quality gate."""

from __future__ import annotations

import engines  # noqa: F401
from core.workflows import WorkflowEngine
from engines import registry
from services.research.citation import analyze_citations
from services.research.models import ResearchDocument


COMMAND = "Create 5 science shorts about black holes"


def _sample_research():
    doc = ResearchDocument(
        title="Black hole",
        summary="A black hole is a region of spacetime where gravity is extremely strong.",
        source="Wikipedia",
        url="https://en.wikipedia.org/wiki/Black_hole",
        publish_date="2024-01-01",
        provider="wikipedia",
        confidence=0.7,
        relevance=0.8,
        credibility_score=0.75,
        category="encyclopedia",
        evidence_strength=0.7,
        popularity=0.6,
        keywords=["black holes", "science"],
        topic_tags=["black holes", "science"],
    )
    return {
        "research_confidence": 0.7,
        "important_facts": ["Black holes have extremely strong gravity."],
        "documents": [doc.to_dict()],
        "research_brief": {"results": [{"title": doc.title, "url": doc.url, "source_name": doc.source, "provider": doc.provider}]},
    }


def test_citation_engine_attaches_citations():
    idea = {
        "hook": "What happens inside a black hole?",
        "script": "Black holes bend spacetime so strongly that not even light escapes.",
    }
    context = {"selected_ideas": [idea], "research": _sample_research()}
    registry.get_engine("citation").run(context)
    assert idea.get("citations")
    assert idea["citations"]["citation_list"]
    assert idea["citations"]["claim_confidence"] > 0
    assert idea.get("references")


def test_citation_flags_unsupported_absolute_claims():
    research = _sample_research()
    result = analyze_citations(
        "Shocking truth",
        "Everyone always fails at this and nothing can ever change.",
        research,
    )
    assert result["unsupported_claims"]


def test_quality_gate_blocks_low_research_confidence():
    context = {
        "command": COMMAND,
        "count": 5,
        "model": "",
        "threshold": 0,
        "research_settings": {
            "research_confidence_threshold": 0.99,
            "citation_required": False,
            "max_unsupported_claims": 5,
            "min_claim_confidence": 0.0,
        },
    }
    run = WorkflowEngine().execute("intelligence", context)
    assert run.succeeded
    assert context["quality_summary"]["held"] == len(context["ideas"])


def test_quality_gate_respects_citation_requirement():
    context = {
        "command": COMMAND,
        "count": 5,
        "model": "",
        "threshold": 0,
        "research_settings": {
            "research_confidence_threshold": 0.0,
            "citation_required": True,
            "max_unsupported_claims": 5,
            "min_claim_confidence": 0.0,
        },
    }
    run = WorkflowEngine().execute("intelligence", context)
    assert run.succeeded
    for idea in context["ideas"]:
        if idea["publishable"]:
            assert idea.get("citations", {}).get("citation_count", 0) > 0


def test_research_brief_includes_required_fields():
    context = {"command": COMMAND, "model": ""}
    updates = registry.get_engine("research").run(context)
    brief = updates["research"].get("research_brief", {})
    assert brief.get("results") is not None
    if brief["results"]:
        row = brief["results"][0]
        for field in (
            "title", "source_name", "url", "date", "summary",
            "credibility_score", "relevance_score", "confidence_score", "topic_tags",
        ):
            assert field in row
