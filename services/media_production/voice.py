"""Production voice service — ElevenLabs / OpenAI TTS / local clone seam.

Wraps ProviderRuntime (selection, fallback, cache, health) and adds:
persistence, timing metadata, SSML handling, and a stable voice_package shape.
"""

from __future__ import annotations

from typing import Any, Callable

from core.log import get_logger, log_event
from services.media_production.persistence import persist_audio_payload
from services.media_production.timestamps import attach_timing_metadata, has_ssml, strip_ssml
from services.provider_runtime.config import has_credential
from services.provider_runtime.engine_api import runtime_synthesize_voice
from services.provider_runtime.health import ProviderHealthMonitor
from services.provider_runtime.runtime import get_provider_runtime

logger = get_logger(__name__)


class VoiceProviderStatus:
    """Health / availability snapshot for the production dashboard."""

    @staticmethod
    def snapshot() -> list[dict[str, Any]]:
        rows = [
            {
                "provider": "elevenlabs",
                "label": "ElevenLabs",
                "configured": has_credential("ELEVENLABS_API_KEY"),
                "supports_ssml": True,
                "supports_timestamps": True,
            },
            {
                "provider": "openai_tts",
                "label": "OpenAI TTS",
                "configured": has_credential("OPENAI_API_KEY"),
                "supports_ssml": False,
                "supports_timestamps": False,
            },
            {
                "provider": "local_voice_clone",
                "label": "Local Voice Clone",
                "configured": False,
                "supports_ssml": False,
                "supports_timestamps": False,
                "status": "future",
            },
        ]
        try:
            runtime = get_provider_runtime()
            health = getattr(runtime, "health", None) or ProviderHealthMonitor()
            for row in rows:
                if row["provider"] == "local_voice_clone":
                    continue
                probe = health.probe(row["provider"]) if hasattr(health, "probe") else None
                if isinstance(probe, dict):
                    row["healthy"] = bool(probe.get("ok") or probe.get("healthy"))
                else:
                    row["healthy"] = row["configured"]
        except Exception:  # noqa: BLE001
            for row in rows:
                row.setdefault("healthy", row["configured"])
        return rows


def synthesize_voice(
    text: str,
    *,
    profile: dict | None = None,
    settings: dict | None = None,
    mode: str = "ai",
    preferred_provider: str = "",
    on_progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Synthesize narration with automatic provider fallback and disk persistence."""
    profile = dict(profile or {})
    settings = dict(settings or {})
    raw_text = text or ""
    if not raw_text.strip():
        return {
            "ok": False,
            "placeholder": True,
            "error": "empty text",
            "voice_package": {},
        }

    if on_progress:
        on_progress("Selecting voice provider")

    # OpenAI TTS rejects SSML; strip when routing may hit it. ElevenLabs can keep SSML.
    payload_text = raw_text
    if has_ssml(raw_text) and not has_credential("ELEVENLABS_API_KEY"):
        payload_text = strip_ssml(raw_text)

    if preferred_provider:
        settings = {**settings, "preferred_provider": preferred_provider}

    result = runtime_synthesize_voice(payload_text, profile, settings, mode=mode)
    if on_progress:
        on_progress(f"Provider={result.get('provider') or 'none'}")

    result = persist_audio_payload(result, name=str(profile.get("profile_id") or "voice"))
    duration = float(result.get("duration_sec") or 0)
    if duration <= 0:
        duration = round(max(1, len(strip_ssml(raw_text).split())) / 2.5, 2)
        result["duration_sec"] = duration

    provider_words = result.get("word_timestamps") or (result.get("metadata") or {}).get("word_timestamps")
    provider_sentences = result.get("sentence_timestamps") or (result.get("metadata") or {}).get(
        "sentence_timestamps"
    )
    timing = attach_timing_metadata(
        raw_text,
        duration,
        word_timestamps=provider_words if isinstance(provider_words, list) else None,
        sentence_timestamps=provider_sentences if isinstance(provider_sentences, list) else None,
    )

    voice_package = {
        "package_version": "1.0",
        "text": raw_text,
        "plain_text": strip_ssml(raw_text),
        "path": result.get("path") or "",
        "audio_b64": result.get("audio_b64") or "",
        "audio_url": result.get("audio_url") or "",
        "provider": result.get("provider") or "",
        "mode": mode,
        "placeholder": bool(result.get("placeholder", True)),
        "error": result.get("error") or "",
        "timing": timing,
        "duration_sec": duration,
        "format": result.get("format") or "mp3",
        "profile_id": profile.get("profile_id") or "",
        "ssml_supported": has_credential("ELEVENLABS_API_KEY"),
    }

    log_event(
        logger,
        "media_production.voice",
        provider=voice_package["provider"],
        placeholder=voice_package["placeholder"],
        duration=duration,
    )
    return {
        "ok": not voice_package["placeholder"],
        "placeholder": voice_package["placeholder"],
        "error": voice_package["error"],
        "provider": voice_package["provider"],
        "path": voice_package["path"],
        "duration_sec": duration,
        "audio_b64": voice_package["audio_b64"],
        "voice_package": voice_package,
        "metadata": {
            "provider": voice_package["provider"],
            "timing": timing,
            "demo_mode": voice_package["placeholder"],
        },
        "asset_id": result.get("asset_id") or f"voice_{abs(hash(raw_text)) % 10**10}",
        "mode": mode,
    }
