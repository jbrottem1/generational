"""ProviderFactory — instantiate adapters from class registry or config."""

from __future__ import annotations

from services.provider_runtime.adapter import ProviderAdapter
from services.provider_runtime.registry import get_provider, register_provider


class ProviderFactory:
    """Creates and caches provider adapter instances."""

    _adapter_classes: "dict[str, type[ProviderAdapter]]" = {}

    @classmethod
    def register_class(cls, adapter_class: "type[ProviderAdapter]") -> "type[ProviderAdapter]":
        cls._adapter_classes[adapter_class.name] = adapter_class
        return adapter_class

    @classmethod
    def create(cls, name: str, **kwargs) -> "ProviderAdapter | None":
        if name in cls._adapter_classes:
            adapter = cls._adapter_classes[name](**kwargs)
            register_provider(adapter)
            return adapter
        return get_provider(name)

    @classmethod
    def create_all(cls) -> list[ProviderAdapter]:
        adapters = []
        for adapter_class in cls._adapter_classes.values():
            adapter = adapter_class()
            register_provider(adapter)
            adapters.append(adapter)
        return adapters

    @classmethod
    def registered_classes(cls) -> "dict[str, type[ProviderAdapter]]":
        return dict(cls._adapter_classes)
