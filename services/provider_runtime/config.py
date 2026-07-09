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
    """Resolve one credential from overrides, then environment."""
    if overrides and env_var in overrides:
        return overrides[env_var]
    return os.environ.get(env_var, "")


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
