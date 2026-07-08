"""arXiv research provider — live Atom API with demo fallback."""

from __future__ import annotations

import uuid

from providers._research_demo import make_document
from providers._research_http import fetch_xml, quote
from providers.research_source import ResearchSourceProvider
from services.research.models import ResearchDocument

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


class ArxivProvider(ResearchSourceProvider):
    key = "arxiv"
    label = "arXiv"

    def is_available(self) -> bool:
        return True

    def search(self, topic: str, niche: str = "", limit: int = 3) -> list:
        docs = self._live_search(topic, niche, limit)
        if docs:
            return docs
        return [
            make_document(
                topic, self.key, "arXiv", i, "preprint",
                "https://arxiv.org/abs/2401.{index:05d}",
                citation_count=20 + i * 15,
                popularity=0.55,
            )
            for i in range(min(limit, 3))
        ]

    def _live_search(self, topic: str, niche: str, limit: int) -> list:
        url = (
            "http://export.arxiv.org/api/query?"
            f"search_query=all:{quote(topic)}&start=0&max_results={limit}&sortBy=relevance"
        )
        root = fetch_xml(url)
        if root is None:
            return []

        documents = []
        for entry in root.findall("atom:entry", ATOM_NS):
            title = (entry.findtext("atom:title", default="", namespaces=ATOM_NS) or topic).strip()
            summary = (entry.findtext("atom:summary", default="", namespaces=ATOM_NS) or "")[:600].strip()
            published = (entry.findtext("atom:published", default="", namespaces=ATOM_NS) or "")[:10]
            link = ""
            for link_el in entry.findall("atom:link", ATOM_NS):
                if link_el.get("rel") == "alternate":
                    link = link_el.get("href", "")
                    break
            if not summary:
                continue
            documents.append(
                ResearchDocument(
                    doc_id=uuid.uuid4().hex[:12],
                    title=title.replace("\n", " "),
                    summary=summary.replace("\n", " "),
                    source="arXiv",
                    url=link or f"https://arxiv.org/search/?query={quote(topic)}",
                    publish_date=published,
                    provider=self.key,
                    confidence=0.0,
                    relevance=0.0,
                    credibility_score=0.0,
                    category="preprint",
                    evidence_strength=0.0,
                    popularity=0.55,
                    keywords=[topic.lower(), "arxiv", "preprint"],
                    topic_tags=[topic.lower(), niche.lower() if niche else "science", "preprint"],
                )
            )
        return documents[:limit]
