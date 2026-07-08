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


def get_llm_provider() -> LLMProvider:
    from core.ai import get_provider

    provider = get_provider()
    if hasattr(provider, "generate_json"):
        return provider  # type: ignore[return-value]
    return provider  # type: ignore[return-value]


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
    "get_llm_provider",
    "get_voice_provider",
]
