"""Research Manager — orchestrates the Knowledge Engine research flow."""

from __future__ import annotations

import json
import os

from core import parsing
from core.ai import is_demo_mode
from core.constants import DEFAULT_RESEARCH_SETTINGS, RESEARCH_PROVIDERS
from core.log import get_logger, log_event
from services.research.cache import ResearchCache, get_research_cache, topic_key
from services.research.models import ResearchBundle, ResearchIntent, ResearchSettings
from services.research.scorer import filter_documents, score_document
from services.research.summarizer import summarize

logger = get_logger(__name__)

AUDIENCES = {
    "Psychology": "Self-improvement viewers, 18-34",
    "AI & Future Tech": "Tech-curious early adopters, 18-40",
    "Dark History": "History and mystery fans, 20-45",
    "Space": "Science and space enthusiasts, 16-40",
    "Finance": "Aspiring investors and savers, 20-40",
    "Health": "Wellness-focused viewers, 20-45",
    "Science": "Curious science lovers, 16-40",
    "General Content": "Curious short-form viewers, 16-40",
}


def _detect_search_intent(command: str) -> str:
    lower = command.lower()
    if "how" in lower:
        return "Instructional (how-to)"
    if "why" in lower or "what" in lower:
        return "Informational curiosity"
    if "story" in lower or "history" in lower:
        return "Narrative discovery"
    return "Entertainment discovery"


_PROJECT_KNOWLEDGE_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "projects",
)


class ResearchManager:
    """Coordinates intent parsing, provider queries, scoring, caching, and summarization."""

    def __init__(
        self,
        cache: ResearchCache | None = None,
        provider_registry: "dict | None" = None,
    ) -> None:
        self.cache = cache or get_research_cache()
        self._registry = provider_registry or _build_provider_registry()

    def run(
        self,
        command: str,
        settings: ResearchSettings | None = None,
        project_name: str | None = None,
    ) -> ResearchBundle:
        settings = settings or ResearchSettings.from_dict(DEFAULT_RESEARCH_SETTINGS)
        intent = self.parse_intent(command)
        key = topic_key(intent.topic, intent.niche)

        cached = self.cache.get(key, settings.cache_ttl_hours)
        if cached:
            documents = self.cache.load_documents(cached)
            summary = self.cache.load_summary(cached)
            bundle = ResearchBundle(
                intent=intent,
                documents=documents,
                summary=summary,
                providers_used=cached.get("providers_used", []),
                cached=True,
            )
            if project_name:
                self.store_project_knowledge(project_name, bundle)
            return bundle

        documents, providers_used, fallback = self._collect_documents(intent, settings)
        min_confidence = settings.min_confidence
        if settings.science_medical_strict and intent.niche in {"Science", "Health"}:
            min_confidence = min(0.95, min_confidence + 0.15)
        scored = [score_document(doc, intent) for doc in documents]
        filtered = filter_documents(scored, min_confidence, settings.max_sources)

        if not filtered and not fallback:
            log_event(logger, "research.all_filtered", topic=intent.topic)
            summary = summarize([], intent)
            bundle = ResearchBundle(
                intent=intent,
                documents=[],
                summary=summary,
                providers_used=providers_used,
                fallback=True,
            )
        else:
            summary = summarize(filtered, intent)
            bundle = ResearchBundle(
                intent=intent,
                documents=filtered,
                summary=summary,
                providers_used=providers_used,
                fallback=fallback,
            )
            if filtered:
                self.cache.set(key, filtered, summary)

        if project_name:
            self.store_project_knowledge(project_name, bundle)

        log_event(
            logger,
            "research.completed",
            topic=intent.topic,
            sources=len(bundle.documents),
            cached=False,
            fallback=fallback,
        )
        return bundle

    @staticmethod
    def parse_intent(command: str) -> ResearchIntent:
        niche = parsing.detect_niche(command)
        video_count = parsing.detect_video_count(command)
        subject = parsing.detect_subject(command, fallback=niche.lower())
        goal = parsing.build_goal(subject)
        audience = AUDIENCES.get(niche, AUDIENCES["General Content"])
        search_intent = _detect_search_intent(command)
        content_type = _detect_content_type(command, niche)
        return ResearchIntent(
            command=command,
            topic=subject,
            niche=niche,
            subject=subject,
            audience=audience,
            search_intent=search_intent,
            content_type=content_type,
            video_count=video_count,
            goal=goal,
        )

    def _collect_documents(
        self,
        intent: ResearchIntent,
        settings: ResearchSettings,
    ) -> tuple[list, list[str], bool]:
        enabled = settings.enabled_providers or list(RESEARCH_PROVIDERS)
        providers = [
            self._registry[key]
            for key in enabled
            if key in self._registry and self._registry[key].is_available()
        ]

        if not providers:
            log_event(logger, "research.no_providers", level=30)
            return [], [], True

        per_provider = settings.per_provider_limit(len(providers))
        all_docs = []
        used = []
        failures = 0

        for provider in providers:
            try:
                docs = provider.search(intent.topic, intent.niche, limit=per_provider)
                if docs:
                    all_docs.extend(docs)
                    used.append(provider.key)
            except Exception as exc:
                failures += 1
                log_event(
                    logger,
                    "research.provider_failed",
                    level=30,
                    provider=provider.key,
                    error=str(exc),
                )

        if not all_docs:
            log_event(logger, "research.all_providers_failed", level=30, failures=failures)
            return [], used, True

        return all_docs, used, False

    @staticmethod
    def store_project_knowledge(project_name: str, bundle: ResearchBundle) -> None:
        """Persist research into a project's Knowledge folder."""
        from core.storage.json_store import _slugify

        slug = _slugify(project_name)
        knowledge_dir = os.path.join(_PROJECT_KNOWLEDGE_ROOT, slug, "knowledge")
        os.makedirs(knowledge_dir, exist_ok=True)
        path = os.path.join(knowledge_dir, "research.json")
        with open(path, "w", encoding="utf-8") as file:
            json.dump(bundle.to_dict(), file, indent=2)
        log_event(logger, "research.project_knowledge_stored", project=project_name)


