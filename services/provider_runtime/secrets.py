"""Secret management — env vars, encrypted config, key rotation helpers.

Never hardcode credentials. Keys resolve from:
1. Runtime credential overrides
2. Environment variables / .env
3. Encrypted secrets file (PROVIDER_SECRETS_PATH or data/provider_runtime/secrets.enc.json)
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from services.provider_runtime.config import get_credential, load_dotenv_if_available

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_SECRETS_PATH = _PROJECT_ROOT / "data" / "provider_runtime" / "secrets.enc.json"


def _derive_fernet_key(passphrase: str) -> bytes:
    """Derive a 32-byte urlsafe key from a passphrase (stdlib-only)."""
    digest = hashlib.sha256(passphrase.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _xor_obfuscate(data: bytes, key: bytes) -> bytes:
    """Lightweight reversible obfuscation when cryptography is unavailable."""
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def encrypt_secrets(secrets: dict[str, str], passphrase: str) -> str:
    """Encrypt a secrets dict to a transportable string."""
    payload = json.dumps(secrets, sort_keys=True).encode("utf-8")
    try:
        from cryptography.fernet import Fernet  # type: ignore

        token = Fernet(_derive_fernet_key(passphrase)).encrypt(payload)
        return token.decode("ascii")
    except ImportError:
        key = hashlib.sha256(passphrase.encode("utf-8")).digest()
        obfuscated = _xor_obfuscate(payload, key)
        return "xor:" + base64.urlsafe_b64encode(obfuscated).decode("ascii")


def decrypt_secrets(token: str, passphrase: str) -> dict[str, str]:
    """Decrypt secrets produced by encrypt_secrets."""
    if token.startswith("xor:"):
        key = hashlib.sha256(passphrase.encode("utf-8")).digest()
        raw = base64.urlsafe_b64decode(token[4:].encode("ascii"))
        payload = _xor_obfuscate(raw, key)
        return json.loads(payload.decode("utf-8"))
    try:
        from cryptography.fernet import Fernet  # type: ignore

        payload = Fernet(_derive_fernet_key(passphrase)).decrypt(token.encode("ascii"))
        return json.loads(payload.decode("utf-8"))
    except ImportError as exc:
        raise RuntimeError("cryptography package required for Fernet secrets") from exc


class SecretManager:
    """Resolves and rotates provider credentials without hardcoding."""

    def __init__(
        self,
        overrides: "dict[str, str] | None" = None,
        secrets_path: "str | Path | None" = None,
        passphrase_env: str = "PROVIDER_SECRETS_PASSPHRASE",
    ) -> None:
        load_dotenv_if_available()
        self._overrides = dict(overrides or {})
        self._secrets_path = Path(secrets_path) if secrets_path else Path(
            os.environ.get("PROVIDER_SECRETS_PATH", str(_DEFAULT_SECRETS_PATH))
        )
        self._passphrase_env = passphrase_env
        self._file_secrets: dict[str, str] = {}
        self._rotation_log: list[dict[str, Any]] = []
        self._load_encrypted_file()

    def _load_encrypted_file(self) -> None:
        if not self._secrets_path.exists():
            return
        passphrase = os.environ.get(self._passphrase_env, "")
        if not passphrase:
            return
        try:
            token = json.loads(self._secrets_path.read_text(encoding="utf-8")).get("token", "")
            if token:
                self._file_secrets = decrypt_secrets(token, passphrase)
        except (OSError, json.JSONDecodeError, ValueError, RuntimeError):
            self._file_secrets = {}

    def get(self, env_var: str) -> str:
        if env_var in self._overrides:
            return self._overrides[env_var]
        env_val = get_credential(env_var)
        if env_val:
            return env_val
        return self._file_secrets.get(env_var, "")

    def has(self, env_var: str) -> bool:
        return bool(self.get(env_var))

    def set_override(self, env_var: str, value: str) -> None:
        self._overrides[env_var] = value

    def rotate(self, env_var: str, new_value: str) -> None:
        """Rotate a credential in-memory and optionally persist encrypted."""
        old = self.get(env_var)
        self._overrides[env_var] = new_value
        self._file_secrets[env_var] = new_value
        self._rotation_log.append(
            {
                "env_var": env_var,
                "rotated": True,
                "had_previous": bool(old),
            }
        )
        passphrase = os.environ.get(self._passphrase_env, "")
        if passphrase:
            self.persist(passphrase)

    def persist(self, passphrase: str) -> Path:
        self._secrets_path.parent.mkdir(parents=True, exist_ok=True)
        token = encrypt_secrets(self._file_secrets, passphrase)
        self._secrets_path.write_text(
            json.dumps({"version": 1, "token": token}, indent=2),
            encoding="utf-8",
        )
        return self._secrets_path

    def rotation_history(self) -> list[dict[str, Any]]:
        return list(self._rotation_log)

    def describe(self) -> dict[str, Any]:
        return {
            "overrides": sorted(self._overrides.keys()),
            "file_secrets": sorted(self._file_secrets.keys()),
            "secrets_path": str(self._secrets_path),
            "rotations": len(self._rotation_log),
        }
