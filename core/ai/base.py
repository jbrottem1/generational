"""AI provider interface.

Any content-generation backend (OpenAI today; Anthropic, local models, etc.
later) implements this interface. Callers only ever talk to a provider
through `generate_ideas`, so swapping or adding providers never touches UI
or service code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class GenerationRequest:
    """What the caller wants generated."""

    def __init__(self, command: str, niche: str, subject: str, count: int, model: str) -> None:
        self.command = command
        self.niche = niche
        self.subject = subject
        self.count = count
        self.model = model


class GenerationResult:
    """What a provider returns. `error` is set when a fallback occurred."""

    def __init__(self, ideas: list, demo_mode: bool, tokens_used: int = 0, error: str = "") -> None:
        self.ideas = ideas
        self.demo_mode = demo_mode
        self.tokens_used = tokens_used
        self.error = error


class AIProvider(ABC):
    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """Whether this provider can currently generate real content."""

    @abstractmethod
    def generate_ideas(self, request: GenerationRequest) -> GenerationResult:
        """Generate content ideas. Must not raise — return a fallback result instead."""

    def generate_json(self, system_prompt: str, user_prompt: str, model: str) -> "tuple[dict | None, int]":
        """General-purpose structured reasoning call: returns (data, tokens_used).

        Returns (None, 0) when the provider cannot serve the call (not
        available, call failed, bad JSON) — callers fall back to their
        deterministic heuristics. This is the extension point the whole
        intelligence pipeline uses, so swapping providers/models never
        touches engine code.
        """
        return None, 0
