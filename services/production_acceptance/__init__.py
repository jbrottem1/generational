"""Production Acceptance Testing System V1.0.

Prove the Generational platform is production-ready after every major update.

    from services.production_acceptance import run_acceptance_suite
    run_acceptance_suite(mode="smoke")
"""

from __future__ import annotations

from services.production_acceptance.catalog import ACCEPTANCE_VERSION, CATEGORIES, MODES
from services.production_acceptance.dashboard import build_acceptance_dashboard
from services.production_acceptance.models import load_history
from services.production_acceptance.runner import run_acceptance_suite

__all__ = [
    "ACCEPTANCE_VERSION",
    "CATEGORIES",
    "MODES",
    "build_acceptance_dashboard",
    "load_history",
    "run_acceptance_suite",
]
