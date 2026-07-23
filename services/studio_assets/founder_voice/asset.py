"""Permanent Founder Voice asset — cloned ElevenLabs voice as universe default."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.studio_assets.registry import upsert_asset

ROOT = Path(__file__).resolve().parents[3]
ASSET_ID = "VOICE-0001"
ASSET_SLUG = "VOICE-0001-FOUNDER-VOICE"
ASSET_VERSION = "1.0.0"
DISPLAY_NAME = "Founder Voice"
# Cloned ElevenLabs voice "Jared" — permanent company IP reference (not an API key).
FOUNDATION_VOICE_ID = "3tjayB0V8cEeXFHiD3SP"
ASSET_ROOT = ROOT / "data" / "studio_assets" / ASSET_SLUG


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def get_founder_voice_id() -> str:
    """Resolve permanent Founder Voice ID (asset file → constant)."""
    profile_path = ASSET_ROOT / "VOICE_PROFILE.json"
    if profile_path.is_file():
        try:
            data = json.loads(profile_path.read_text(encoding="utf-8"))
            vid = str(data.get("voice_id") or "").strip()
            if vid:
                return vid
        except (OSError, json.JSONDecodeError):
            pass
    return FOUNDATION_VOICE_ID


def get_founder_voice_profile() -> dict[str, Any]:
    return {
        "asset_number": "0001",
        "id": ASSET_ID,
        "slug": ASSET_SLUG,
        "name": DISPLAY_NAME,
        "provider": "elevenlabs",
        "status": "permanent",
        "default": True,
        "version": ASSET_VERSION,
        "voice_id": get_founder_voice_id(),
        "clone_name": "Jared",
        "category": "cloned",
        "delivery": {
            "pacing": "natural",
            "tone": "professional",
            "warmth": "warm",
            "confidence": "confident",
            "cadence": "conversational",
            "pronunciation": "consistent",
            "emotion": "expressive_educational",
            "style": "educational_storytelling",
        },
        "memory": {
            "voice_id": get_founder_voice_id(),
            "provider": "elevenlabs",
            "preferred_model": "eleven_multilingual_v2",
            "preferred_stability": 0.52,
            "preferred_similarity": 0.8,
            "preferred_style": 0.35,
            "preferred_speaking_rate": 1.0,
            "preferred_output_format": "mp3_44100_128",
            "preferred_sample_rate": 44100,
            "preferred_language": "en",
            "preferred_normalization": "on",
        },
        "failover": {
            "pause_if_unavailable": True,
            "attempt_reconnect": True,
            "retry": True,
            "allow_silent_fallback": False,
            "fallback_only_if_user_allows_or_test_mode": True,
        },
        "continuity": {
            "rule": "Always reference this Studio Asset. Never silently replace Founder Voice.",
            "override": "Only when a production explicitly requests another voice_id / narrator override.",
        },
    }


def get_founder_default_config() -> dict[str, Any]:
    mem = get_founder_voice_profile()["memory"]
    return {
        "default_voice_asset_id": ASSET_ID,
        "default": True,
        "provider": "elevenlabs",
        "voice_id": mem["voice_id"],
        "model_id": mem["preferred_model"],
        "stability": mem["preferred_stability"],
        "similarity_boost": mem["preferred_similarity"],
        "style": mem["preferred_style"],
        "speaking_rate": mem["preferred_speaking_rate"],
        "output_format": mem["preferred_output_format"],
        "sample_rate": mem["preferred_sample_rate"],
        "language": mem["preferred_language"],
        "normalization": mem["preferred_normalization"],
        "reject_fallback_when_elevenlabs_available": True,
        "assign_when_narrator_unspecified": True,
        "env_keys": {
            "default_voice": "ELEVENLABS_DEFAULT_VOICE_ID",
            "founder_voice": "ELEVENLABS_VOICE_FOUNDER",
            "allow_fallback": "ELEVENLABS_ALLOW_FALLBACK",
        },
        "recommended_env": {
            "ELEVENLABS_ALLOW_FALLBACK": "0",
        },
    }


def resolve_default_narrator(
    narrator: str = "",
    *,
    explicit_voice_id: str = "",
    allow_profile_env_override: bool = True,
) -> dict[str, Any]:
    """Return Founder Voice resolution when narrator/voice unspecified."""
    import os

    profile = get_founder_voice_profile()
    mem = profile["memory"]
    env_founder = (os.environ.get("ELEVENLABS_VOICE_FOUNDER") or "").strip()
    voice_id = (explicit_voice_id or "").strip() or env_founder or mem["voice_id"]
    return {
        "profile_key": "founder",
        "label": DISPLAY_NAME,
        "description": "Permanent default narrator — Founder Voice (cloned ElevenLabs)",
        "provider": "elevenlabs",
        "provider_voice_id": voice_id,
        "voice_id": voice_id,
        "model_id": mem["preferred_model"],
        "stability": float(mem["preferred_stability"]),
        "similarity_boost": float(mem["preferred_similarity"]),
        "style": float(mem["preferred_style"]),
        "studio_asset_id": ASSET_ID,
        "permanent_default": True,
        "settings": {
            "preferred_provider": "elevenlabs",
            "stability": float(mem["preferred_stability"]),
            "similarity_boost": float(mem["preferred_similarity"]),
            "style": float(mem["preferred_style"]),
            "model": mem["preferred_model"],
            "speaking_rate": mem["preferred_speaking_rate"],
        },
    }


def ensure_founder_voice_asset(*, sync_voice_studio: bool = True, sync_env: bool = True) -> dict[str, Any]:
    """Write permanent voice asset files and soft-wire Voice Studio / .env defaults."""
    ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    profile = get_founder_voice_profile()
    default_cfg = get_founder_default_config()
    asset_doc = {
        "package_type": "GENERATIONAL_STUDIO_VOICE_ASSET",
        "asset_number": "0001",
        "id": ASSET_ID,
        "slug": ASSET_SLUG,
        "name": DISPLAY_NAME,
        "provider": "elevenlabs",
        "status": "permanent",
        "default": True,
        "version": ASSET_VERSION,
        "voice_id": profile["voice_id"],
        "clone_name": profile["clone_name"],
        "generated_at": _now(),
        "path": str(ASSET_ROOT),
        "philosophy": {
            "no_new_voice_engine": True,
            "no_pipeline_redesign": True,
            "uses_existing_elevenlabs_integration": True,
            "never_silently_replace_founder_voice": True,
        },
    }

    _write_json(ASSET_ROOT / "VOICE_PROFILE.json", profile)
    _write_json(ASSET_ROOT / "VOICE_ASSET.json", asset_doc)
    _write_json(ASSET_ROOT / "VOICE_DEFAULT_CONFIG.json", default_cfg)
    _write_json(
        ASSET_ROOT / "VERSION.json",
        {
            "id": ASSET_ID,
            "version": ASSET_VERSION,
            "status": "permanent",
            "updated_at": _now(),
            "changelog": [
                {
                    "version": "1.0.0",
                    "note": "Initial permanent Founder Voice — cloned ElevenLabs narrator as universe default.",
                }
            ],
        },
    )

    if sync_voice_studio:
        from services.voice_studio.config_store import load_profile_voice_config, save_profile_voice_config

        data = load_profile_voice_config()
        vid = profile["voice_id"]
        data["default_voice_id"] = vid
        data["default_voice_asset_id"] = ASSET_ID
        profiles = dict(data.get("profiles") or {})
        profiles["founder"] = {
            "voice_id": vid,
            "label": DISPLAY_NAME,
            "studio_asset_id": ASSET_ID,
            "default": True,
        }
        # Soft-map all studio profiles to Founder Voice (production may still override via
        # explicit_voice_id or intentional ELEVENLABS_VOICE_* env keys).
        for key in list(profiles.keys()) or []:
            row = dict(profiles.get(key) or {})
            row["voice_id"] = vid
            row["studio_asset_id"] = ASSET_ID
            row.setdefault("label", key.replace("_", " ").title())
            profiles[key] = row
        for key in (
            "professor",
            "documentary",
            "storyteller",
            "science_educator",
            "technology_explainer",
            "history_narrator",
            "calm_instructor",
            "energetic_presenter",
            "energetic_explainer",
            "calm_educator",
            "default",
            "doctor",
        ):
            row = dict(profiles.get(key) or {})
            row["voice_id"] = vid
            row["studio_asset_id"] = ASSET_ID
            row.setdefault("label", "Founder Voice" if key in {"founder", "default"} else key.replace("_", " ").title())
            profiles[key] = row
        data["profiles"] = profiles
        save_profile_voice_config(data)

    if sync_env:
        try:
            from core.env import write_env_value

            write_env_value("ELEVENLABS_DEFAULT_VOICE_ID", profile["voice_id"])
            write_env_value("ELEVENLABS_VOICE_FOUNDER", profile["voice_id"])
            # Prefer no silent fallback for Founder Voice productions
            write_env_value("ELEVENLABS_ALLOW_FALLBACK", "0")
        except Exception:  # noqa: BLE001
            pass

    upsert_asset(
        {
            "id": ASSET_ID,
            "asset_number": "0001",
            "name": DISPLAY_NAME,
            "slug": ASSET_SLUG,
            "version": ASSET_VERSION,
            "status": "permanent",
            "role": "default_narrator",
            "provider": "elevenlabs",
            "path": f"data/studio_assets/{ASSET_SLUG}/",
            "default": True,
            "flagship_default_voice": True,
            "manifest": "VOICE_ASSET.json",
        }
    )
    reg_path = ROOT / "data" / "studio_assets" / "REGISTRY.json"
    if reg_path.is_file():
        try:
            reg = json.loads(reg_path.read_text(encoding="utf-8"))
            reg["flagship_default_voice"] = ASSET_ID
            reg_path.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")
        except (OSError, json.JSONDecodeError):
            pass

    return asset_doc
