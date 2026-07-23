"""OpenAI-backed provider. Falls back to demo content on any failure."""

from __future__ import annotations

import json
import os

import streamlit as st

from core.ai.base import AIProvider, GenerationRequest, GenerationResult
from core.ai.demo_provider import placeholder_ideas
from core.log import get_logger

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - openai should always be installed
    OpenAI = None

logger = get_logger(__name__)


def get_api_key() -> str:
    """Resolve OpenAI key: session override → env / .env / SecretManager."""
    try:
        session_key = (st.session_state.get("openai_api_key_override") or "").strip()
        if session_key:
            return session_key
    except Exception:  # noqa: BLE001 — session_state unavailable outside Streamlit
        pass
    try:
        from services.provider_runtime.config import get_credential

        return (get_credential("OPENAI_API_KEY") or "").strip()
    except Exception:  # noqa: BLE001
        return (os.getenv("OPENAI_API_KEY") or "").strip()


def _build_prompt(request: GenerationRequest) -> "tuple[str, str]":
    system_prompt = (
        "You are Generational, an expert short-form (faceless) content strategist. "
        "You always respond with valid, minified JSON only — no prose, no markdown fences."
    )
    user_prompt = (
        f'Original user command: "{request.command}"\n'
        f'Niche: "{request.niche}"\n'
        f'Subject: "{request.subject}"\n\n'
        f"Generate exactly {request.count} unique, viral-worthy short-form video content ideas. "
        "Respond with JSON matching exactly this shape:\n"
        "{\n"
        '  "ideas": [\n'
        "    {\n"
        '      "title": "catchy video title",\n'
        '      "hook": "first 1-2 sentence viral hook",\n'
        '      "script": "full 15-30 second voiceover script",\n'
        '      "cta": "short call to action",\n'
        '      "hashtags": ["#tag1", "#tag2", "#tag3"],\n'
        '      "thumbnail_concept": "one sentence describing a thumbnail concept"\n'
        "    }\n"
        "  ]\n"
        "}"
    )
    return system_prompt, user_prompt


class OpenAIProvider(AIProvider):
    name = "openai"

    def is_available(self) -> bool:
        return OpenAI is not None and bool(get_api_key())

    def generate_json(self, system_prompt: str, user_prompt: str, model: str) -> "tuple[dict | None, int]":
        if not self.is_available():
            return None, 0
        try:
            client = OpenAI(api_key=get_api_key())
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.8,
            )
            data = json.loads(response.choices[0].message.content)
            tokens = 0
            if getattr(response, "usage", None):
                tokens = getattr(response.usage, "total_tokens", 0) or 0
            return data, tokens
        except Exception as exc:  # noqa: BLE001 - engines fall back to heuristics
            logger.error("OpenAI JSON call failed (model=%s): %s", model, exc)
            return None, 0

    def generate_ideas(self, request: GenerationRequest) -> GenerationResult:
        try:
            client = OpenAI(api_key=get_api_key())
            system_prompt, user_prompt = _build_prompt(request)
            response = client.chat.completions.create(
                model=request.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.9,
            )
            data = json.loads(response.choices[0].message.content)
            ideas = data.get("ideas") or []
            if not ideas:
                raise ValueError("The model returned no ideas.")

            tokens_used = 0
            if getattr(response, "usage", None):
                tokens_used = getattr(response.usage, "total_tokens", 0) or 0

            logger.info(
                "Generated %d ideas via OpenAI (model=%s, tokens=%d)", len(ideas), request.model, tokens_used
            )
            return GenerationResult(ideas=ideas[: request.count], demo_mode=False, tokens_used=tokens_used)
        except Exception as exc:  # noqa: BLE001 - any failure must fall back gracefully
            logger.error("OpenAI generation failed, falling back to demo content: %s", exc)
            fallback = placeholder_ideas(request.niche, request.subject, request.count)
            return GenerationResult(ideas=fallback, demo_mode=True, error=str(exc))
