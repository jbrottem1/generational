"""Adapter auto-discovery and registration."""

from __future__ import annotations

from services.provider_runtime.adapters.vendors import register_vendor_adapters
from services.provider_runtime.factory import ProviderFactory
from services.provider_runtime.registry import register_provider


def discover_and_register() -> int:
    """Register all vendor adapter classes and instantiate them."""
    register_vendor_adapters()
    adapters = ProviderFactory.create_all()
    return len(adapters)
