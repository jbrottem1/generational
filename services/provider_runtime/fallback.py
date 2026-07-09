"""ProviderFallbackManager — graceful degradation across providers."""

from __future__ import annotations

from services.provider_runtime.adapter import ProviderAdapter
from services.provider_runtime.models import ProviderRequest, ProviderResponse
from services.provider_runtime.registry import providers_for_capability
from services.provider_runtime.selection import ProviderSelectionEngine


class ProviderFallbackManager:
    """Try primary provider, then fall back through ranked alternatives."""

    def __init__(self, selector: "ProviderSelectionEngine | None" = None) -> None:
        self._selector = selector or ProviderSelectionEngine()

    def execute_with_fallback(
        self,
        request: ProviderRequest,
        executor,
        capability: str = "",
    ) -> ProviderResponse:
        cap = capability or request.capability
        fallbacks_used: list[str] = []
        primary = self._selector.select(request, cap)
        if not primary:
            return ProviderResponse(
                success=False,
                operation=request.operation,
                error=f"No provider available for capability {cap!r}",
            )

        tried: set[str] = set()
        chain = [primary]
        if request.allow_fallback:
            for alt in self._selector.rank_all(cap, request.optimize_for):
                if alt.name not in tried and alt.name != primary.name:
                    chain.append(alt)

        last_response = ProviderResponse(success=False, operation=request.operation)
        for provider in chain:
            if provider.name in tried:
                continue
            tried.add(provider.name)
            response = executor(provider, request)
            response.fallbacks_used = list(fallbacks_used)
            if response.success:
                return response
            fallbacks_used.append(provider.name)
            last_response = response

        last_response.fallbacks_used = fallbacks_used
        return last_response
