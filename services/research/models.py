"""Strongly typed research data models for the Knowledge Engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ResearchSettings:
    """User-configurable research parameters (Settings tab + defaults)."""

    enabled_providers: list[str] = field(default_factory=list)
    cache_ttl_hours: int = 24
    max_sources: int = 20
    min_confidence: float = 0.4

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ResearchSettings":
        return cls(
            enabled_providers=list(data.get("enabled_providers", [])),
            cache_ttl_hours=int(data.get("cache_ttl_hours", 24)),
            max_sources=int(data.get("max_sources", 20)),
            min_confidence=float(data.get("min_confidence", 0.4)),
        )


@dataclass
class ResearchIntent:
    """Parsed command intent — step 1 of the research flow."""

    command: str
    topic: str
    niche: str
    subject: str
    audience: str
    search_intent: str
    content_type: str  # "educational" | "entertainment"
    video_count: int
    goal: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ResearchDocument:
    """Normalized research document from any provider."""

    title: str
    summary: str
    source: str
    url: str
    publish_date: str
    provider: str
    confidence: float
    relevance: float
    category: str
    evidence_strength: float
    popularity: float
    keywords: list[str] = field(default_factory=list)
    citation_count: int = 0
    authority: float = 0.0
    freshness: float = 0.0
    scientific_reliability: float = 0.0
    doc_id: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ResearchDocument":
        return cls(
            title=data.get("title", ""),
            summary=data.get("summary", ""),
            source=data.get("source", ""),
            url=data.get("url", ""),
            publish_date=data.get("publish_date", ""),
            provider=data.get("provider", ""),
            confidence=float(data.get("confidence", 0)),
            relevance=float(data.get("relevance", 0)),
            category=data.get("category", ""),
            evidence_strength=float(data.get("evidence_strength", 0)),
            popularity=float(data.get("popularity", 0)),
            keywords=list(data.get("keywords", [])),
            citation_count=int(data.get("citation_count", 0)),
            authority=float(data.get("authority", 0)),
            freshness=float(data.get("freshness", 0)),
            scientific_reliability=float(data.get("scientific_reliability", 0)),
            doc_id=data.get("doc_id", ""),
        )


@dataclass
class ResearchSummary:
    """Structured research summary — input for idea generation."""

    executive_summary: str
    important_facts: list[str]
    statistics: list[str]
    contrarian_ideas: list[str]
    common_myths: list[str]
    questions: list[str]
    emerging_trends: list[str]
    key_takeaways: list[str]
    topic_context: str = ""
    trend_strength: int = 60
    opportunity_score: int = 60

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ResearchSummary":
        return cls(
            executive_summary=data.get("executive_summary", ""),
            important_facts=list(data.get("important_facts", [])),
            statistics=list(data.get("statistics", [])),
            contrarian_ideas=list(data.get("contrarian_ideas", [])),
            common_myths=list(data.get("common_myths", [])),
            questions=list(data.get("questions", [])),
            emerging_trends=list(data.get("emerging_trends", [])),
            key_takeaways=list(data.get("key_takeaways", [])),
            topic_context=data.get("topic_context", ""),
            trend_strength=int(data.get("trend_strength", 60)),
            opportunity_score=int(data.get("opportunity_score", 60)),
        )

    @property
    def summary_text(self) -> str:
        """Backward-compatible single-string summary for downstream engines."""
        return self.executive_summary or self.topic_context


@dataclass
class ResearchBundle:
    """Complete research output from the Knowledge Engine."""

    intent: ResearchIntent
    documents: list[ResearchDocument]
    summary: ResearchSummary
    providers_used: list[str]
    cached: bool = False
    fallback: bool = False

    def to_dict(self) -> dict:
        return {
            "intent": self.intent.to_dict(),
            "documents": [d.to_dict() for d in self.documents],
            "summary": self.summary.to_dict(),
            "providers_used": self.providers_used,
            "cached": self.cached,
            "fallback": self.fallback,
        }

    def build_research_brief(self) -> dict[str, Any]:
        """Merge into context['research'] — preserves v2/v4 contract + v5 fields."""
        s = self.summary
        return {
            "topic_context": s.topic_context or s.executive_summary,
            "audience": self.intent.audience,
            "search_intent": self.intent.search_intent,
            "content_type": self.intent.content_type,
            "trend_strength": s.trend_strength,
            "summary": s.summary_text,
            "opportunity_score": s.opportunity_score,
            "executive_summary": s.executive_summary,
            "important_facts": s.important_facts,
            "statistics": s.statistics,
            "contrarian_ideas": s.contrarian_ideas,
            "common_myths": s.common_myths,
            "questions": s.questions,
            "emerging_trends": s.emerging_trends,
            "key_takeaways": s.key_takeaways,
            "sources": [
                {"title": d.title, "url": d.url, "provider": d.provider, "confidence": d.confidence}
                for d in self.documents[:10]
            ],
            "documents": [d.to_dict() for d in self.documents],
            "source_count": len(self.documents),
            "cached": self.cached,
            "providers_used": self.providers_used,
            "fallback": self.fallback,
        }

    def build_references(self) -> dict:
        """Traceability payload attached to generated scripts."""
        facts = s.important_facts if (s := self.summary) else []
        return {
            "sources": [
                {"title": d.title, "url": d.url, "provider": d.provider}
                for d in self.documents[:5]
            ],
            "facts_used": facts[:5],
            "urls": [d.url for d in self.documents[:5] if d.url],
        }
