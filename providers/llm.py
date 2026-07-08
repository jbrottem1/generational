"""LLM provider interface — wraps structured and free-text generation."""

from __future__ import annotations

from abc import abstractmethod

from providers.base import Provider


class LLMProvider(Provider):
    @abstractmethod
    def generate_json(self, system_prompt: str, user_prompt: str, model: str) -> "tuple[dict | None, int]":
        """Returns (parsed_json, tokens_used) or (None, 0) on failure."""

    def generate_text(self, system_prompt: str, user_prompt: str, model: str) -> "tuple[str, int]":
        data, tokens = self.generate_json(system_prompt, user_prompt, model)
        if data is None:
            return "", 0
        return str(data.get("text", data)), tokens
