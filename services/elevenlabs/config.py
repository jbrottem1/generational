"""Secure ElevenLabs configuration — env only, never hardcoded secrets."""

from __future__ import annotations

import os
from typing import Any

from services.provider_runtime.config import get_credential, has_credential

DEFAULT_MODEL_ID = "eleven_multilingual_v2"
DEFAULT_OUTPUT_FORMAT = "mp3_44100_128"
DEFAULT_REQUEST_TIMEOUT = 90.0
DEFAULT_MAX_RETRIES = 2
# Fallback only when no env / Voice Studio default is configured (public catalog ID).
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

# Narrator profile → optional env override for voice IDs (config, not code)
NARRATOR_PROFILE_ENV_KEYS = {
    "founder": "ELEVENLABS_VOICE_FOUNDER",
    "professor": "ELEVENLABS_VOICE_PROFESSOR",
    "documentary": "ELEVENLABS_VOICE_DOCUMENTARY",
    "storyteller": "ELEVENLABS_VOICE_STORYTELLER",
    "science_educator": "ELEVENLABS_VOICE_SCIENCE",
    "technology_explainer": "ELEVENLABS_VOICE_TECH",
    "history_narrator": "ELEVENLABS_VOICE_HISTORY",
    "calm_instructor": "ELEVENLABS_VOICE_CALM",
    "energetic_presenter": "ELEVENLABS_VOICE_ENERGETIC",
    # Legacy aliases kept for existing .env lines
    "energetic_explainer": "ELEVENLABS_VOICE_ENERGETIC",
    "calm_educator": "ELEVENLABS_VOICE_CALM",
    "doctor": "ELEVENLABS_VOICE_FOUNDER",
    "default": "ELEVENLABS_VOICE_FOUNDER",
}


def get_elevenlabs_config() -> dict[str, Any]:
    """Return non-secret configuration for ElevenLabs production TTS."""
    model = (os.environ.get("ELEVENLABS_MODEL_ID") or "").strip() or DEFAULT_MODEL_ID
    voice = (os.environ.get("ELEVENLABS_DEFAULT_VOICE_ID") or "").strip()
    if not voice:
        try:
            from services.voice_studio.config_store import get_studio_default_voice_id

            voice = get_studio_default_voice_id()
        except Exception:  # noqa: BLE001
            voice = ""
    if not voice:
        voice = DEFAULT_VOICE_ID
    allow_fallback = str(os.environ.get("ELEVENLABS_ALLOW_FALLBACK") or "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }
    try:
        timeout = float(os.environ.get("ELEVENLABS_REQUEST_TIMEOUT") or DEFAULT_REQUEST_TIMEOUT)
    except ValueError:
        timeout = DEFAULT_REQUEST_TIMEOUT
    try:
        retries = int(os.environ.get("ELEVENLABS_MAX_RETRIES") or DEFAULT_MAX_RETRIES)
    except ValueError:
        retries = DEFAULT_MAX_RETRIES
    output_format = (os.environ.get("ELEVENLABS_OUTPUT_FORMAT") or "").strip() or DEFAULT_OUTPUT_FORMAT
    return {
        "api_key_configured": has_credential("ELEVENLABS_API_KEY"),
        "api_key_env": "ELEVENLABS_API_KEY",
        "default_voice_id": voice,
        "default_voice_from_env": bool((os.environ.get("ELEVENLABS_DEFAULT_VOICE_ID") or "").strip()),
        "model_id": model,
        "output_format": output_format,
        "request_timeout_sec": timeout,
        "max_retries": max(0, retries),
        "allow_fallback": allow_fallback,
        "sdk_preferred": str(os.environ.get("ELEVENLABS_USE_SDK") or "1").strip().lower()
        not in {"0", "false", "no", "off"},
        "official_provider": "elevenlabs",
    }


def api_key_present() -> bool:
    return has_credential("ELEVENLABS_API_KEY")


def api_key() -> str:
    """Return key for connectors only — never log this value."""
    return (get_credential("ELEVENLABS_API_KEY") or "").strip()
