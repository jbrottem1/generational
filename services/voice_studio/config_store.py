"""Voice Studio configuration store — profile voice IDs in JSON/env only."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from services.voice_studio.profiles import NARRATOR_PROFILE_CATALOG, normalize_profile_key

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "data" / "voice_studio" / "PROFILE_VOICES.json"


def config_path() -> Path:
    return CONFIG_PATH


def load_profile_voice_config() -> dict[str, Any]:
    path = CONFIG_PATH
    if not path.exists():
        return {"version": "1.0", "default_voice_id": "", "profiles": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"profiles": {}}
    except (OSError, json.JSONDecodeError):
        return {"version": "1.0", "default_voice_id": "", "profiles": {}}


def save_profile_voice_config(data: dict[str, Any]) -> Path:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return CONFIG_PATH


def get_configured_voice_id(profile_key: str) -> str:
    """Resolve voice ID: env → PROFILE_VOICES.json → empty (caller may use global default)."""
    key = normalize_profile_key(profile_key)
    meta = NARRATOR_PROFILE_CATALOG.get(key) or {}
    env_key = str(meta.get("env_key") or "")
    if env_key:
        from_env = (os.environ.get(env_key) or "").strip()
        if from_env:
            return from_env
    cfg = load_profile_voice_config()
    profiles = cfg.get("profiles") or {}
    row = profiles.get(key) if isinstance(profiles, dict) else None
    if isinstance(row, dict):
        return str(row.get("voice_id") or "").strip()
    return ""


def get_studio_default_voice_id() -> str:
    env_default = (os.environ.get("ELEVENLABS_DEFAULT_VOICE_ID") or "").strip()
    if env_default:
        return env_default
    env_founder = (os.environ.get("ELEVENLABS_VOICE_FOUNDER") or "").strip()
    if env_founder:
        return env_founder
    try:
        from services.studio_assets.founder_voice import get_founder_voice_id

        founder = get_founder_voice_id()
        if founder:
            return founder
    except Exception:  # noqa: BLE001
        pass
    cfg = load_profile_voice_config()
    return str(cfg.get("default_voice_id") or "").strip()


def set_profile_voice_id(profile_key: str, voice_id: str, *, also_default: bool = False) -> dict[str, Any]:
    """Write a profile→voice mapping into PROFILE_VOICES.json (configuration only)."""
    key = normalize_profile_key(profile_key)
    data = load_profile_voice_config()
    profiles = dict(data.get("profiles") or {})
    label = (NARRATOR_PROFILE_CATALOG.get(key) or {}).get("label") or key
    profiles[key] = {
        **(profiles.get(key) if isinstance(profiles.get(key), dict) else {}),
        "voice_id": str(voice_id or "").strip(),
        "label": label,
    }
    data["profiles"] = profiles
    if also_default and voice_id:
        data["default_voice_id"] = str(voice_id).strip()
    save_profile_voice_config(data)
    return {"ok": True, "profile_key": key, "voice_id": str(voice_id).strip(), "path": str(CONFIG_PATH)}


def set_default_voice_id(voice_id: str) -> dict[str, Any]:
    data = load_profile_voice_config()
    data["default_voice_id"] = str(voice_id or "").strip()
    save_profile_voice_config(data)
    return {
        "ok": True,
        "default_voice_id": data["default_voice_id"],
        "path": str(CONFIG_PATH),
        "note": "Also set ELEVENLABS_DEFAULT_VOICE_ID in .env to override at runtime",
    }
