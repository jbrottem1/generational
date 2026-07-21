"""Application environment bootstrap — .env loading and credential status.

Single source of truth for where Generational reads API keys:
1. Explicit overrides (SecretManager / runtime)
2. Process environment variables
3. Project-root `.env` (via python-dotenv)
4. Encrypted secrets file (when PROVIDER_SECRETS_PASSPHRASE is set)

Never hardcode secrets. Never log secret values.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_ENV_PATH = _PROJECT_ROOT / ".env"
_ENV_EXAMPLE_PATH = _PROJECT_ROOT / ".env.example"

# Keys operators most often need for leaving Demo Mode / enabling providers.
CORE_ENV_KEYS = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
    "XAI_API_KEY",
    "ELEVENLABS_API_KEY",
    "ELEVENLABS_DEFAULT_VOICE_ID",
    "ELEVENLABS_MODEL_ID",
    "RUNWAY_API_KEY",
    "BFL_API_KEY",
    "YOUTUBE_API_KEY",
)

_DOTENV_LOADED = False


def project_root() -> Path:
    return _PROJECT_ROOT


def env_file_path() -> Path:
    return _ENV_PATH


def env_example_path() -> Path:
    return _ENV_EXAMPLE_PATH


def ensure_env_file() -> dict[str, Any]:
    """Create `.env` from `.env.example` when missing (empty values only)."""
    if _ENV_PATH.exists():
        return {"created": False, "path": str(_ENV_PATH), "existed": True}
    if _ENV_EXAMPLE_PATH.exists():
        _ENV_PATH.write_text(_ENV_EXAMPLE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        return {"created": True, "path": str(_ENV_PATH), "from_example": True}
    # Minimal fallback if example is absent
    lines = [
        "# Generational local credentials — never commit this file.",
        "",
    ]
    for key in CORE_ENV_KEYS:
        lines.append(f"{key}=")
    lines.append("")
    _ENV_PATH.write_text("\n".join(lines), encoding="utf-8")
    return {"created": True, "path": str(_ENV_PATH), "from_example": False}


def load_application_env(*, create_if_missing: bool = True) -> dict[str, Any]:
    """Load project-root `.env` into os.environ. Idempotent and safe to call often."""
    global _DOTENV_LOADED
    created = {"created": False, "path": str(_ENV_PATH)}
    if create_if_missing and not _ENV_PATH.exists():
        created = ensure_env_file()

    loaded = False
    path_used = str(_ENV_PATH)
    try:
        from dotenv import load_dotenv

        if _ENV_PATH.exists():
            # Do not override already-exported shell env vars.
            load_dotenv(dotenv_path=_ENV_PATH, override=False)
            loaded = True
        else:
            load_dotenv(override=False)
            path_used = "(cwd search)"
            loaded = True
    except ImportError:
        loaded = False

    _DOTENV_LOADED = loaded
    # Keep provider_runtime helper in sync for callers that use it later.
    try:
        from services.provider_runtime.config import load_dotenv_if_available

        load_dotenv_if_available()
    except Exception:  # noqa: BLE001
        pass

    return {
        "loaded": loaded,
        "path": path_used,
        "exists": _ENV_PATH.exists(),
        "created": bool(created.get("created")),
        "project_root": str(_PROJECT_ROOT),
    }


def credential_status(env_var: str) -> dict[str, Any]:
    """Whether a credential is available (never returns the secret)."""
    from services.provider_runtime.config import get_credential

    value = (get_credential(env_var) or "").strip()
    source = "missing"
    if value:
        if os.environ.get(env_var):
            source = "environment"
        else:
            source = "secrets_file"
    return {
        "env_var": env_var,
        "present": bool(value),
        "source": source,
        "length": len(value),
    }


def startup_credential_report(keys: "tuple[str, ...] | None" = None) -> dict[str, Any]:
    """Human-readable startup report for core provider keys."""
    keys = keys or CORE_ENV_KEYS
    rows = [credential_status(key) for key in keys]
    openai = next((r for r in rows if r["env_var"] == "OPENAI_API_KEY"), None)
    youtube = next((r for r in rows if r["env_var"] == "YOUTUBE_API_KEY"), None)
    lines = []
    for row in rows:
        mark = "✓" if row["present"] else "✗"
        detail = f"loaded ({row['source']})" if row["present"] else "missing"
        lines.append(f"{mark} {row['env_var']} {detail}")

    youtube_validation: dict[str, Any] = {"skipped": True}
    if youtube and youtube["present"]:
        try:
            from services.providers.youtube_provider import validate_youtube_startup

            youtube_validation = validate_youtube_startup()
            for yline in youtube_validation.get("lines") or []:
                lines.append(yline)
        except Exception as exc:  # noqa: BLE001
            youtube_validation = {"ok": False, "error": str(exc)[:200]}
            lines.append("✗ YouTube API validation error (see logs — key never printed)")
    else:
        lines.append("✗ YouTube API detected (YOUTUBE_API_KEY missing)")

    return {
        "openai_loaded": bool(openai and openai["present"]),
        "youtube_loaded": bool(youtube and youtube["present"]),
        "youtube_validation": youtube_validation,
        "demo_mode": not bool(openai and openai["present"]),
        "lines": lines,
        "rows": rows,
        "env_path": str(_ENV_PATH),
        "env_exists": _ENV_PATH.exists(),
    }


def write_env_value(env_var: str, value: str) -> dict[str, Any]:
    """Upsert one KEY=value in the project `.env` without printing the secret."""
    env_var = str(env_var or "").strip()
    value = str(value or "").strip()
    if not env_var or not value:
        return {"ok": False, "error": "env_var and value required"}
    ensure_env_file()
    lines = _ENV_PATH.read_text(encoding="utf-8").splitlines() if _ENV_PATH.exists() else []
    prefix = f"{env_var}="
    replaced = False
    new_lines = []
    for line in lines:
        if line.startswith(prefix) or line.startswith(f"export {prefix}"):
            new_lines.append(f"{env_var}={value}")
            replaced = True
        else:
            new_lines.append(line)
    if not replaced:
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        new_lines.append(f"{env_var}={value}")
    _ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    os.environ[env_var] = value
    return {"ok": True, "env_var": env_var, "path": str(_ENV_PATH), "updated": replaced}
