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
from services.provider_runtime.reliability import ProviderReliabilityManager

_shared_reliability: "ProviderReliabilityManager | None" = None


def get_reliability_manager() -> ProviderReliabilityManager:
    global _shared_reliability
    if _shared_reliability is None:
        _shared_reliability = ProviderReliabilityManager()
    return _shared_reliability


def set_reliability_manager(manager: "ProviderReliabilityManager | None") -> None:
    global _shared_reliability
    _shared_reliability = manager


class ProviderSelectionEngine:
    """Selects the best provider for a given operation and optimization goal."""

    def __init__(self, reliability: "ProviderReliabilityManager | None" = None) -> None:
        self._reliability = reliability or get_reliability_manager()

    def select(
        self,
        request: ProviderRequest,
        capability: str = "",
    ) -> "ProviderAdapter | None":
        cap = capability or request.capability
        if request.preferred_provider:
            preferred = get_provider(request.preferred_provider)
            if (
                preferred
                and preferred.is_available()
                and (not cap or preferred.supports(cap))
                and not self._reliability.is_blacklisted(preferred.name)
            ):
                return preferred

        candidates = available_providers(cap) if cap else available_providers()
        candidates = [c for c in candidates if not self._reliability.is_blacklisted(c.name)]
        if not candidates:
            # Fall back to registered but unavailable stubs for demo routing
            candidates = [
                p for p in (providers_for_capability(cap) if cap else [])
                if not self._reliability.is_blacklisted(p.name)
            ]
        if not candidates:
            return None

        return self._rank(candidates, request.optimize_for)

    def rank_all(
        self,
        capability: str,
        optimize_for: str = "quality",
    ) -> list[ProviderAdapter]:
        candidates = [
            p for p in providers_for_capability(capability)
            if not self._reliability.is_blacklisted(p.name)
        ]
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
        weight_boost = (self._reliability.get_weight(provider.name) - 1.0) * 15.0
        latency_penalty = self._reliability._latency[provider.name].avg_ms / 1000.0
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
                + weight_boost
                + production_boost
                - demo_penalty
                - latency_penalty
            )
        if optimize_for == "speed":
            return (
                profile.speed * 1.5
                + profile.quality * 0.5
                - profile.cost_per_unit * 10
                + priority_boost
                + health_boost
                + weight_boost
                + production_boost
                - demo_penalty
                - latency_penalty * 2
            )
        return (
            profile.quality
            + profile.consistency * 0.3
            - profile.cost_per_unit * 5
            + priority_boost
            + health_boost
            + weight_boost
            + production_boost
            - demo_penalty
            - latency_penalty
        )
