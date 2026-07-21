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
    narrator: str = "",
    on_progress: Callable[[str], None] | None = None,
    allow_fallback: bool | None = None,
) -> dict[str, Any]:
    """Synthesize narration with ElevenLabs preferred when configured."""
    from services.elevenlabs.config import get_elevenlabs_config
    from services.elevenlabs.validation import validate_narration_audio
    from services.elevenlabs.voices import resolve_narrator_profile

    profile = dict(profile or {})
    settings = dict(settings or {})
    cfg = get_elevenlabs_config()
    if allow_fallback is None:
        # Founder Voice productions never silently fallback when ElevenLabs is configured
        allow_fallback = bool(cfg.get("allow_fallback"))
        if has_credential("ELEVENLABS_API_KEY") and not allow_fallback:
            allow_fallback = False

    raw_text = text or ""
    if not raw_text.strip():
        return {
            "ok": False,
            "placeholder": True,
            "error": "empty text",
            "voice_package": {},
            "provider": "",
        }

    if on_progress:
        on_progress("Selecting voice provider")

    # Official production provider: ElevenLabs when key is present.
    if not preferred_provider and has_credential("ELEVENLABS_API_KEY"):
        preferred_provider = "elevenlabs"
    # Default narrator unspecified → Founder Voice (VOICE_ASSET_0001)
    if not narrator and not profile.get("narrator") and not profile.get("narrator_profile"):
        narrator = "founder"
        profile.setdefault("narrator_profile", "founder")

    # Map studio narrator → configurable ElevenLabs voice ID
    if preferred_provider == "elevenlabs" or has_credential("ELEVENLABS_API_KEY"):
        narrator_key = (
            narrator
            or profile.get("narrator")
            or profile.get("style")
            or settings.get("narrator")
            or "professor"
        )
        resolved = resolve_narrator_profile(
            str(narrator_key),
            style=str(profile.get("style") or ""),
            explicit_voice_id=str(profile.get("provider_voice_id") or profile.get("voice_id") or ""),
        )
        profile = {
            **profile,
            "provider_voice_id": resolved["provider_voice_id"],
            "voice_id": resolved["voice_id"],
            "narrator_profile": resolved["profile_key"],
            "narrator_label": resolved["label"],
        }
        settings = {
            **settings,
            **resolved["settings"],
            "stability": resolved["stability"],
            "similarity_boost": resolved["similarity_boost"],
            "model": resolved["model_id"],
            "preferred_provider": preferred_provider or "elevenlabs",
        }

    # OpenAI TTS rejects SSML; strip when routing may hit it. ElevenLabs can keep SSML.
    payload_text = raw_text
    if has_ssml(raw_text) and preferred_provider != "elevenlabs" and not has_credential("ELEVENLABS_API_KEY"):
        payload_text = strip_ssml(raw_text)

    if preferred_provider:
        settings = {**settings, "preferred_provider": preferred_provider}

    # Disable local tone/`say` fallback when ElevenLabs is required and fallbacks off
    result = runtime_synthesize_voice(payload_text, profile, settings, mode=mode)
    if on_progress:
        on_progress(f"Provider={result.get('provider') or 'none'}")

    # If ElevenLabs failed and fallbacks disabled, pause — never silently replace Founder Voice
    provider_name = str(result.get("provider") or "")
    test_mode = str(mode or "").lower() in {"test", "smoke", "demo_allowed"}
    if (
        preferred_provider == "elevenlabs"
        and has_credential("ELEVENLABS_API_KEY")
        and not allow_fallback
        and not test_mode
        and provider_name not in ("elevenlabs",)
    ):
        return {
            "ok": False,
            "placeholder": True,
            "paused": True,
            "error": result.get("error")
            or "ElevenLabs unavailable — Founder Voice failover paused (set ELEVENLABS_ALLOW_FALLBACK=1 to override)",
            "provider": provider_name or "none",
            "voice_package": {
                "provider": provider_name or "none",
                "placeholder": True,
                "paused": True,
                "studio_asset_id": "VOICE-0001",
                "error": result.get("error") or "elevenlabs_failed_no_silent_fallback",
            },
        }

    result = persist_audio_payload(result, name=str(profile.get("profile_id") or profile.get("narrator_profile") or "voice"))
    # If local fallback filled a path after empty provider payload, re-tag clearly
    if result.get("local_fallback") and provider_name and provider_name != "elevenlabs":
        result["provider"] = provider_name
        result["fallback_from"] = preferred_provider or "elevenlabs"

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

    qa = validate_narration_audio(result.get("path") or "", timing=timing)
    if not qa.get("ok"):
        # Mark unusable audio — do not claim production narration succeeded
        placeholder = True
        error = "narration_qa_failed:" + ",".join(qa.get("hard_fails") or ["unknown"])
    else:
        placeholder = bool(result.get("placeholder", True)) and not bool(result.get("path"))
        # Real bytes on disk + QA pass ⇒ not a placeholder
        if qa.get("ok") and result.get("path"):
            placeholder = False
        error = result.get("error") or ""

    final_provider = str(result.get("provider") or preferred_provider or "")
    voice_package = {
        "package_version": "1.0",
        "text": raw_text,
        "plain_text": strip_ssml(raw_text),
        "path": result.get("path") or "",
        "audio_b64": result.get("audio_b64") or "",
        "audio_url": result.get("audio_url") or "",
        "provider": final_provider,
        "official_narration_provider": "elevenlabs" if final_provider == "elevenlabs" else final_provider,
        "mode": mode,
        "placeholder": placeholder,
        "error": error,
        "timing": timing,
        "duration_sec": float(qa.get("duration_sec") or duration),
        "format": result.get("format") or "mp3",
        "profile_id": profile.get("profile_id") or "",
        "narrator_profile": profile.get("narrator_profile") or "",
        "voice_id": profile.get("provider_voice_id") or profile.get("voice_id") or "",
        "model_id": settings.get("model") or cfg.get("model_id") or "",
        "ssml_supported": has_credential("ELEVENLABS_API_KEY"),
        "audio_qa": qa,
        "transport": (result.get("metadata") or {}).get("transport") or result.get("transport") or "",
        "fallback_from": result.get("fallback_from") or "",
    }

    log_event(
        logger,
        "media_production.voice",
        provider=voice_package["provider"],
        placeholder=voice_package["placeholder"],
        duration=voice_package["duration_sec"],
        qa_ok=bool(qa.get("ok")),
    )
    return {
        "ok": bool(qa.get("ok")) and not voice_package["placeholder"],
        "placeholder": voice_package["placeholder"],
        "error": voice_package["error"],
        "provider": voice_package["provider"],
        "path": voice_package["path"],
        "duration_sec": voice_package["duration_sec"],
        "audio_b64": voice_package["audio_b64"],
        "voice_package": voice_package,
        "audio_qa": qa,
        "metadata": {
            "provider": voice_package["provider"],
            "timing": timing,
            "demo_mode": voice_package["placeholder"],
            "audio_qa": qa,
            "narrator_profile": voice_package["narrator_profile"],
            "voice_id": voice_package["voice_id"],
        },
        "asset_id": result.get("asset_id") or f"voice_{abs(hash(raw_text)) % 10**10}",
        "mode": mode,
    }
