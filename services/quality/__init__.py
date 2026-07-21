"""Multidimensional content quality scoring."""

from services.quality.content_score import (
    DEFAULT_THRESHOLDS,
    FOUNDATION_THRESHOLDS,
    QualityDimension,
    QualityReport,
    hard_fail_reasons,
    score_production,
    soft_warning_reasons,
)
from services.quality.visual_layout_qc import (
    READABILITY_TARGET,
    VisualLayoutQCResult,
    evaluate_demo_visual_qc,
    evaluate_visual_layout,
)
from services.quality.visual_education_qc import (
    VisualEducationQCResult,
    evaluate_visual_education_policy,
    validate_annotation_purpose,
    validate_authentic_media_policy,
)
from services.quality.visual_priority import (
    AUTHENTIC_PHOTO_TYPES,
    prefer_authentic,
    priority_rank,
    select_visual_source,
)

__all__ = [
    "AUTHENTIC_PHOTO_TYPES",
    "DEFAULT_THRESHOLDS",
    "FOUNDATION_THRESHOLDS",
    "QualityDimension",
    "QualityReport",
    "READABILITY_TARGET",
    "VisualEducationQCResult",
    "VisualLayoutQCResult",
    "evaluate_demo_visual_qc",
    "evaluate_visual_education_policy",
    "evaluate_visual_layout",
    "hard_fail_reasons",
    "prefer_authentic",
    "priority_rank",
    "score_production",
    "select_visual_source",
    "soft_warning_reasons",
    "validate_annotation_purpose",
    "validate_authentic_media_policy",
]
