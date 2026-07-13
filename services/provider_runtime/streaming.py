"""Streaming helpers for ProviderRuntime LLM connectors."""

from __future__ import annotations

import json
from typing import Callable, Iterator

from services.provider_runtime.http_client import HttpRequest, get_default_transport
from services.provider_runtime.models import ProviderRequest, ProviderResponse


def stream_chat_completions(
    url: str,
    *,
    headers: dict,
    body: dict,
    timeout_sec: float = 120.0,
    on_token: "Callable[[str], None] | None" = None,
) -> "tuple[str, dict]":
    """Consume an OpenAI-compatible SSE chat stream; return (full_text, usage).

    When the transport returns a non-streaming JSON body, falls back to a
    single-shot parse so connectors work under mock transports in tests.
    """
    transport = get_default_transport()
    req = HttpRequest(
        method="POST",
        url=url,
        headers={**headers, "Accept": "text/event-stream"},
        json_body={**body, "stream": True},
        timeout_sec=timeout_sec,
    )
    resp = transport(req)
    if not resp.ok and resp.status != 0:
        raise RuntimeError(f"stream failed: {resp.status} {resp.body}")

    # Mock / non-SSE JSON response
    if isinstance(resp.body, dict) and "choices" in resp.body:
        choice = (resp.body.get("choices") or [{}])[0]
        text = str(((choice.get("message") or {}).get("content")) or choice.get("text") or "")
        if on_token and text:
            on_token(text)
        return text, dict(resp.body.get("usage") or {})

    raw = resp.raw or (resp.body if isinstance(resp.body, (bytes, bytearray)) else b"")
    if isinstance(resp.body, str):
        raw = resp.body.encode("utf-8")
    text_parts: list[str] = []
    usage: dict = {}
    for line in raw.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            break
        try:
            chunk = json.loads(payload)
        except json.JSONDecodeError:
            continue
        delta = ((chunk.get("choices") or [{}])[0].get("delta") or {})
        token = str(delta.get("content") or "")
        if token:
            text_parts.append(token)
            if on_token:
                on_token(token)
        if chunk.get("usage"):
            usage = dict(chunk["usage"])
    return "".join(text_parts), usage


def streaming_response(
    request: ProviderRequest,
    provider_name: str,
    text: str,
    *,
    tokens_used: int = 0,
    model: str = "",
) -> ProviderResponse:
    return ProviderResponse(
        success=True,
        operation=request.operation,
        provider=provider_name,
        data={"text": text, "content": text, "script": text, "streamed": True, "model": model},
        tokens_used=tokens_used,
        metadata={"streamed": True, "model": model},
    )


def iter_tokens(text: str, chunk_size: int = 12) -> Iterator[str]:
    """Utility for demo/mock streaming of a completed string."""
    for i in range(0, len(text), chunk_size):
        yield text[i : i + chunk_size]
