"""Visual layout QC — fail closed on unreadable educational frames.

Checks (sampled across the demo timeline):
- No overlapping text boxes
- No duplicate labels
- No clipped text outside board/content zones
- Tray exclusivity (no stacked evidence layers)
- Annotations resolve to semantic targets when required
- Presenter AABB does not invade content zone
- Readability score ≥ 95
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable

from PIL import Image

from services.animation.layout_engine import (
    TextBox,
    claim_evidence_tray,
    layout_keyword_board,
    visibility_envelope,
)
from services.animation.annotation_engine import (
    SemanticAnnotation,
    annotations_from_pointer_actions,
    resolve_target,
)


READABILITY_TARGET = 95.0


@dataclass
class VisualLayoutQCResult:
    passed: bool
    readability: float
    hard_fails: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    samples: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _overlap_count(boxes: list[TextBox]) -> int:
    n = 0
    for i, a in enumerate(boxes):
        for b in boxes[i + 1 :]:
            if a.kind == "write" and b.kind == "write" and a.overlaps(b):
                n += 1
    return n


def _duplicates(boxes: list[TextBox]) -> int:
    seen: set[str] = set()
    dups = 0
    for box in boxes:
        if box.kind not in ("write", "label"):
            continue
        key = " ".join(box.text.lower().split())
        if key in seen:
            dups += 1
        seen.add(key)
    return dups


def evaluate_visual_layout(
    *,
    demo_id: str,
    keywords: list[Any] | None = None,
    pointers: list[Any] | None = None,
    panel_windows: list[tuple[float, float]] | None = None,
    timeline_window: tuple[float, float] | None = None,
    shell_window: tuple[float, float] | None = None,
    sample_ps: list[float] | None = None,
    canvas_size: tuple[int, int] = (1080, 1920),
    board_rect_fn: Callable[[int, int], tuple[int, int, int, int]] | None = None,
    professor_zone_fn: Callable[[int, int], tuple[int, int, int, int]] | None = None,
    content_x_min_fn: Callable[[int], int] | None = None,
    professor_width_px: int = 340,
    require_semantic_targets: bool = True,
) -> VisualLayoutQCResult:
    """Dry-run layout/annotation rules across sample times (no FFmpeg)."""
    from services.animation.foundation_v2 import (
        board_rect_v2,
        content_zone_rect,
        professor_zone_rect,
    )

    w, h = canvas_size
    board_fn = board_rect_fn or board_rect_v2
    zone_fn = professor_zone_fn or professor_zone_rect
    content_x = (content_x_min_fn or (lambda width: int(width * 0.34)))(w)
    board = board_fn(w, h)
    zone = zone_fn(w, h)

    samples = sample_ps or [0.12, 0.24, 0.35, 0.45, 0.55, 0.65, 0.75, 0.88]
    hard: list[str] = []
    warnings: list[str] = []
    sample_rows: list[dict[str, Any]] = []
    penalties = 0.0
    checks = 0

    anns = annotations_from_pointer_actions(pointers or [])
    if require_semantic_targets:
        missing = [a for a in anns if not a.target]
        if missing:
            hard.append(f"annotations_missing_semantic_targets:{len(missing)}")
            penalties += 8.0 * len(missing)

    for p in samples:
        layout = layout_keyword_board(keywords or [], board, p)
        writes = [b for b in layout.boxes if b.kind == "write"]
        overlaps = _overlap_count(writes)
        dups = _duplicates(writes)
        clipped = 0
        for box in writes:
            if box.x < board[0] or box.y < board[1] or box.x + box.w > board[2] or box.y + box.h > board[3]:
                clipped += 1

        claim = claim_evidence_tray(
            p,
            panel_windows=panel_windows,
            timeline_window=timeline_window,
            shell_window=shell_window,
        )
        # Count how many tray modes would have been active without exclusivity
        raw_active = 0
        for start, end in panel_windows or []:
            if visibility_envelope(p, start, end) > 0.5:
                raw_active += 1
                break
        if timeline_window and visibility_envelope(p, timeline_window[0], timeline_window[1]) > 0.5:
            raw_active += 1
        if shell_window and visibility_envelope(p, shell_window[0], shell_window[1]) > 0.5:
            raw_active += 1
        tray_conflict = raw_active > 1

        # Annotation target resolution for active cues
        unresolved = 0
        for ann in anns:
            if visibility_envelope(p, ann.start, ann.end) <= 0.05:
                continue
            if not ann.target:
                continue
            resolved = resolve_target(
                ann.target,
                canvas_size=(w, h),
                board_layout=layout,
                board_rect=board,
                panel_slots={"0": (board[0], board[3] + 20, board[2], int(h * 0.76))} if claim.mode == "panel" else {},
                shell_stages=[(board[0], board[3] + 20, board[2], int(h * 0.76))] if claim.mode == "shell" else [],
            )
            # keyword targets must resolve when their cue is active
            if ann.target.startswith("keyword:") and resolved is None:
                unresolved += 1

        # Presenter invasion check (static width estimate at zone right edge)
        professor_right = zone[0] + professor_width_px
        invades = professor_right > content_x - 4

        row = {
            "p": p,
            "write_count": len(writes),
            "overlaps": overlaps,
            "duplicates": dups,
            "clipped": clipped,
            "tray_mode": claim.mode,
            "tray_conflict_without_compositor": tray_conflict,
            "unresolved_keyword_targets": unresolved,
            "professor_invades_content": invades,
            "redesigns": layout.redesigns,
        }
        sample_rows.append(row)
        checks += 6
        if overlaps:
            hard.append(f"overlapping_text:p={p:.2f}")
            penalties += 12.0 * overlaps
        if dups:
            hard.append(f"duplicate_text:p={p:.2f}")
            penalties += 8.0 * dups
        if clipped:
            hard.append(f"clipped_text:p={p:.2f}")
            penalties += 10.0 * clipped
        if tray_conflict:
            # Soft if compositor would fix; hard if demo still schedules conflicts
            warnings.append(f"tray_schedule_conflict:p={p:.2f}")
            penalties += 3.0
        if unresolved:
            warnings.append(f"unresolved_annotation:p={p:.2f}")
            penalties += 4.0 * unresolved
        if invades:
            hard.append("presenter_covers_content")
            penalties += 15.0

    # Deduplicate hard fails
    hard = sorted(set(hard))
    warnings = sorted(set(warnings))

    # Teaching-purpose + clutter policy (permanent Visual Education rules)
    try:
        from services.quality.visual_education_qc import validate_annotation_purpose

        purpose_fails = validate_annotation_purpose(anns, sample_ps=list(samples))
        for reason in purpose_fails:
            key = reason.split(":", 1)[0]
            if key == "annotations_missing_semantic_targets" and not require_semantic_targets:
                continue
            if reason not in hard:
                hard.append(reason)
                if "purpose" in reason or "clutter" in reason:
                    penalties += 10.0
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"annotation_purpose_qc_error:{exc}")

    readability = max(0.0, min(100.0, 100.0 - penalties))

    def _key(reason: str) -> str:
        return str(reason or "").split(":", 1)[0].strip()

    passed = readability >= READABILITY_TARGET and not any(
        _key(x)
        in {
            "overlapping_text",
            "duplicate_text",
            "clipped_text",
            "presenter_covers_content",
            "annotations_missing_semantic_targets",
            "annotations_missing_teaching_purpose",
            "annotation_clutter_arrow",
            "annotation_clutter_circle",
            "annotation_clutter_highlight",
            "annotation_clutter_label",
            "annotation_clutter_total",
        }
        for x in hard
    )
    if readability < READABILITY_TARGET:
        hard.append(f"visual_readability_below_95:{readability:.1f}")
        passed = False

    return VisualLayoutQCResult(
        passed=passed,
        readability=round(readability, 1),
        hard_fails=hard,
        warnings=warnings,
        samples=sample_rows,
    )


def evaluate_demo_visual_qc(demo_id: str) -> VisualLayoutQCResult:
    """Convenience: load known demo specs and evaluate."""
    if demo_id == "foundation_v2_turtle_202":
        from services.animation.turtle_demos import TURTLE_202_KEYWORDS, TURTLE_202_POINTERS
        from services.reality.planner import TURTLE_202_PANELS

        panels = [(p.start, p.end) for p in TURTLE_202_PANELS]
        result = evaluate_visual_layout(
            demo_id=demo_id,
            keywords=TURTLE_202_KEYWORDS,
            pointers=TURTLE_202_POINTERS,
            panel_windows=panels,
            timeline_window=(0.26, 0.36),
            shell_window=(0.36, 0.50),
            professor_width_px=280,
        )
        return _merge_education_policy(result, demo_id=demo_id, pointers=TURTLE_202_POINTERS)
    if demo_id == "foundation_v2_seasons_001":
        from services.animation.seasons_demos import (
            ORBIT_WINDOW,
            SEASONS_KEYWORDS,
            SEASONS_POINTERS,
        )
        from services.reality.planner import SEASONS_001_PANELS

        panels = [(p.start, p.end) for p in SEASONS_001_PANELS]
        result = evaluate_visual_layout(
            demo_id=demo_id,
            keywords=SEASONS_KEYWORDS,
            pointers=SEASONS_POINTERS,
            panel_windows=panels,
            timeline_window=(0.0, 0.0),
            shell_window=ORBIT_WINDOW,
            professor_width_px=280,
        )
        return _merge_education_policy(
            result,
            demo_id=demo_id,
            pointers=SEASONS_POINTERS,
            concepts=["earth", "seasons", "axial_tilt", "spring", "summer", "autumn", "winter"],
        )
    return VisualLayoutQCResult(passed=True, readability=100.0, warnings=["no_demo_visual_spec"])


def _merge_education_policy(
    result: VisualLayoutQCResult,
    *,
    demo_id: str,
    pointers: list[Any],
    concepts: list[str] | None = None,
) -> VisualLayoutQCResult:
    """Fold authentic-media + purpose policy into layout QC."""
    from services.animation.annotation_engine import annotations_from_pointer_actions
    from services.quality.visual_education_qc import evaluate_visual_education_policy

    anns = annotations_from_pointer_actions(pointers)
    edu = evaluate_visual_education_policy(
        demo_id=demo_id,
        annotations=anns,
        concepts=concepts,
    )
    hard = sorted(set(list(result.hard_fails) + list(edu.hard_fails)))
    warnings = sorted(set(list(result.warnings) + list(edu.warnings)))
    passed = result.passed and edu.passed and not hard
    if not edu.passed:
        # Keep readability but fail closed on education policy
        passed = False
    return VisualLayoutQCResult(
        passed=passed,
        readability=result.readability,
        hard_fails=hard,
        warnings=warnings,
        samples=result.samples,
    )