"""PubMed research provider — live NCBI E-utilities with demo fallback."""

from __future__ import annotations

import uuid

from providers._research_demo import make_document
from providers._research_http import fetch_json, quote
from providers.research_source import ResearchSourceProvider
from services.research.models import ResearchDocument


class PubMedProvider(ResearchSourceProvider):
    key = "pubmed"
    label = "PubMed"

    def is_available(self) -> bool:
        return True

    def search(self, topic: str, niche: str = "", limit: int = 3) -> list:
        docs = self._live_search(topic, niche, limit)
        if docs:
            return docs
        return [
            make_document(
                topic, self.key, "PubMed", i, "scientific",
                "https://pubmed.ncbi.nlm.nih.gov/{index}/",
                citation_count=50 + i * 30,
                popularity=0.6,
            )
            for i in range(min(limit, 3))
        ]

    def _live_search(self, topic: str, niche: str, limit: int) -> list:
        search_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
            f"db=pubmed&term={quote(topic)}&retmax={limit}&retmode=json&sort=relevance"
        )
        search_data = fetch_json(search_url)
        if not search_data:
            return []

        ids = search_data.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []

        summary_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?"
            f"db=pubmed&id={','.join(ids)}&retmode=json"
        )
        summary_data = fetch_json(summary_url)
        if not summary_data:
            return []

        result = summary_data.get("result", {})
        documents = []
        for pmid in ids:
            item = result.get(pmid, {})
            if not item or pmid == "uids":
                continue
            title = item.get("title", topic)
            pub_date = item.get("pubdate", "")[:10]
            summary = f"PubMed indexed study on {topic}. Journal: {item.get('source', 'unknown')}."
            documents.append(
                ResearchDocument(
                    doc_id=uuid.uuid4().hex[:12],
                    title=title.rstrip("."),
                    summary=summary,
                    source="PubMed",
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    publish_date=pub_date,
                    provider=self.key,
                    confidence=0.0,
                    relevance=0.0,
                    credibility_score=0.0,
                    category="scientific",
                    evidence_strength=0.0,
                    popularity=0.6,
                    keywords=[topic.lower(), "pubmed", "medical"],
                    topic_tags=[topic.lower(), niche.lower() if niche else "science", "peer-reviewed"],
                    citation_count=int(item.get("pmcrefcount", 0) or 0),
                )
            )
        return documents[:limit]
