"""Production Validation — prove real videos, not more infrastructure.

    from services.production_validation import run_validation_suite
    run_validation_suite()
"""

from __future__ import annotations

from services.production_validation.catalog import DOMAIN_PRODUCTIONS, SCORE_DIMENSIONS
from services.production_validation.evaluate import aggregate_weaknesses, evaluate_production

__all__ = [
    "DOMAIN_PRODUCTIONS",
    "SCORE_DIMENSIONS",
    "aggregate_weaknesses",
    "evaluate_production",
    "run_validation_suite",
]


def run_validation_suite(*args, **kwargs):
    from services.production_validation.suite import run_validation_suite as _run

    return _run(*args, **kwargs)
