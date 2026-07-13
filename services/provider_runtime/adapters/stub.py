"""Shared stub adapter base for production-ready vendor placeholders."""

from __future__ import annotations

from services.provider_runtime.adapter import ProviderAdapter
from services.provider_runtime.models import ProviderProfile, ProviderRequest, ProviderResponse


class StubAdapter(ProviderAdapter):
    """Available when API key is set; returns not-implemented until wired."""

    def execute(self, request: ProviderRequest) -> ProviderResponse:
        if not self.is_available():
            return ProviderResponse(
                success=False,
                operation=request.operation,
                provider=self.name,
                error=f"{self.name} is not available (missing API key)",
            )
        return ProviderResponse(
            success=False,
            operation=request.operation,
            provider=self.name,
            error=f"{self.name} adapter is registered but its API call is not implemented yet",
            cost_usd=self.estimate_cost(request),
            latency_ms=self.estimate_latency_ms(request),
        )


class DemoAdapter(ProviderAdapter):
    """Always-available deterministic demo backend."""

    name = "demo"
    label = "Demo Provider"
    capabilities = ()

    def is_available(self) -> bool:
        return True

    def execute(self, request: ProviderRequest) -> ProviderResponse:
        return ProviderResponse(
            success=True,
            operation=request.operation,
            provider=self.name,
            demo_mode=True,
            data={"placeholder": True, "operation": request.operation, **request.payload},
        )
