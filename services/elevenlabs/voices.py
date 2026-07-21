"""Narrator profiles → configurable ElevenLabs voice IDs (Voice Studio + env)."""

from __future__ import annotations

import os
from typing import Any, Callable

from services.elevenlabs.config import (
    DEFAULT_VOICE_ID,
    NARRATOR_PROFILE_ENV_KEYS,
    api_key,
    get_elevenlabs_config,
)

_studio_normalize: Callable[[str], str] | None = None
NARRATOR_PROFILES: dict[str, dict[str, Any]] = {}
_ALIASES: dict[str, str] = {"default": "founder", "founder": "founder"}


def _sync_voice_studio_catalog() -> None:
    """Lazy-load Voice Studio catalog (avoids empty profiles from import cycles)."""
    global _studio_normalize, NARRATOR_PROFILES, _ALIASES
    try:
        from services.voice_studio.profiles import (
            NARRATOR_PROFILE_CATALOG,
            PROFILE_ALIASES,
            normalize_profile_key,
        )
    except Exception:  # noqa: BLE001
        if not NARRATOR_PROFILES:
            NARRATOR_PROFILES = {
                "founder": {
                    "label": "Founder Voice",
                    "description": "Permanent default narrator",
                    "stability": 0.52,
                    "similarity_boost": 0.8,
                    "style_keys": ("default", "founder"),
                },
                "professor": {
                    "label": "Professor",
                    "description": "Authoritative educational delivery",
                    "stability": 0.55,
                    "similarity_boost": 0.8,
                    "style_keys": ("educational", "science", "professor"),
                },
            }
        return

    _studio_normalize = normalize_profile_key
    _ALIASES = dict(PROFILE_ALIASES or {})
    NARRATOR_PROFILES = {
        key: {
            "label": meta["label"],
            "description": meta["description"],
            "stability": meta["stability"],
            "similarity_boost": meta["similarity_boost"],
            "style_keys": meta.get("content_types") or (),
        }
        for key, meta in (NARRATOR_PROFILE_CATALOG or {}).items()
    }


_sync_voice_studio_catalog()


def normalize_narrator_key(value: str) -> str:
    _sync_voice_studio_catalog()
    if _studio_normalize:
        return _studio_normalize(value)
    raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    return _ALIASES.get(raw, raw if raw in NARRATOR_PROFILES else "founder")


