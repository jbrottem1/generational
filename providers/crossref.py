"""Crossref research provider — live REST API with demo fallback."""

from __future__ import annotations

import uuid

from providers._research_demo import make_document
from providers._research_http import fetch_json, quote
from providers.research_source import ResearchSourceProvider
from services.research.models import ResearchDocument


class CrossrefProvider(ResearchSourceProvider):
    key = "crossref"
    label = "Crossref"

    def is_available(self) -> bool:
        return True

    def search(self, topic: str, niche: str = "", limit: int = 3) -> list:
        docs = self._live_search(topic, niche, limit)
        if docs:
            return docs
        return [
            make_document(
                topic, self.key, "Crossref", i, "citation",
                "https://doi.org/10.1000/{slug}.{index}",
                citation_count=100 + i * 40,
                popularity=0.5,
            )
            for i in range(min(limit, 3))
        ]

    def _live_search(self, topic: str, niche: str, limit: int) -> list:
        url = f"https://api.crossref.org/works?query={quote(topic)}&rows={limit}&select=title,URL,abstract,published,author,is-referenced-by-count,container-title"
        payload = fetch_json(url)
        if not payload:
            return []

        items = payload.get("message", {}).get("items", [])
        documents = []
        for item in items:
            titles = item.get("title") or []
            title = titles[0] if titles else topic
            abstract = item.get("abstract") or f"Crossref indexed work related to {topic}."
            abstract = abstract.replace("<jats:p>", "").replace("</jats:p>", "")[:600]
            url_val = item.get("URL") or ""
            date_parts = item.get("published", {}).get("date-parts", [[]])
            publish_date = "-".join(str(p) for p in date_parts[0][:3]) if date_parts and date_parts[0] else ""
            citations = int(item.get("is-referenced-by-count") or 0)
            journal = (item.get("container-title") or ["Crossref"])[0]
            documents.append(
                ResearchDocument(
                    doc_id=uuid.uuid4().hex[:12],
                    title=title,
                    summary=f"{abstract} Published in {journal}.",
                    source="Crossref",
                    url=url_val,
                    publish_date=publish_date,
                    provider=self.key,
                    confidence=0.0,
                    relevance=0.0,
                    credibility_score=0.0,
                    category="citation",
                    evidence_strength=0.0,
                    popularity=0.5,
                    keywords=[topic.lower(), "crossref", "citation"],
                    topic_tags=[topic.lower(), niche.lower() if niche else "research", "cited-work"],
                    citation_count=citations,
                )
            )
        return documents[:limit]
