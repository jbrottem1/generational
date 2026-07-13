"""Provider registry and factories.

Each factory returns the best available provider for its capability.
Swap implementations here — engines never import vendor SDKs directly.
"""

from __future__ import annotations

import os

from providers.analytics_provider import AnalyticsProvider
from providers.image_provider import ImageProvider
from providers.llm import LLMProvider
from providers.music_provider import MusicProvider
from providers.publishing_provider import PublishingProvider
from providers.research_provider import ResearchProvider
from providers.seo_provider import SEOProvider
from providers.research_source import ResearchSourceProvider
from providers.trend_provider import TrendProvider
from providers.video_provider import VideoProvider
from providers.voice.base import VoiceMode, VoiceProvider
from providers.voice.demo_ai import DemoAIVoiceProvider
from providers.voice.recorded import RecordedVoiceProvider

_DEFAULT_RECORDINGS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "voice_recordings"
)

_ai_voice = DemoAIVoiceProvider()
_recorded_voice = RecordedVoiceProvider(_DEFAULT_RECORDINGS)
_research_sources: "list[ResearchSourceProvider] | None" = None


def _load_research_sources() -> list[ResearchSourceProvider]:
    from providers.arxiv import ArxivProvider
    from providers.crossref import CrossrefProvider
    from providers.news import NewsProvider
    from providers.pubmed import PubMedProvider
    from providers.reddit import RedditProvider
    from providers.tiktok import TikTokProvider
    from providers.trends import TrendsProvider
    from providers.wikipedia import WikipediaProvider
    from providers.youtube import YouTubeProvider

    return [
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


def get_research_source_providers(enabled: "list[str] | None" = None) -> list[ResearchSourceProvider]:
    """Return enabled research source providers. Drop a file in providers/ and register here."""
    global _research_sources
    if _research_sources is None:
        _research_sources = _load_research_sources()
    if enabled is None:
        return [p for p in _research_sources if p.is_available()]
    return [p for p in _research_sources if p.key in enabled and p.is_available()]


class _RuntimeLLMProvider(LLMProvider):
    """LLMProvider adapter over ProviderRuntime (no direct core.ai calls)."""

    name = "provider_runtime"
    label = "Provider Runtime LLM"

    def is_available(self) -> bool:
        return True

    def generate_json(self, system_prompt: str, user_prompt: str, model: str) -> "tuple[dict | None, int]":
        from services.provider_runtime.engine_api import runtime_generate_json

        data, tokens, _provider = runtime_generate_json(system_prompt, user_prompt, model=model)
        return data, tokens


def get_llm_provider() -> LLMProvider:
    """Return the ProviderRuntime-backed LLM provider (never a vendor SDK)."""
    return _RuntimeLLMProvider()


def get_voice_provider(mode: str = VoiceMode.AI) -> VoiceProvider:
    if mode == VoiceMode.RECORDED and _recorded_voice.is_available():
        return _recorded_voice
    return _ai_voice


__all__ = [
    "LLMProvider",
    "ResearchProvider",
    "SEOProvider",
    "VoiceProvider",
    "VoiceMode",
    "ImageProvider",
    "VideoProvider",
    "MusicProvider",
    "PublishingProvider",
    "AnalyticsProvider",
    "TrendProvider",
    "ResearchSourceProvider",
    "get_llm_provider",
    "get_voice_provider",
    "get_research_source_providers",
]
