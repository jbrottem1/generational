"""Autonomous Optimization & Experimentation Engine (V4.0).

Lazy exports avoid circular imports when submodules are loaded from engines/.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "DEFAULT_VARIANT_COUNT",
    "OPTIMIZATION_PASS_THRESHOLD",
    "OptimizationPackage",
    "build_optimization_dashboard",
    "build_optimization_package",
    "generate_variants",
    "measurable_improvement_signal",
    "search_experiments",
]


def __getattr__(name: str) -> Any:
    if name in ("DEFAULT_VARIANT_COUNT", "OPTIMIZATION_PASS_THRESHOLD", "OptimizationPackage"):
        from services.optimization_lab import models as _models

        return getattr(_models, name)
    if name == "build_optimization_dashboard":
        from services.optimization_lab.dashboard import build_optimization_dashboard

        return build_optimization_dashboard
    if name == "build_optimization_package":
        from services.optimization_lab.director import build_optimization_package

        return build_optimization_package
    if name == "generate_variants":
        from services.optimization_lab.variants import generate_variants

        return generate_variants
    if name == "measurable_improvement_signal":
        from services.optimization_lab.continuous import measurable_improvement_signal

        return measurable_improvement_signal
    if name == "search_experiments":
        from services.optimization_lab.history import search_experiments

        return search_experiments
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
