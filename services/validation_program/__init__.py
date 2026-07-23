"""Generational V1 Validation Program — measure real productions, not assumptions."""

from __future__ import annotations

from services.validation_program.catalog import CATEGORIES, MEASUREMENT_DIMENSIONS, build_validation_catalog, filter_catalog
from services.validation_program.dashboard import build_executive_dashboard, write_executive_dashboard
from services.validation_program.library import list_validations, store_validation
from services.validation_program.runner import ingest_existing_production, run_validation_program

__all__ = [
    "CATEGORIES",
    "MEASUREMENT_DIMENSIONS",
    "build_executive_dashboard",
    "build_validation_catalog",
    "filter_catalog",
    "ingest_existing_production",
    "list_validations",
    "run_validation_program",
    "store_validation",
    "write_executive_dashboard",
]
