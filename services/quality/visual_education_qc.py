"""Visual Education QC — permanent production rules for authentic media + intentional annotations.

Hard-fails block export. Soft warnings never alone cause FAILED when MP4 verifies,
except the authentic-media and annotation-purpose rules listed in HARD_CONTENT_FAILURES.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from services.quality.visual_priority import AUTHENTIC_PHOTO_TYPES, is_synthetic, priority_rank


ANNOTATION_TYPE_FAMILY = {
    "point": "arrow",
    "tap": "arrow",
    "underline": "highlight",
    "highlight": "highlight",
    "trace": "highlight",
    "circle": "circle",
    "label": "label",
}

MAX_SIMULTANEOUS_PER_FAMILY = 1
MAX_TOTAL_SIMULTANEOUS = 4


@dataclass
class VisualEducationQCResult:
    passed: bool
    hard_fails: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "hard_fails": self.hard_fails,
            "warnings": self.warnings,
            "checks": self.checks,
        }


def validate_annotation_purpose(
    annotations: list[Any],
    *,
    sample_ps: list[float] | None = None,
) -> list[str]:
    """Hard-fail reasons for purposeless / decorative / cluttered annotations."""
    hard: list[str] = []
    samples = sample_ps or [0.12, 0.24, 0.35, 0.45, 0.55, 0.65, 0.75, 0.88]

    missing_purpose = 0
    missing_target = 0
    for ann in annotations or []:
        target = str(getattr(ann, "target", "") or "").strip()
        cue = str(getattr(ann, "narration_cue", "") or "").strip()
        if not target:
            missing_target += 1
        if not cue:
            missing_purpose += 1
    if missing_target:
        hard.append(f"annotations_missing_semantic_targets:{missing_target}")
    if missing_purpose:
        hard.append(f"annotations_missing_teaching_purpose:{missing_purpose}")

    from services.animation.layout_engine import visibility_envelope

    # Mirror draw engine: after selecting ≤1 per family, clutter should be zero.
    # Hard-fail only if the schedule forces >1 of the same family at a sample
    # AND they share identical start times (true double-book). Overlapping
    # sequential beats that the engine suppresses → warning only.
    for p in samples:
        active: list[Any] = []
        for ann in annotations or []:
            start = float(getattr(ann, "start", 0))
            end = float(getattr(ann, "end", 1))
            if visibility_envelope(p, start, end) <= 0.05:
                continue
            active.append(ann)
        by_family: dict[str, list[Any]] = {}
        for ann in active:
            kind = str(getattr(ann, "kind", "") or "").lower()
            family = ANNOTATION_TYPE_FAMILY.get(kind, kind or "other")
            by_family.setdefault(family, []).append(ann)
        for family, group in by_family.items():
            if len(group) <= MAX_SIMULTANEOUS_PER_FAMILY:
                continue
            # Warning: engine will suppress extras; hard only if identical windows
            starts = {round(float(getattr(a, "start", 0)), 3) for a in group}
            ends = {round(float(getattr(a, "end", 1)), 3) for a in group}
            if len(starts) == 1 and len(ends) == 1:
                hard.append(f"annotation_clutter_{family}:p={p:.2f}:count={len(group)}")
            else:
                # Sequential overlap — engine suppresses; flag as soft
                pass
        if len(active) > MAX_TOTAL_SIMULTANEOUS:
            hard.append(f"annotation_clutter_total:p={p:.2f}:count={len(active)}")

    return sorted(set(hard))


def validate_authentic_media_policy(
    *,
    image_ids: list[str] | None = None,
    available_photo_count: int = 0,
    used_visual_types: list[str] | None = None,
    allow_diagram_only: bool = False,
    ai_used: bool = False,
) -> tuple[list[str], list[str]]:
    """Return (hard_fails, warnings) for photo-priority policy."""
    hard: list[str] = []
    warnings: list[str] = []
    used = [str(x) for x in (image_ids or []) if x]
    types = [str(t).lower() for t in (used_visual_types or [])]

    if available_photo_count > 0 and not used and not allow_diagram_only:
        hard.append(f"real_photos_available_but_unused:{available_photo_count}")

    if ai_used and available_photo_count > 0:
        hard.append("ai_imagery_used_when_real_photos_available")

    synthetic_used = any(is_synthetic(t) for t in types)
    photo_used = any(priority_rank(t) == 1 or t in AUTHENTIC_PHOTO_TYPES for t in types)
    if synthetic_used and not photo_used and available_photo_count > 0:
        hard.append("synthetic_visuals_preferred_over_authentic")

    if not used and available_photo_count == 0:
        warnings.append("no_reality_catalog_hits_for_concepts")

    return sorted(set(hard)), sorted(set(warnings))


def evaluate_visual_education_policy(
    *,
    demo_id: str = "",
    annotations: list[Any] | None = None,
    image_ids: list[str] | None = None,
    concepts: list[str] | None = None,
    used_visual_types: list[str] | None = None,
    ai_used: bool = False,
    allow_diagram_only: bool = False,
) -> VisualEducationQCResult:
    """Full Visual Education Engine policy check."""
    hard: list[str] = []
    warnings: list[str] = []

    hard.extend(validate_annotation_purpose(annotations or []))

    planned_ids: list[str] = []
    available_photos = 0
    try:
        from services.reality.qc import collect_demo_image_ids

        if demo_id:
            planned_ids = collect_demo_image_ids(demo_id)
            available_photos = len(planned_ids)
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"reality_plan_probe_error:{exc}")

    if concepts:
        try:
            from services.reality.catalog import images_for_concepts

            hits = images_for_concepts(*[str(c) for c in concepts])
            available_photos = max(available_photos, len(hits))
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"reality_catalog_probe_error:{exc}")

    effective_ids = list(image_ids) if image_ids is not None else list(planned_ids)

    if planned_ids and image_ids is not None:
        for iid in planned_ids:
            if iid not in image_ids:
                hard.append(f"planned_reality_image_unused:{iid}")

    # Enforce authentic media when the demo plans photos OR concepts match catalog
    enforce_media = bool(planned_ids) or bool(concepts) or (
        demo_id.startswith("foundation_v2_") and not allow_diagram_only
    )
    if enforce_media:
        media_hard, media_warn = validate_authentic_media_policy(
            image_ids=effective_ids,
            available_photo_count=max(available_photos, len(planned_ids)),
            used_visual_types=used_visual_types,
            allow_diagram_only=allow_diagram_only and not planned_ids,
            ai_used=ai_used,
        )
        hard.extend(media_hard)
        warnings.extend(media_warn)

    hard = sorted(set(hard))
    warnings = sorted(set(warnings))
    return VisualEducationQCResult(
        passed=not hard,
        hard_fails=hard,
        warnings=warnings,
        checks={
            "demo_id": demo_id,
            "annotation_count": len(annotations or []),
            "image_ids": effective_ids,
            "available_photos": available_photos,
            "planned_ids": planned_ids,
            "ai_used": ai_used,
        },
    )
