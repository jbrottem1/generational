"""ProviderSelectionEngine — capability-based provider routing."""

from __future__ import annotations

from services.provider_runtime.adapter import ProviderAdapter
from services.provider_runtime.models import ProviderRequest
from services.provider_runtime.registry import available_providers, get_provider, providers_for_capability


class ProviderSelectionEngine:
    """Selects the best provider for a given operation and optimization goal."""

    def select(
        self,
        request: ProviderRequest,
        capability: str = "",
    ) -> "ProviderAdapter | None":
        cap = capability or request.capability
        if request.preferred_provider:
            preferred = get_provider(request.preferred_provider)
            if preferred and preferred.is_available() and (not cap or preferred.supports(cap)):
                return preferred

        candidates = available_providers(cap) if cap else available_providers()
        if not candidates:
            # Fall back to registered but unavailable stubs for demo routing
            candidates = providers_for_capability(cap) if cap else []
        if not candidates:
            return None

        return self._rank(candidates, request.optimize_for)

    def rank_all(
        self,
        capability: str,
        optimize_for: str = "quality",
    ) -> list[ProviderAdapter]:
        candidates = providers_for_capability(capability)
        return sorted(
            candidates,
            key=lambda p: self._score(p, optimize_for),
            reverse=True,
        )

    def _rank(self, candidates: list[ProviderAdapter], optimize_for: str) -> ProviderAdapter:
        return max(candidates, key=lambda p: self._score(p, optimize_for))

    def _score(self, provider: ProviderAdapter, optimize_for: str) -> float:
        profile = provider.profile
        if optimize_for == "cost":
            cost_penalty = profile.cost_per_unit * 100
            return profile.quality + profile.speed - cost_penalty
        if optimize_for == "speed":
            return profile.speed * 1.5 + profile.quality * 0.5 - profile.cost_per_unit * 10
        return profile.quality + profile.consistency * 0.3 - profile.cost_per_unit * 5
