"""SEO signal provider registry with automatic discovery.

Adding a new SEO signal source requires exactly one step: drop a module in
this package containing a `SeoSourceProvider` subclass. The registry scans
the package at runtime, instantiates every concrete provider, and exposes
them to the Global Content Optimization Engine. No registration code, no
imports to edit — mirrors `providers/trend_sources/`.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil

from core.log import get_logger, log_event
from providers.seo_sources.base import SeoSourceProvider

logger = get_logger(__name__)

_registry: "dict[str, SeoSourceProvider] | None" = None


def _scan_package() -> dict[str, SeoSourceProvider]:
    """Import every module in this package and collect provider instances."""
    registry: dict[str, SeoSourceProvider] = {}
    package_path = __path__
    for module_info in pkgutil.iter_modules(package_path):
        name = module_info.name
        if name.startswith("_") or name == "base":
            continue
        try:
            module = importlib.import_module(f"{__name__}.{name}")
        except Exception as exc:
            log_event(logger, "seo.module_import_failed", level=30, module=name, error=str(exc))
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, SeoSourceProvider)
                and obj is not SeoSourceProvider
                and not inspect.isabstract(obj)
                and obj.__module__ == module.__name__
            ):
                try:
                    instance = obj()
                    registry[instance.key] = instance
                except Exception as exc:
                    log_event(
                        logger, "seo.provider_init_failed", level=30,
                        provider=obj.__name__, error=str(exc),
                    )
    return registry


def get_seo_provider_registry() -> dict[str, SeoSourceProvider]:
    global _registry
    if _registry is None:
        _registry = _scan_package()
        log_event(logger, "seo.registry_loaded", providers=len(_registry))
    return _registry


def get_seo_providers() -> list[SeoSourceProvider]:
    return list(get_seo_provider_registry().values())
