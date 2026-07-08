"""Shared helpers for demo research source providers."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from services.research.models import ResearchDocument


def _seed(topic: str, provider: str, index: int) -> int:
    raw = f"{provider}:{topic}:{index}"
    return int(hashlib.md5(raw.encode()).hexdigest()[:8], 16)


def _date(days_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%d")


def make_document(
    topic: str,
    provider: str,
    source: str,
    index: int,
    category: str,
    url_template: str,
    *,
    citation_count: int = 0,
    popularity: float = 0.0,
) -> ResearchDocument:
    seed = _seed(topic, provider, index)
    title = f"{topic.title()}: {['Overview', 'Recent findings', 'Key insights'][index % 3]}"
    summary = (
        f"Research on {topic} from {source} highlights important patterns relevant to "
        f"short-form content. Finding #{index + 1} emphasizes evidence-based framing."
    )
    slug = topic.lower().replace(" ", "-")
    return ResearchDocument(
        doc_id=uuid.uuid4().hex[:12],
        title=title,
        summary=summary,
        source=source,
        url=url_template.format(slug=slug, index=index),
        publish_date=_date(seed % 900 + 30),
        provider=provider,
        confidence=0.0,
        relevance=0.0,
        category=category,
        evidence_strength=0.0,
        popularity=popularity or round(0.4 + (seed % 60) / 100, 2),
        keywords=[topic.lower(), category, provider],
        citation_count=citation_count or seed % 500,
    )
