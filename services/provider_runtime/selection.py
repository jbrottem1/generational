"""ProviderSelectionEngine — capability-based provider routing."""

from __future__ import annotations

from services.provider_runtime.adapter import ProviderAdapter
from services.provider_runtime.models import ProviderRequest
from services.provider_runtime.registry import (
    available_providers,
    get_priority,
    get_provider,
    health_score,
    providers_for_capability,
)


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

    def best(self, capability: str) -> "ProviderAdapter | None":
        ranked = self.rank_all(capability, "quality")
        available = [p for p in ranked if p.is_available()]
        return available[0] if available else (ranked[0] if ranked else None)

    def cheapest(self, capability: str) -> "ProviderAdapter | None":
        ranked = self.rank_all(capability, "cost")
        available = [p for p in ranked if p.is_available()]
        return available[0] if available else (ranked[0] if ranked else None)

    def fastest(self, capability: str) -> "ProviderAdapter | None":
        ranked = self.rank_all(capability, "speed")
        available = [p for p in ranked if p.is_available()]
        return available[0] if available else (ranked[0] if ranked else None)

    def highest_quality(self, capability: str) -> "ProviderAdapter | None":
        return self.best(capability)

    def fallback_provider(self, capability: str, exclude: str = "") -> "ProviderAdapter | None":
        for provider in self.rank_all(capability, "quality"):
            if provider.name == exclude:
                continue
            if provider.is_available() or provider.name == "demo":
                return provider
        return get_provider("demo")

    def _rank(self, candidates: list[ProviderAdapter], optimize_for: str) -> ProviderAdapter:
        return max(candidates, key=lambda p: self._score(p, optimize_for))

    def _score(self, provider: ProviderAdapter, optimize_for: str) -> float:
        profile = provider.profile
        priority_boost = get_priority(provider.name) * 10.0
        health_boost = health_score(provider.name) * 0.05
        # Prefer real production connectors over demo when both available.
        impl = getattr(provider, "implementation_status", "")
        production_boost = 5.0 if impl == "production" and provider.is_available() else 0.0
        # Soft-penalize demo so real providers win when keys are present.
        demo_penalty = 40.0 if provider.name == "demo" else 0.0

        if optimize_for == "cost":
            cost_penalty = profile.cost_per_unit * 100
            return (
                profile.quality
                + profile.speed
                - cost_penalty
                + priority_boost
                + health_boost
                + production_boost
                - demo_penalty
            )
        if optimize_for == "speed":
            return (
                profile.speed * 1.5
                + profile.quality * 0.5
                - profile.cost_per_unit * 10
                + priority_boost
                + health_boost
                + production_boost
                - demo_penalty
            )
        return (
            profile.quality
            + profile.consistency * 0.3
            - profile.cost_per_unit * 5
            + priority_boost
            + health_boost
            + production_boost
            - demo_penalty
        )
