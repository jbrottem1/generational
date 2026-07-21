"""Production Quality Assurance — final editor-in-chief before export/publish."""

from __future__ import annotations

from services.production_qa.inspector import inspect_many, inspect_production
from services.production_qa.learning import compare_predicted_vs_actual, record_performance_feedback
from services.production_qa.models import (
    CATEGORY_PASS_THRESHOLD,
    OVERALL_PASS_THRESHOLD,
    PQA_CATEGORIES,
    ProductionQAReport,
    format_report_markdown,
)
from services.production_qa.publish_gate import ProductionQAGate, ensure_pqa_gate_registered
from services.production_qa.revision import build_revision_requests, group_revisions_by_engine
from services.production_qa.store import load_recent_reports, store_report, write_validation_bundle

__all__ = [
    "CATEGORY_PASS_THRESHOLD",
    "OVERALL_PASS_THRESHOLD",
    "PQA_CATEGORIES",
    "ProductionQAGate",
    "ProductionQAReport",
    "build_revision_requests",
    "compare_predicted_vs_actual",
    "ensure_pqa_gate_registered",
    "format_report_markdown",
    "group_revisions_by_engine",
    "inspect_many",
    "inspect_production",
    "load_recent_reports",
    "record_performance_feedback",
    "store_report",
    "write_validation_bundle",
]
