"""Security helpers — credential validation, permissions, audit logging."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from core.log import get_logger, log_event
from services.provider_runtime.config import get_credential, has_credential

logger = get_logger("provider_runtime.security")

# Expected env vars / permission scopes per provider family.
PROVIDER_PERMISSIONS: dict[str, dict[str, Any]] = {
    "openai": {"env": "OPENAI_API_KEY", "scopes": ("chat", "images", "audio"), "pattern": r"^sk-"},
    "anthropic": {"env": "ANTHROPIC_API_KEY", "scopes": ("messages",), "pattern": r"^sk-ant-"},
    "google_gemini": {"env": "GOOGLE_API_KEY", "scopes": ("generateContent",), "pattern": r".+"},
    "xai": {"env": "XAI_API_KEY", "scopes": ("chat",), "pattern": r"^xai-|^sk-"},
    "elevenlabs": {"env": "ELEVENLABS_API_KEY", "scopes": ("tts", "sfx"), "pattern": r".+"},
    "runway": {"env": "RUNWAY_API_KEY", "scopes": ("video",), "pattern": r".+"},
    "flux": {"env": "BFL_API_KEY", "scopes": ("image",), "pattern": r".+"},
    "fal_ai": {"env": "FAL_KEY", "scopes": ("image", "video"), "pattern": r".+"},
    "replicate": {"env": "REPLICATE_API_TOKEN", "scopes": ("predictions",), "pattern": r"^r8_"},
    "youtube": {"env": "YOUTUBE_ACCESS_TOKEN", "scopes": ("youtube.upload",), "pattern": r".+"},
    "tiktok": {"env": "TIKTOK_ACCESS_TOKEN", "scopes": ("video.publish",), "pattern": r".+"},
    "instagram": {"env": "INSTAGRAM_ACCESS_TOKEN", "scopes": ("instagram_content_publish",), "pattern": r".+"},
    "facebook": {"env": "FACEBOOK_ACCESS_TOKEN", "scopes": ("pages_manage_posts",), "pattern": r".+"},
    "x": {"env": "X_ACCESS_TOKEN", "scopes": ("tweet.write",), "pattern": r".+"},
    "linkedin": {"env": "LINKEDIN_ACCESS_TOKEN", "scopes": ("w_member_social",), "pattern": r".+"},
}


class AuditLog:
    """Append-only in-memory audit trail (also emitted via structured logs)."""

    def __init__(self) -> None:
        self._events: list[dict] = []

    def record(self, action: str, **fields: Any) -> dict:
        event = {
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **fields,
        }
        self._events.append(event)
        log_event(logger, f"audit.{action}", **{k: v for k, v in fields.items() if k != "secret"})
        return event

    def events(self, action: str = "") -> list[dict]:
        if not action:
            return list(self._events)
        return [e for e in self._events if e.get("action") == action]

    def clear(self) -> None:
        self._events.clear()


_audit = AuditLog()


def get_audit_log() -> AuditLog:
    return _audit


def validate_credential(provider: str, overrides: "dict[str, str] | None" = None) -> dict:
    """Validate that a provider credential exists and matches expected shape."""
    spec = PROVIDER_PERMISSIONS.get(provider, {})
    env = str(spec.get("env") or "")
    if not env:
        return {"provider": provider, "valid": False, "reason": "unknown provider"}
    value = get_credential(env, overrides)
    if not value:
        result = {"provider": provider, "valid": False, "reason": f"missing {env}", "env": env}
        _audit.record("credential_validation", provider=provider, valid=False, reason=result["reason"])
        return result
    pattern = str(spec.get("pattern") or ".+")
    ok = bool(re.match(pattern, value))
    result = {
        "provider": provider,
        "valid": ok,
        "reason": "" if ok else "credential format mismatch",
        "env": env,
        "scopes": list(spec.get("scopes") or ()),
        "length": len(value),
    }
    _audit.record("credential_validation", provider=provider, valid=ok, reason=result["reason"])
    return result


def validate_permissions(provider: str, required_scopes: "list[str] | None" = None) -> dict:
    """Check declared permission scopes for a provider (config-level)."""
    spec = PROVIDER_PERMISSIONS.get(provider, {})
    declared = list(spec.get("scopes") or ())
    required = list(required_scopes or ())
    missing = [s for s in required if s not in declared]
    result = {
        "provider": provider,
        "declared": declared,
        "required": required,
        "missing": missing,
        "ok": not missing and bool(declared or not required),
    }
    _audit.record("permission_validation", provider=provider, ok=result["ok"], missing=missing)
    return result


def credential_inventory(overrides: "dict[str, str] | None" = None) -> list[dict]:
    """Status of all known provider credentials (never returns secret values)."""
    inventory = []
    for provider, spec in PROVIDER_PERMISSIONS.items():
        env = str(spec.get("env") or "")
        present = has_credential(env, overrides) if env else False
        inventory.append(
            {
                "provider": provider,
                "env": env,
                "present": present,
                "scopes": list(spec.get("scopes") or ()),
            }
        )
    return inventory
