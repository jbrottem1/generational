"""Production connector base — HTTP helpers, health probes, cost estimation."""

from __future__ import annotations

import time
from typing import Any

from services.provider_runtime.adapter import ProviderAdapter
from services.provider_runtime.config import get_credential
from services.provider_runtime.http_client import HttpResponse, request_json
from services.provider_runtime.logging_utils import log_request_end, log_request_start
from services.provider_runtime.models import ProviderRequest, ProviderResponse
from services.provider_runtime.versioning import VersionManager


class ProductionConnector(ProviderAdapter):
    """Base class for real vendor connectors routed through ProviderRuntime."""

    base_url: str = ""
    api_version: str = "v1"
    default_timeout_sec: float = 90.0
    implementation_status: str = "production"  # production | partial | stub

    def __init__(self, version_manager: "VersionManager | None" = None) -> None:
        self._version_manager = version_manager or VersionManager()
        self._last_health: dict[str, Any] = {}

    def api_key(self) -> str:
        if not self.api_key_env:
            return ""
        return get_credential(self.api_key_env, self._credential_overrides())

    def auth_headers(self) -> dict[str, str]:
        key = self.api_key()
        return {"Authorization": f"Bearer {key}"} if key else {}

    def resolved_model(self, request: ProviderRequest, default: str = "") -> str:
        payload_model = str(request.payload.get("model") or "")
        if payload_model:
            return payload_model
        return self._version_manager.model_for(self.name, default)

    def http(
        self,
        method: str,
        path: str,
        *,
        json_body: "dict | list | None" = None,
        headers: "dict | None" = None,
        timeout_sec: "float | None" = None,
        retries: int = 1,
        absolute_url: str = "",
    ) -> HttpResponse:
        url = absolute_url or f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        merged = {**self.auth_headers(), **(headers or {})}
        return request_json(
            method,
            url,
            headers=merged,
            json_body=json_body,
            timeout_sec=timeout_sec or self.default_timeout_sec,
            retries=retries,
        )

    def fail(self, request: ProviderRequest, error: str, **extra: Any) -> ProviderResponse:
        return ProviderResponse(
            success=False,
            operation=request.operation,
            provider=self.name,
            error=error,
            cost_usd=self.estimate_cost(request),
            metadata=dict(extra),
        )

    def ok(
        self,
        request: ProviderRequest,
        data: dict,
        *,
        tokens_used: int = 0,
        cost_usd: "float | None" = None,
        **extra: Any,
    ) -> ProviderResponse:
        return ProviderResponse(
            success=True,
            operation=request.operation,
            provider=self.name,
            data=data,
            tokens_used=tokens_used,
            cost_usd=self.estimate_cost(request) if cost_usd is None else cost_usd,
            metadata={"implementation": self.implementation_status, **extra},
        )

    def execute(self, request: ProviderRequest) -> ProviderResponse:
        if not self.is_available():
            return self.fail(request, f"{self.name} is not available (missing API key)")
        log_request_start(self.name, request.operation)
        started = time.time()
        try:
            response = self._execute_impl(request)
        except Exception as exc:  # noqa: BLE001 — adapters must not raise
            response = self.fail(request, str(exc))
        response.latency_ms = int((time.time() - started) * 1000)
        log_request_end(
            self.name,
            request.operation,
            success=response.success,
            latency_ms=response.latency_ms,
            cost_usd=response.cost_usd,
            error=response.error,
        )
        return response

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        raise NotImplementedError(f"{self.name} connector missing _execute_impl")

    def health_check(self) -> dict:
        available = self.is_available()
        probe: dict[str, Any] = {
            "provider": self.name,
            "available": available,
            "healthy": available,
            "implementation": self.implementation_status,
            "api_version": self._version_manager.get(self.name).api_version,
        }
        if available and self.base_url:
            try:
                resp = self._health_probe()
                probe["probe_status"] = resp.status
                probe["healthy"] = resp.ok or resp.status in (200, 204, 404)
            except Exception as exc:  # noqa: BLE001
                probe["healthy"] = False
                probe["probe_error"] = str(exc)
        self._last_health = probe
        return probe

    def _health_probe(self) -> HttpResponse:
        """Default probe — subclasses may override with a cheaper endpoint."""
        return self.http("GET", "/", timeout_sec=10.0, retries=0)

    def describe(self) -> dict:
        base = super().describe()
        base["implementation"] = self.implementation_status
        base["api_version"] = self._version_manager.get(self.name).api_version
        base["model"] = self._version_manager.model_for(self.name)
        return base
