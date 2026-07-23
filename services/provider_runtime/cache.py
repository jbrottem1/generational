"""Response cache for provider operations — content-addressed, TTL-aware."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from services.provider_runtime.models import ProviderRequest, ProviderResponse

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CACHE_DIR = _PROJECT_ROOT / "data" / "provider_runtime" / "cache"


class ProviderCache:
    """Disk-backed cache keyed by operation + payload fingerprint."""

    def __init__(
        self,
        cache_dir: "str | Path | None" = None,
        ttl_sec: float = 3600.0,
        enabled: bool = True,
    ) -> None:
        self._dir = Path(cache_dir) if cache_dir else _DEFAULT_CACHE_DIR
        self._ttl = ttl_sec
        self._enabled = enabled
        self._hits = 0
        self._misses = 0
        if self._enabled:
            self._dir.mkdir(parents=True, exist_ok=True)

    @property
    def enabled(self) -> bool:
        return self._enabled

    def fingerprint(self, request: ProviderRequest, provider: str = "") -> str:
        payload = {
            "operation": request.operation,
            "capability": request.capability,
            "provider": provider,
            "payload": request.payload,
        }
        raw = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, request: ProviderRequest, provider: str = "") -> "ProviderResponse | None":
        if not self._enabled:
            return None
        key = self.fingerprint(request, provider)
        path = self._dir / f"{key}.json"
        if not path.exists():
            self._misses += 1
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if time.time() - float(data.get("cached_at", 0)) > self._ttl:
                path.unlink(missing_ok=True)
                self._misses += 1
                return None
            body = data["response"]
            self._hits += 1
            return ProviderResponse(
                success=bool(body.get("success")),
                data=dict(body.get("data") or {}),
                provider=body.get("provider", provider),
                operation=body.get("operation", request.operation),
                error=body.get("error", ""),
                demo_mode=bool(body.get("demo_mode")),
                tokens_used=int(body.get("tokens_used") or 0),
                cost_usd=float(body.get("cost_usd") or 0),
                latency_ms=int(body.get("latency_ms") or 0),
                metadata={**(body.get("metadata") or {}), "cache_hit": True},
            )
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            self._misses += 1
            return None

    def put(self, request: ProviderRequest, response: ProviderResponse, provider: str = "") -> None:
        if not self._enabled or not response.success:
            return
        # Fingerprint by request only so get()/put() share the same key
        # regardless of which provider served the response.
        key = self.fingerprint(request, provider)
        path = self._dir / f"{key}.json"
        try:
            path.write_text(
                json.dumps(
                    {
                        "cached_at": time.time(),
                        "response": response.to_dict(),
                    },
                    indent=2,
                    default=str,
                ),
                encoding="utf-8",
            )
        except OSError:
            pass

    def stats(self) -> dict[str, Any]:
        return {
            "enabled": self._enabled,
            "hits": self._hits,
            "misses": self._misses,
            "dir": str(self._dir),
            "ttl_sec": self._ttl,
        }

    def clear(self) -> int:
        if not self._dir.exists():
            return 0
        count = 0
        for path in self._dir.glob("*.json"):
            path.unlink(missing_ok=True)
            count += 1
        self._hits = 0
        self._misses = 0
        return count