def _detect_content_type(command: str, niche: str) -> str:
    lower = command.lower()
    educational_niches = {"Science", "Health", "Finance", "Psychology"}
    if niche in educational_niches:
        return "educational"
    if any(word in lower for word in ("learn", "explain", "science", "study", "research", "how", "why")):
        return "educational"
    if any(word in lower for word in ("funny", "viral", "entertain", "story", "drama")):
        return "entertainment"
    return "educational"


def _build_provider_registry() -> dict:
    from providers.arxiv import ArxivProvider
    from providers.crossref import CrossrefProvider
    from providers.news import NewsProvider
    from providers.pubmed import PubMedProvider
    from providers.reddit import RedditProvider
    from providers.tiktok import TikTokProvider
    from providers.trends import TrendsProvider
    from providers.wikipedia import WikipediaProvider
    from providers.youtube import YouTubeProvider

    instances = [
        WikipediaProvider(),
        PubMedProvider(),
        ArxivProvider(),
        CrossrefProvider(),
        NewsProvider(),
        TrendsProvider(),
        YouTubeProvider(),
        RedditProvider(),
        TikTokProvider(),
    ]
    return {p.key: p for p in instances}


_manager: "ResearchManager | None" = None


def get_research_manager() -> ResearchManager:
    global _manager
    if _manager is None:
        _manager = ResearchManager()
    return _manager


def run_research(
    command: str,
    settings: ResearchSettings | None = None,
    project_name: str | None = None,
) -> ResearchBundle:
    return get_research_manager().run(command, settings=settings, project_name=project_name)


def build_research_context(
    command: str,
    settings: ResearchSettings | None = None,
    project_name: str | None = None,
) -> dict:
    """Full research stage output for the workflow engine."""
    bundle = run_research(command, settings=settings, project_name=project_name)
    intent = bundle.intent
    return {
        "niche": intent.niche,
        "video_count": intent.video_count,
        "subject": intent.subject,
        "goal": intent.goal,
        "demo_mode": is_demo_mode(),
        "research": bundle.build_research_brief(),
        "research_bundle": bundle.to_dict(),
        "research_references": bundle.build_references(),
    }
