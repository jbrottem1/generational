"""ProviderAdapter — the universal adapter interface for all AI backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from services.provider_runtime.models import ProviderProfile, ProviderRequest, ProviderResponse

if TYPE_CHECKING:
    pass


class ProviderAdapter(ABC):
    """One swappable AI backend. Vendor SDKs live only in adapter subclasses."""

    name: str = "base"
    label: str = ""
    capabilities: "tuple[str, ...]" = ()
    api_key_env: str = ""
    offline: bool = False
    local: bool = False
    profile: ProviderProfile = ProviderProfile()

    def is_available(self) -> bool:
        """Whether this adapter can serve requests right now."""
        if self.offline or self.local:
            return True
        if not self.api_key_env:
            return False
        from services.provider_runtime.config import has_credential

        return has_credential(self.api_key_env, self._credential_overrides())

    def _credential_overrides(self) -> "dict[str, str] | None":
        return getattr(self, "_overrides", None)

    def set_credential_overrides(self, overrides: "dict[str, str]") -> None:
        self._overrides = overrides

    def supports(self, capability: str) -> bool:
        return capability in self.capabilities

    def estimate_cost(self, request: ProviderRequest) -> float:
        return float(self.profile.cost_per_unit)

    def estimate_latency_ms(self, request: "ProviderRequest | None" = None) -> int:
        if self.profile.latency_ms > 0:
            return self.profile.latency_ms
        speed = float(self.profile.speed)
        return int(max(1000, 30_000 - (speed / 100.0) * 29_000))

    def describe(self) -> dict:
        return {
            "name": self.name,
            "label": self.label or self.name,
            "capabilities": list(self.capabilities),
            "available": self.is_available(),
            "offline": self.offline,
            "local": self.local,
            "profile": self.profile.to_dict(),
            "api_key_env": self.api_key_env,
        }

    @abstractmethod
    def execute(self, request: ProviderRequest) -> ProviderResponse:
        """Run one operation. Must not raise — return error in ProviderResponse."""

    def health_check(self) -> dict:
        """Lightweight availability probe for health monitoring."""
        return {"provider": self.name, "available": self.is_available(), "healthy": self.is_available()}
