"""Trend provider registry with automatic discovery.

Adding a new trend source requires exactly one step: drop a module in this
package containing a `TrendSourceProvider` subclass. The registry scans the
package at runtime, instantiates every concrete provider, and exposes them
to the Trend Discovery Manager. No registration code, no imports to edit.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil

from core.log import get_logger, log_event
from providers.trend_sources.base import TrendSourceProvider

logger = get_logger(__name__)

_registry: "dict[str, TrendSourceProvider] | None" = None


def _scan_package() -> dict[str, TrendSourceProvider]:
    """Import every module in this package and collect provider instances."""
    registry: dict[str, TrendSourceProvider] = {}
    package_path = __path__
    for module_info in pkgutil.iter_modules(package_path):
        name = module_info.name
        if name.startswith("_") or name == "base":
            continue
        try:
            module = importlib.import_module(f"{__name__}.{name}")
        except Exception as exc:
            log_event(logger, "trends.module_import_failed", level=30, module=name, error=str(exc))
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, TrendSourceProvider)
                and obj is not TrendSourceProvider
                and not inspect.isabstract(obj)
                and obj.__module__ == module.__name__
            ):
                try:
                    instance = obj()
                    registry[instance.key] = instance
                except Exception as exc:
                    log_event(
                        logger, "trends.provider_init_failed", level=30,
                        provider=obj.__name__, error=str(exc),
                    )
    return registry


def get_trend_provider_registry() -> dict[str, TrendSourceProvider]:
    global _registry
    if _registry is None:
        _registry = _scan_package()
        log_event(logger, "trends.registry_loaded", providers=len(_registry))
    return _registry


def get_trend_providers() -> list[TrendSourceProvider]:
    return list(get_trend_provider_registry().values())
