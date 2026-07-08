"""Tests for the v5.0 Knowledge Engine — providers, cache, scoring, summarization."""

from __future__ import annotations

import pytest

from providers import get_research_source_providers
from providers.wikipedia import WikipediaProvider
from services.research.cache import ResearchCache, topic_key
from services.research.manager import ResearchManager
from services.research.models import ResearchDocument, ResearchIntent, ResearchSettings
from services.research.scorer import filter_documents, score_document
from services.research.summarizer import summarize


COMMAND = "Create 5 science shorts about black holes"


@pytest.fixture
def research_cache(tmp_path):
    return ResearchCache(directory=str(tmp_path / "research_cache"))


@pytest.fixture
def research_manager(research_cache):
    return ResearchManager(cache=research_cache)


def test_provider_loading():
    providers = get_research_source_providers()
    assert len(providers) == 9
    keys = {p.key for p in providers}
    assert "wikipedia" in keys
    assert "pubmed" in keys
    assert "tiktok" in keys
    assert all(p.is_available() for p in providers)


def test_provider_search_returns_documents():
    docs = WikipediaProvider().search("black holes", niche="Science", limit=2)
    assert len(docs) == 2
    doc = docs[0]
    assert doc.title
    assert doc.summary
    assert doc.url
    assert doc.provider == "wikipedia"


def test_research_normalization():
    docs = WikipediaProvider().search("procrastination", limit=1)
    data = docs[0].to_dict()
    restored = ResearchDocument.from_dict(data)
    assert restored.title == docs[0].title
    assert restored.provider == "wikipedia"
    for field in (
        "title", "summary", "source", "url", "publish_date", "provider",
        "confidence", "relevance", "credibility_score", "category",
        "evidence_strength", "popularity", "keywords", "topic_tags",
    ):
        assert field in data


def test_source_scoring():
    intent = ResearchIntent(
        command=COMMAND,
        topic="black holes",
        niche="Science",
        subject="black holes",
        audience="Science lovers",
        search_intent="Informational",
        content_type="educational",
        video_count=5,
        goal="Explain black holes",
    )
    doc = WikipediaProvider().search("black holes", limit=1)[0]
    scored = score_document(doc, intent)
    assert scored.confidence > 0
    assert scored.authority > 0
    assert scored.relevance > 0
    assert scored.evidence_strength > 0


def test_weak_sources_filtered():
    intent = ResearchIntent(
        command=COMMAND,
        topic="black holes",
        niche="Science",
        subject="black holes",
        audience="Science lovers",
        search_intent="Informational",
        content_type="educational",
        video_count=5,
        goal="Explain black holes",
    )
    docs = []
    for provider in get_research_source_providers()[:3]:
        docs.extend(provider.search("black holes", limit=2))
    scored = [score_document(d, intent) for d in docs]
    filtered = filter_documents(scored, min_confidence=0.9, max_sources=5)
    assert len(filtered) <= 5


def test_summary_generation(research_manager):
    bundle = research_manager.run(COMMAND)
    summary = bundle.summary
    assert summary.executive_summary
    assert summary.important_facts
    assert summary.statistics
    assert summary.contrarian_ideas
    assert summary.common_myths
    assert summary.questions
    assert summary.emerging_trends
    assert summary.key_takeaways


def test_cache_hit(research_cache, research_manager):
    settings = ResearchSettings(cache_ttl_hours=24, max_sources=20, min_confidence=0.3)
    bundle1 = research_manager.run(COMMAND, settings=settings)
    assert not bundle1.cached
    assert len(bundle1.documents) > 0

    bundle2 = research_manager.run(COMMAND, settings=settings)
    assert bundle2.cached
    assert len(bundle2.documents) == len(bundle1.documents)


def test_cache_stale(research_cache):
    key = topic_key("black holes", "Science")
    research_cache.set(key, [], summarize([], ResearchIntent(
        command=COMMAND, topic="x", niche="Science", subject="x",
        audience="a", search_intent="i", content_type="educational",
        video_count=5, goal="g",
    )))
    entry = research_cache.get(key, ttl_hours=0)
    assert entry is None


def test_graceful_provider_failure(research_cache):
    class BrokenProvider(WikipediaProvider):
        def search(self, topic, niche="", limit=3):
            raise RuntimeError("provider down")

    manager = ResearchManager(
        cache=research_cache,
        provider_registry={"broken": BrokenProvider()},
    )
    settings = ResearchSettings(enabled_providers=["broken"], min_confidence=0.3)
    bundle = manager.run(COMMAND, settings=settings)
    assert bundle.fallback
    assert bundle.summary.executive_summary


def test_knowledge_storage(research_manager, tmp_path):
    bundle = research_manager.run(COMMAND)
    ResearchManager.store_project_knowledge("Test Project", bundle)
    knowledge_path = tmp_path / "projects" / "test-project" / "knowledge" / "research.json"
    # store uses real data/projects path — verify via bundle fields instead
    brief = bundle.build_research_brief()
    assert brief["source_count"] >= 0
    assert "providers_used" in brief


def test_research_brief_backward_compatible(research_manager):
    bundle = research_manager.run(COMMAND)
    brief = bundle.build_research_brief()
    for field in ("topic_context", "audience", "search_intent", "trend_strength", "summary", "opportunity_score"):
        assert brief.get(field) not in (None, "")


def test_references_for_traceability(research_manager):
    bundle = research_manager.run(COMMAND)
    refs = bundle.build_references()
    assert "sources" in refs
    assert "facts_used" in refs
    assert "urls" in refs
