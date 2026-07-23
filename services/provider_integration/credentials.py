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


def set_api_key(env_var: str, value: str, *, persist: bool = True, write_dotenv: bool = True) -> dict:
    """Store a key in process env, optional .env file, and SecretManager."""
    import os

    env_var = str(env_var or "").strip()
    value = str(value or "").strip()
    if not env_var or not value:
        return {"ok": False, "error": "env_var and value required"}

    # Immediate process visibility for Demo Mode / providers.
    os.environ[env_var] = value

    env_write = {"ok": False}
    if persist and write_dotenv:
        try:
            from core.env import write_env_value

            env_write = write_env_value(env_var, value)
        except Exception as exc:  # noqa: BLE001
            env_write = {"ok": False, "error": str(exc)}

    mgr = _manager()
    mgr.set_override(env_var, value)
    if persist:
        mgr.rotate(env_var, value)
        if not mgr.get(env_var):
            mgr.set_override(env_var, value)

    get_audit_log().record("api_key_set", env_var=env_var, length=len(value))
    return {
        "ok": True,
        "env_var": env_var,
        "masked": mask_secret(value),
        "wrote_dotenv": bool(env_write.get("ok")),
        "dotenv_path": env_write.get("path", ""),
    }


def rotate_api_key(env_var: str, new_value: str) -> dict:
    return set_api_key(env_var, new_value, persist=True)


def delete_api_key(env_var: str) -> dict:
    env_var = str(env_var or "").strip()
    if not env_var:
        return {"ok": False, "error": "env_var required"}
    removed = _manager().delete(env_var)
    get_audit_log().record("api_key_deleted", env_var=env_var, removed=removed)
    return {"ok": removed, "env_var": env_var}


def import_api_keys(secrets: dict[str, str], *, write_dotenv: bool = True) -> dict:
    import os

    count = _manager().import_secrets(secrets or {})
    wrote = 0
    if write_dotenv:
        try:
            from core.env import write_env_value

            for key, value in (secrets or {}).items():
                if key and value:
                    os.environ[str(key)] = str(value)
                    if write_env_value(str(key), str(value)).get("ok"):
                        wrote += 1
        except Exception:  # noqa: BLE001
            pass
    else:
        for key, value in (secrets or {}).items():
            if key and value:
                os.environ[str(key)] = str(value)
    get_audit_log().record("api_keys_imported", count=count)
    return {"ok": True, "imported": count, "wrote_dotenv": wrote}


def validate_api_key(provider: str) -> dict:
    """Validate credential presence/format for a known provider (no secret returned)."""
    return validate_credential(provider)
