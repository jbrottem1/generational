"""Engine-facing helpers — the only AI gateway engines should use.

Engines call these helpers instead of `core.ai` or legacy provider factories.
All traffic still flows through ProviderRuntime (selection, fallback, cost).
"""

from __future__ import annotations

import json
from typing import Any

from services.provider_runtime.models import ProviderResponse
from services.provider_runtime.runtime import get_provider_runtime


def runtime_generate_json(
    system_prompt: str,
    user_prompt: str,
    *,
    model: str = "",
    operation: str = "generate_script",
    preferred_provider: str = "",
    optimize_for: str = "quality",
) -> "tuple[dict | None, int, str]":
    """LLM JSON generation via ProviderRuntime.

    Returns ``(data, tokens_used, provider_name)``. ``data`` is None on failure.
    """
    runtime = get_provider_runtime()
    payload = {
        "system_prompt": system_prompt,
        "prompt": user_prompt,
        "user_prompt": user_prompt,
        "json": True,
        "model": model or "",
    }
    kwargs: dict[str, Any] = {
        "optimize_for": optimize_for,
        "allow_fallback": True,
    }
    if preferred_provider:
        kwargs["preferred_provider"] = preferred_provider

    method = getattr(runtime, operation, None)
    if callable(method) and operation.startswith("generate_"):
        response = method(payload, **kwargs)
    else:
        from services.provider_runtime.models import ProviderRequest

        response = runtime.execute(
            ProviderRequest(operation=operation or "generate_script", payload=payload, **kwargs)
        )
    return _parse_json_response(response)


def _parse_json_response(response: ProviderResponse) -> "tuple[dict | None, int, str]":
    if not response.success:
        return None, 0, response.provider or ""
    data = response.data or {}
    # Prefer structured JSON already in data; else parse text/content.
    if any(k in data for k in ("candidates", "scripts", "items", "ideas")):
        return data, int(response.tokens_used or 0), response.provider
    text = str(data.get("text") or data.get("content") or data.get("script") or "")
    if text:
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed, int(response.tokens_used or 0), response.provider
        except json.JSONDecodeError:
            # Strip markdown fences if present
            stripped = text.strip()
            if stripped.startswith("```"):
                stripped = stripped.strip("`")
                if stripped.startswith("json"):
                    stripped = stripped[4:]
                try:
                    parsed = json.loads(stripped.strip())
                    if isinstance(parsed, dict):
                        return parsed, int(response.tokens_used or 0), response.provider
                except json.JSONDecodeError:
                    pass
    # Raw dict payload without known keys — return as-is when non-empty
    if data and not data.get("placeholder"):
        return data, int(response.tokens_used or 0), response.provider
    return None, int(response.tokens_used or 0), response.provider


def runtime_generate_image(prompt: str, metadata: "dict | None" = None) -> dict:
    """Image generation via ProviderRuntime — returns legacy-compatible asset dict."""
    meta = metadata or {}
    runtime = get_provider_runtime()
    response = runtime.generate_image(
        {
            "prompt": prompt,
            "width": meta.get("width", 1080),
            "height": meta.get("height", 1920),
            **{k: v for k, v in meta.items() if k not in ("width", "height")},
        },
        allow_fallback=True,
    )
    data = dict(response.data or {})
    return {
        "path": data.get("image_url") or data.get("uri") or data.get("path") or f"runtime://image/{response.provider}",
        "uri": data.get("image_url") or data.get("uri") or "",
        "image_url": data.get("image_url") or "",
        "b64_json": data.get("b64_json") or "",
        "provider": response.provider,
        "placeholder": bool(response.demo_mode or data.get("placeholder")),
        "status": "generated" if response.success and not response.demo_mode else "mock",
        "prompt": prompt,
        "width": meta.get("width", 1080),
        "height": meta.get("height", 1920),
        "error": response.error,
    }


def runtime_generate_video(prompt: str, duration_sec: float = 0, metadata: "dict | None" = None) -> dict:
    """Video generation via ProviderRuntime — returns legacy-compatible asset dict."""
    meta = metadata or {}
    runtime = get_provider_runtime()
    response = runtime.generate_video(
        {
            "prompt": prompt,
            "duration_sec": duration_sec,
            "width": meta.get("width", 1080),
            "height": meta.get("height", 1920),
        },
        allow_fallback=True,
    )
    data = dict(response.data or {})
    return {
        "path": data.get("video_url") or data.get("uri") or data.get("path") or f"runtime://video/{response.provider}",
        "uri": data.get("video_url") or data.get("uri") or "",
        "video_url": data.get("video_url") or "",
        "job_id": data.get("job_id") or "",
        "provider": response.provider,
        "placeholder": bool(response.demo_mode or data.get("placeholder") or data.get("async")),
        "status": data.get("status") or ("generated" if response.success and not response.demo_mode else "mock"),
        "prompt": prompt,
        "duration_sec": duration_sec,
        "width": meta.get("width", 1080),
        "height": meta.get("height", 1920),
        "error": response.error,
        "async": bool(data.get("async")),
    }


def runtime_synthesize_voice(text: str, profile: dict, settings: dict, mode: str = "ai") -> dict:
    """Voice synthesis via ProviderRuntime — returns narration-compatible dict."""
    runtime = get_provider_runtime()
    response = runtime.generate_voice(
        {
            "text": text,
            "profile": profile,
            "settings": settings,
            "mode": mode,
            "voice_id": profile.get("provider_voice_id") or profile.get("voice_id") or "",
            "voice": settings.get("voice") or profile.get("voice") or "alloy",
        },
        allow_fallback=True,
    )
    data = dict(response.data or {})
    words = max(1, len(text.split()))
    duration = float(data.get("duration_sec") or round(words / 2.5, 2))
    return {
        "asset_id": data.get("asset_id") or f"voice_{response.provider}_{abs(hash(text)) % 10**10}",
        "duration_sec": duration,
        "path": data.get("audio_url") or data.get("path") or "",
        "audio_b64": data.get("audio_b64") or "",
        "mode": mode,
        "placeholder": bool(response.demo_mode or not (data.get("audio_b64") or data.get("audio_url"))),
        "provider": response.provider,
        "error": response.error,
        "metadata": {"provider": response.provider, "demo_mode": response.demo_mode},
    }


def runtime_generate_asset(operation: str, payload: dict) -> ProviderResponse:
    """Generic asset generation routed by operation name."""
    runtime = get_provider_runtime()
    method = getattr(runtime, operation, None)
    if callable(method):
        return method(payload, allow_fallback=True)
    from services.provider_runtime.models import ProviderRequest

    return runtime.execute(ProviderRequest(operation=operation, payload=payload, allow_fallback=True))
