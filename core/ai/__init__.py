"""AI provider selection.

`get_provider()` returns the best currently-available provider: OpenAI when
a key is configured, otherwise the demo provider. New providers plug in here
without touching any calling code.
"""

from __future__ import annotations

from core.ai.base import AIProvider, GenerationRequest, GenerationResult
from core.ai.demo_provider import DemoProvider
from core.ai.openai_provider import OpenAIProvider

__all__ = [
    "AIProvider",
    "GenerationRequest",
    "GenerationResult",
    "get_provider",
    "is_demo_mode",
]

_openai = OpenAIProvider()
_demo = DemoProvider()


def get_provider() -> AIProvider:
    return _openai if _openai.is_available() else _demo


def is_demo_mode() -> bool:
    return not _openai.is_available()
