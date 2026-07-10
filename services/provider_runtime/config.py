"""Credential and runtime configuration loading.

Loads API keys from (in priority order):
1. Explicit runtime overrides passed to ProviderRuntime
2. Environment variables
3. .env file (via python-dotenv when available)
4. Provider registry metadata (api_key_env fields)
5. Optional JSON config file (PROVIDER_CONFIG_PATH)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_dotenv_if_available() -> None:
    """Load .env from project root when python-dotenv is installed."""
    try:
        from dotenv import load_dotenv

        env_path = _PROJECT_ROOT / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    except ImportError:
        pass


def get_credential(env_var: str, overrides: "dict[str, str] | None" = None) -> str:
    """Resolve one credential from overrides, environment, then encrypted secrets."""
    if overrides and env_var in overrides:
        return overrides[env_var]
    value = os.environ.get(env_var, "")
    if value:
        return value
    # Encrypted SecretManager file (never hardcode; passphrase-gated).
    try:
        from services.provider_runtime.secrets import SecretManager

        return SecretManager().get(env_var) or ""
    except Exception:  # noqa: BLE001 — credential resolution must never crash callers
        return ""


def has_credential(env_var: str, overrides: "dict[str, str] | None" = None) -> bool:
    return bool(get_credential(env_var, overrides))


def load_runtime_config(path: "str | Path | None" = None) -> dict[str, Any]:
    """Load optional JSON runtime config (provider preferences, rate limits)."""
    config_path = path or os.environ.get("PROVIDER_CONFIG_PATH", "")
    if not config_path:
        default = _PROJECT_ROOT / "data" / "provider_runtime" / "config.json"
        if default.exists():
            config_path = str(default)
        else:
            return {}
    try:
        return json.loads(Path(config_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def provider_config_for(name: str, runtime_config: "dict | None" = None) -> dict:
    """Per-provider settings from runtime config."""
    cfg = runtime_config or load_runtime_config()
    providers = cfg.get("providers", {})
    return dict(providers.get(name, {}))


def save_runtime_config(data: dict[str, Any], path: "str | Path | None" = None) -> Path:
    """Persist runtime preferences (never write secrets into this file)."""
    config_path = Path(path) if path else Path(
        os.environ.get(
            "PROVIDER_CONFIG_PATH",
            str(_PROJECT_ROOT / "data" / "provider_runtime" / "config.json"),
        )
    )
    config_path.parent.mkdir(parents=True, exist_ok=True)
    # Strip accidental secret-looking keys
    safe = dict(data or {})
    for banned in ("api_key", "access_token", "client_secret", "refresh_token", "password"):
        safe.pop(banned, None)
    config_path.write_text(json.dumps(safe, indent=2, sort_keys=True), encoding="utf-8")
    return config_path
