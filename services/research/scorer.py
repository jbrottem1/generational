"""Source quality scoring — authority, freshness, relevance, and filtering."""

from __future__ import annotations

from datetime import datetime, timezone

from services.research.models import ResearchDocument, ResearchIntent

# Provider authority baselines (0-1) — higher = more trusted for factual content.
PROVIDER_AUTHORITY = {
    "pubmed": 0.95,
    "arxiv": 0.90,
    "crossref": 0.88,
    "wikipedia": 0.75,
    "news": 0.65,
    "youtube": 0.55,
    "reddit": 0.45,
    "trends": 0.50,
}

# Scientific reliability by provider.
PROVIDER_SCIENTIFIC = {
    "pubmed": 0.98,
    "arxiv": 0.95,
    "crossref": 0.90,
    "wikipedia": 0.70,
    "news": 0.55,
    "youtube": 0.40,
    "reddit": 0.30,
    "trends": 0.35,
}


def _parse_date(date_str: str) -> "datetime | None":
    if not date_str:
        return None
    for fmt, length in (("%Y-%m-%d", 10), ("%Y-%m", 7), ("%Y", 4)):
        try:
            dt = datetime.strptime(date_str[:length], fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def freshness_score(publish_date: str) -> float:
    """0-1 score — newer sources score higher."""
    parsed = _parse_date(publish_date)
    if parsed is None:
        return 0.5
    age_days = max(0, (datetime.now(timezone.utc) - parsed).days)
    if age_days <= 30:
        return 1.0
    if age_days <= 180:
        return 0.85
    if age_days <= 365:
        return 0.65
    if age_days <= 730:
        return 0.45
    return 0.25


def relevance_score(doc: ResearchDocument, intent: ResearchIntent) -> float:
    """Keyword overlap between document and research intent."""
    topic_words = set(w.lower() for w in (intent.topic + " " + intent.subject).split() if len(w) > 2)
    text = f"{doc.title} {doc.summary} {' '.join(doc.keywords)}".lower()
    if not topic_words:
        return 0.5
    hits = sum(1 for word in topic_words if word in text)
    return min(1.0, 0.3 + hits / max(len(topic_words), 1))


def citation_boost(citation_count: int) -> float:
    if citation_count >= 1000:
        return 1.0
    if citation_count >= 100:
        return 0.85
    if citation_count >= 10:
        return 0.65
    if citation_count >= 1:
        return 0.45
    return 0.2


def score_document(doc: ResearchDocument, intent: ResearchIntent) -> ResearchDocument:
    """Fill all quality dimensions and compute overall confidence."""
    authority = PROVIDER_AUTHORITY.get(doc.provider, 0.5)
    scientific = PROVIDER_SCIENTIFIC.get(doc.provider, 0.4)
    freshness = freshness_score(doc.publish_date)
    relevance = relevance_score(doc, intent)
    popularity = min(1.0, doc.popularity if doc.popularity else 0.5)
    citation_factor = citation_boost(doc.citation_count)

    evidence = (
        0.35 * authority
        + 0.25 * scientific
        + 0.20 * citation_factor
        + 0.20 * relevance
    )

    confidence = (
        0.25 * authority
        + 0.20 * freshness
        + 0.15 * popularity
        + 0.20 * scientific
        + 0.10 * citation_factor
        + 0.10 * relevance
    )

    doc.authority = round(authority, 3)
    doc.freshness = round(freshness, 3)
    doc.scientific_reliability = round(scientific, 3)
    doc.relevance = round(relevance, 3)
    doc.evidence_strength = round(evidence, 3)
    doc.confidence = round(confidence, 3)
    return doc


def filter_documents(
    documents: list[ResearchDocument],
    min_confidence: float,
    max_sources: int,
) -> list[ResearchDocument]:
    """Remove weak sources and cap total count."""
    scored = [d for d in documents if d.confidence >= min_confidence]
    scored.sort(key=lambda d: (d.confidence, d.relevance), reverse=True)
    return scored[:max_sources]
