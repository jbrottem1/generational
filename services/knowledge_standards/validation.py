"""Validation rules for Knowledge & Standards capture (Agent 27)."""

from __future__ import annotations

from typing import Any

REQUIRED_EXPERIMENT_FIELDS = (
    "id",
    "objective",
    "method",
    "variables",
    "outcome",
    "metrics",
    "decision",
    "lessons",
    "date",
)

VALID_DECISIONS = frozenset({"keep", "discard", "iterate"})
VALID_STANDARD_MARKERS = frozenset({"LOCKED", "ASPIRATIONAL"})


class KnowledgeValidationError(ValueError):
    """Raised when a knowledge asset fails validation."""


def validate_lesson(
    *,
    title: str,
    source: str,
    body: str | None = None,
    what_worked: list[str] | None = None,
    what_failed: list[str] | None = None,
) -> None:
    """Reject empty lessons (no title/source or no substantive content)."""
    if not title or not str(title).strip():
        raise KnowledgeValidationError("Lesson title must be non-empty")
    if not source or not str(source).strip():
        raise KnowledgeValidationError("Lesson source must be non-empty")

    worked = [w for w in (what_worked or []) if str(w).strip()]
    failed = [w for w in (what_failed or []) if str(w).strip()]
    body_ok = bool(body and str(body).strip())
    if not worked and not failed and not body_ok:
        raise KnowledgeValidationError(
            "Lesson must include what_worked, what_failed, or non-empty body"
        )


def validate_experiment(experiment: dict[str, Any]) -> None:
    """Reject incomplete experiments and bad decisions."""
    if not isinstance(experiment, dict):
        raise KnowledgeValidationError("Experiment must be a dict")

    for field in REQUIRED_EXPERIMENT_FIELDS:
        if field not in experiment:
            raise KnowledgeValidationError(f"Experiment missing required field: {field}")

    exp_id = experiment.get("id")
    if not exp_id or not str(exp_id).strip():
        raise KnowledgeValidationError("Experiment id must be non-empty")

    for text_field in ("objective", "method", "outcome", "date"):
        val = experiment.get(text_field)
        if not val or not str(val).strip():
            raise KnowledgeValidationError(f"Experiment {text_field} must be non-empty")

    variables = experiment.get("variables")
    if not isinstance(variables, list) or not variables:
        raise KnowledgeValidationError("Experiment variables must be a non-empty list")

    metrics = experiment.get("metrics")
    if not isinstance(metrics, dict):
        raise KnowledgeValidationError("Experiment metrics must be a dict")

    lessons = experiment.get("lessons")
    if not isinstance(lessons, list) or not lessons:
        raise KnowledgeValidationError("Experiment lessons must be a non-empty list")

    decision = str(experiment.get("decision", "")).lower()
    if decision not in VALID_DECISIONS:
        raise KnowledgeValidationError(
            f"decision must be one of {sorted(VALID_DECISIONS)}, got {experiment.get('decision')!r}"
        )


def validate_standard_markers(text: str) -> list[str]:
    """Return list of conflict descriptions if LOCKED and ASPIRATIONAL collide in one clause.

    Practical check: lines that contain both markers are flagged.
    """
    if not text or not str(text).strip():
        raise KnowledgeValidationError("Standards text must be non-empty")

    conflicts: list[str] = []
    for i, line in enumerate(str(text).splitlines(), start=1):
        upper = line.upper()
        if "LOCKED" in upper and "ASPIRATIONAL" in upper:
            conflicts.append(f"line {i}: contains both LOCKED and ASPIRATIONAL")
    return conflicts
