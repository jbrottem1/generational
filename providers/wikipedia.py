"""Wikipedia research provider — live MediaWiki API with demo fallback."""

from __future__ import annotations

import uuid

from providers._research_demo import make_document
from providers._research_http import fetch_json, quote
from providers.research_source import ResearchSourceProvider
from services.research.models import ResearchDocument


class WikipediaProvider(ResearchSourceProvider):
    key = "wikipedia"
    label = "Wikipedia"

    def is_available(self) -> bool:
        return True

    def search(self, topic: str, niche: str = "", limit: int = 3) -> list:
        docs = self._live_search(topic, limit)
        if docs:
            return docs
        return [
            make_document(
                topic, self.key, "Wikipedia", i, "encyclopedia",
                "https://en.wikipedia.org/wiki/{slug}",
                citation_count=0,
                popularity=0.7,
            )
            for i in range(min(limit, 3))
        ]

    def _live_search(self, topic: str, limit: int) -> list:
        search_url = (
            "https://en.wikipedia.org/w/api.php?"
            f"action=query&list=search&srsearch={quote(topic)}&format=json&utf8=1&srlimit={limit}"
        )
        payload = fetch_json(search_url)
        if not payload:
            return []

        hits = payload.get("query", {}).get("search", [])
        if not hits:
            return []

        page_ids = "|".join(str(hit["pageid"]) for hit in hits[:limit])
        detail_url = (
            "https://en.wikipedia.org/w/api.php?"
            f"action=query&prop=extracts|info&exintro=1&explaintext=1&inprop=url"
            f"&pageids={page_ids}&format=json"
        )
        details = fetch_json(detail_url)
        if not details:
            return []

        pages = details.get("query", {}).get("pages", {})
        documents = []
        for page in pages.values():
            title = page.get("title", topic)
            summary = (page.get("extract") or "")[:600]
            url = page.get("fullurl") or f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"
            if not summary:
                continue
            documents.append(
                ResearchDocument(
                    doc_id=uuid.uuid4().hex[:12],
                    title=title,
                    summary=summary,
                    source="Wikipedia",
                    url=url,
                    publish_date="",
                    provider=self.key,
                    confidence=0.0,
                    relevance=0.0,
                    credibility_score=0.0,
                    category="encyclopedia",
                    evidence_strength=0.0,
                    popularity=0.7,
                    keywords=[topic.lower(), niche.lower() if niche else "general", "wikipedia"],
                    topic_tags=[topic.lower(), "encyclopedia"],
                )
            )
        return documents[:limit]