def resolve_narrator_profile(
    narrator: str = "founder",
    *,
    style: str = "",
    explicit_voice_id: str = "",
) -> dict[str, Any]:
    """Map a studio narrator/style onto ElevenLabs voice settings (env/config IDs only).

    Permanent default is VOICE_ASSET_0001 (Founder Voice) unless a production
    passes ``explicit_voice_id`` or an intentional per-profile env override.
    Profile *keys* (professor, documentary, …) remain for delivery metadata;
    the voice ID still resolves to Founder Voice by default.
    """
    _sync_voice_studio_catalog()
    cfg = get_elevenlabs_config()
    raw_narrator = str(narrator or "").strip()
    key = normalize_narrator_key(raw_narrator or style or "founder")
    if key not in NARRATOR_PROFILES and style:
        key = normalize_narrator_key(style)
    # Unspecified / default → founder profile key
    if not raw_narrator or key == "default":
        key = "founder" if "founder" in NARRATOR_PROFILES else key
    meta = dict(
        NARRATOR_PROFILES.get(key)
        or NARRATOR_PROFILES.get("founder")
        or next(iter(NARRATOR_PROFILES.values()))
    )
    env_key = NARRATOR_PROFILE_ENV_KEYS.get(key, "")

    founder_voice = ""
    founder_settings: dict[str, Any] = {}
    try:
        from services.studio_assets.founder_voice import get_founder_voice_id, resolve_default_narrator

        founder_voice = get_founder_voice_id()
        founder_settings = resolve_default_narrator(key, explicit_voice_id=explicit_voice_id)
    except Exception:  # noqa: BLE001
        founder_voice = ""

    studio_voice = ""
    try:
        from services.voice_studio.config_store import get_configured_voice_id

        studio_voice = get_configured_voice_id(key)
    except Exception:  # noqa: BLE001
        studio_voice = ""

    # Priority: production explicit → intentional env override → Founder Voice → studio/cfg
    env_override = (os.environ.get(env_key) or "").strip() if env_key else ""
    # ELEVENLABS_VOICE_FOUNDER / DEFAULT are the permanent default, not an "override"
    intentional_env = env_override and env_key not in {
        "ELEVENLABS_VOICE_FOUNDER",
        "ELEVENLABS_DEFAULT_VOICE_ID",
    }
    voice_id = (
        (explicit_voice_id or "").strip()
        or (env_override if intentional_env else "")
        or founder_voice
        or studio_voice
        or cfg["default_voice_id"]
        or DEFAULT_VOICE_ID
    )
    use_founder_delivery = bool(
        founder_settings and not intentional_env and not (explicit_voice_id or "").strip()
    )
    stability = float(
        (founder_settings.get("stability") if use_founder_delivery else meta.get("stability")) or 0.5
    )
    similarity = float(
        (
            founder_settings.get("similarity_boost")
            if use_founder_delivery
            else meta.get("similarity_boost")
        )
        or 0.75
    )
    return {
        "profile_key": key,
        "label": meta.get("label") or "Founder Voice",
        "description": meta.get("description") or "",
        "provider": "elevenlabs",
        "provider_voice_id": voice_id,
        "voice_id": voice_id,
        "model_id": cfg["model_id"],
        "stability": stability,
        "similarity_boost": similarity,
        "studio_asset_id": "VOICE-0001" if voice_id == founder_voice else "",
        "permanent_default": bool(
            founder_voice and voice_id == founder_voice and not (explicit_voice_id or "").strip()
        ),
        "settings": {
            "preferred_provider": "elevenlabs",
            "stability": stability,
            "similarity_boost": similarity,
            "model": cfg["model_id"],
            "style": float((founder_settings or {}).get("style") or 0.35),
        },
    }


def list_elevenlabs_voices(*, limit: int = 50) -> dict[str, Any]:
    """List voices from ElevenLabs (SDK preferred, HTTP fallback). Never prints the API key."""
    if not api_key():
        return {"ok": False, "error": "ELEVENLABS_API_KEY missing", "voices": []}

    try:
        from elevenlabs.client import ElevenLabs

        client = ElevenLabs(api_key=api_key())
        raw = client.voices.get_all()
        voices = []
        for v in getattr(raw, "voices", None) or []:
            voices.append(
                {
                    "voice_id": getattr(v, "voice_id", "") or getattr(v, "voiceId", ""),
                    "name": getattr(v, "name", "") or "",
                    "category": getattr(v, "category", "") or "",
                }
            )
            if len(voices) >= limit:
                break
        return {"ok": True, "source": "sdk", "voices": voices, "count": len(voices)}
    except Exception as sdk_exc:  # noqa: BLE001
        sdk_error = str(sdk_exc)[:240]

    try:
        from services.provider_runtime.connectors.voice import ElevenLabsConnector

        conn = ElevenLabsConnector()
        resp = conn.http("GET", "/voices", timeout_sec=30.0, retries=1, headers={"Accept": "application/json"})
        if not resp.ok:
            return {
                "ok": False,
                "error": f"voices HTTP {resp.status}",
                "sdk_error": sdk_error,
                "voices": [],
            }
        body = resp.body if isinstance(resp.body, dict) else {}
        voices = []
        for v in body.get("voices") or []:
            if not isinstance(v, dict):
                continue
            voices.append(
                {
                    "voice_id": v.get("voice_id") or "",
                    "name": v.get("name") or "",
                    "category": v.get("category") or "",
                }
            )
            if len(voices) >= limit:
                break
        return {"ok": True, "source": "http", "voices": voices, "count": len(voices), "sdk_error": sdk_error}
    except Exception as http_exc:  # noqa: BLE001
        return {"ok": False, "error": str(http_exc)[:240], "sdk_error": sdk_error, "voices": []}
