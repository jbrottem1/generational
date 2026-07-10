"""API key management — encrypt at rest, mask in UI, never log values."""

from __future__ import annotations

from typing import Any

from services.provider_runtime.secrets import SecretManager, mask_secret
from services.provider_runtime.security import get_audit_log, validate_credential


def _manager() -> SecretManager:
    return SecretManager()


def list_api_keys() -> list[dict[str, Any]]:
    """Masked inventory of stored / env credentials."""
    from services.provider_runtime.security import credential_inventory
    from services.provider_runtime.config import has_credential

    rows = []
    seen = set()
    for item in credential_inventory():
        env = item.get("env") or ""
        if not env or env in seen:
            continue
        seen.add(env)
        present = bool(item.get("present"))
        rows.append(
            {
                "provider": item.get("provider"),
                "env_var": env,
                "present": present,
                "masked": "•••• configured" if present else "",
                "scopes": item.get("scopes") or [],
                "source": "env_or_secrets" if present else "missing",
            }
        )
    # Include any extra encrypted secrets not in PROVIDER_PERMISSIONS
    for extra in _manager().list_masked():
        if extra["env_var"] in seen:
            continue
        rows.append(
            {
                "provider": "",
                "env_var": extra["env_var"],
                "present": extra["present"],
                "masked": extra["masked"],
                "scopes": [],
                "source": extra["source"],
            }
        )
    return rows


def set_api_key(env_var: str, value: str, *, persist: bool = True) -> dict:
    """Store a key (encrypted when PROVIDER_SECRETS_PASSPHRASE is set)."""
    env_var = str(env_var or "").strip()
    value = str(value or "").strip()
    if not env_var or not value:
        return {"ok": False, "error": "env_var and value required"}
    mgr = _manager()
    mgr.rotate(env_var, value) if persist else mgr.set_override(env_var, value)
    if persist and not mgr.get(env_var):
        # rotate may skip persist without passphrase — keep override
        mgr.set_override(env_var, value)
    get_audit_log().record("api_key_set", env_var=env_var, length=len(value))
    return {"ok": True, "env_var": env_var, "masked": mask_secret(value)}


def rotate_api_key(env_var: str, new_value: str) -> dict:
    return set_api_key(env_var, new_value, persist=True)


def delete_api_key(env_var: str) -> dict:
    env_var = str(env_var or "").strip()
    if not env_var:
        return {"ok": False, "error": "env_var required"}
    removed = _manager().delete(env_var)
    get_audit_log().record("api_key_deleted", env_var=env_var, removed=removed)
    return {"ok": removed, "env_var": env_var}


def import_api_keys(secrets: dict[str, str]) -> dict:
    count = _manager().import_secrets(secrets or {})
    get_audit_log().record("api_keys_imported", count=count)
    return {"ok": True, "imported": count}


def validate_api_key(provider: str) -> dict:
    """Validate credential presence/format for a known provider (no secret returned)."""
    return validate_credential(provider)
