"""Final production status — SUCCESS / SUCCESS_WITH_WARNINGS / FAILED.

The physical local MP4 is the source of truth for export completion.
Non-critical QC and missing metadata must not flip a playable export to FAILED.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any


class FinalStatus(str, Enum):
    SUCCESS = "SUCCESS"
    SUCCESS_WITH_WARNINGS = "SUCCESS_WITH_WARNINGS"
    FAILED = "FAILED"


# Conditions that mean the MP4 itself is unusable
HARD_EXPORT_FAILURES = frozenset(
    {
        "missing_export_path",
        "export_missing",
        "export_zero_bytes",
        "export_truncated",
        "missing_video",
        "missing_audio",
        "invalid_duration",
        "invalid_resolution",
        "export_verification_failed",
        "export_path_inaccessible",
        "destination_not_created",
        "placeholder_assets_remain",
        "implausible_bitrate",
        "duration_mismatch",
        "incomplete_ffmpeg_output",
        "stale_cloud_path",
    }
)

# Animation / content hard fails (video may exist but must not ship as SUCCESS)
HARD_CONTENT_FAILURES = frozenset(
    {
        "animation_qc_failed",
        "lipsync_below_foundation_floor",
        "animation_below_foundation_floor",
        "overlapping_text",
        "duplicate_text",
        "clipped_text",
        "presenter_covers_content",
        "visual_readability_below_95",
        "annotations_missing_semantic_targets",
        "annotations_missing_teaching_purpose",
        "annotation_clutter_arrow",
        "annotation_clutter_circle",
        "annotation_clutter_highlight",
        "annotation_clutter_label",
        "annotation_clutter_total",
        "no_reality_images",
        "real_photos_available_but_unused",
        "ai_imagery_used_when_real_photos_available",
        "synthetic_visuals_preferred_over_authentic",
        "planned_reality_image_unused",
    }
)

# Missing optional reports / soft score misses — never sole cause of FAILED when MP4 is valid
WARNING_ONLY_CONDITIONS = frozenset(
    {
        "animation_qc_missing",
        "missing_animation_qc",
        "whiteboard_sync_metadata_missing",
        "no_equation_board_action",
        "equation_outside_write_beat",
        "equation_write_overlap_too_small",
        "export_too_small",  # legacy raw-size gate — demoted when file verifies
        "technical_validity_below_threshold",
        "educational_clarity_below_threshold",
        "factual_accuracy_below_threshold",
        "hook_quality_below_threshold",
        "ending_quality_below_threshold",
        "story_structure_below_threshold",
        "overall_below_target",
        "manifest_path_null_recovered",
        "qc_report_regenerated",
        "no_board_write_actions",
        "keyword_write_outside_write_beat",
        "tray_schedule_conflict",
        "unresolved_annotation",
        "visual_layout_qc_error",
    }
)


def _normalize_reasons(reasons: list[str] | None) -> list[str]:
    out: list[str] = []
    for raw in reasons or []:
        text = str(raw or "").strip()
        if not text:
            continue
        # Strip numeric suffixes like overall_below_target:77.4<78.0
        key = text.split(":", 1)[0]
        out.append(text if text in WARNING_ONLY_CONDITIONS or text in HARD_EXPORT_FAILURES else text)
        _ = key  # key used by classifiers below
    return out


def _reason_key(reason: str) -> str:
    return str(reason or "").split(":", 1)[0].strip()


def is_hard_fail_reason(reason: str, *, export_verified: bool = False) -> bool:
    """Return True when a reason must force FAILED.

    Warning-only conditions are demoted even if a caller listed them under hard_fails.
    Unknown reasons default to hard fail (caller intent) unless demoted above.
    """
    key = _reason_key(reason)
    if key in WARNING_ONLY_CONDITIONS:
        return False
    if key.startswith("overall_below_target"):
        return False
    if key.endswith("_below_threshold"):
        if key in (
            "lipsync_below_foundation_floor",
            "animation_below_foundation_floor",
        ):
            return True
        # Soft dimension thresholds — warnings when export verifies
        if export_verified:
            return False
        return False
    if key in HARD_EXPORT_FAILURES:
        return True
    if any(key.startswith(h) or key == h for h in HARD_CONTENT_FAILURES):
        return True
    if key.startswith("lipsync_below_foundation_floor"):
        return True
    if key.startswith("animation_below_foundation_floor"):
        return True
    if key.startswith("idle_ratio_out_of_range"):
        return True
    if key.startswith("walk_ratio_too_high"):
        return True
    if key in (
        "wave_gesture_forbidden",
        "mouth_does_not_vary",
        "speech_mouth_missing",
        "silence_mouth_not_closed",
        "missing_animation_qc",
        "reality_qc_failed",
    ):
        # missing_animation_qc stays hard only when export is NOT verified
        if key == "missing_animation_qc" and export_verified:
            return False
        return True
    # Preserve caller intent for other explicit hard fails
    return True


def classify_reasons(
    hard_fails: list[str] | None,
    warnings: list[str] | None,
    *,
    export_verified: bool,
) -> tuple[list[str], list[str]]:
    """Split mixed reason lists into true hard fails vs warnings."""
    true_hard: list[str] = []
    soft: list[str] = list(warnings or [])
    for reason in hard_fails or []:
        if is_hard_fail_reason(reason, export_verified=export_verified):
            if reason not in true_hard:
                true_hard.append(reason)
        else:
            if reason not in soft:
                soft.append(reason)
    return true_hard, soft


def assign_final_status(
    *,
    export_verified: bool,
    export_path: str | Path | None = None,
    hard_fails: list[str] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Assign SUCCESS / SUCCESS_WITH_WARNINGS / FAILED from physical export + QC."""
    path = Path(str(export_path)) if export_path else None
    path_exists = bool(path and path.is_file() and path.stat().st_size > 0)

    true_hard, soft = classify_reasons(
        hard_fails, warnings, export_verified=export_verified and path_exists
    )

    if not export_verified or not path_exists or true_hard:
        status = FinalStatus.FAILED
    elif soft:
        status = FinalStatus.SUCCESS_WITH_WARNINGS
    else:
        status = FinalStatus.SUCCESS

    publishing = {
        FinalStatus.SUCCESS: "ready_for_review",
        FinalStatus.SUCCESS_WITH_WARNINGS: "ready_for_review",
        FinalStatus.FAILED: "qc_failed",
    }[status]

    return {
        "final_status": status.value,
        "ok": status != FinalStatus.FAILED,
        "export_verified": bool(export_verified and path_exists),
        "export_path": str(path.resolve()) if path_exists and path else (str(export_path or "") or None),
        "hard_fails": true_hard,
        "warnings": soft,
        "publishing_status": publishing,
        "local_render_status": "verified" if status != FinalStatus.FAILED else "failed",
    }


def format_bytes(num: int | float | None) -> str:
    n = float(num or 0)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f} MB"
    if n >= 1_000:
        return f"{n / 1_000:.1f} KB"
    return f"{int(n)} B"


def format_completion_block(
    *,
    final_status: str,
    export_path: str | Path | None,
    probe: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    hard_fails: list[str] | None = None,
    qc_label: str | None = None,
) -> str:
    """Concise terminal completion block for every production run."""
    probe = probe or {}
    path = Path(str(export_path)) if export_path else None
    size = probe.get("bytes")
    if size is None and path and path.is_file():
        size = path.stat().st_size
    duration = probe.get("duration_sec")
    vcodec = probe.get("video_codec") or "?"
    acodec = probe.get("audio_codec") or "?"
    width = probe.get("width")
    height = probe.get("height")
    res = f"{width}x{height}" if width and height else "?"

    if qc_label is None:
        if hard_fails:
            qc_label = "Failed"
        elif warnings:
            qc_label = "Passed with warnings"
        else:
            qc_label = "Passed"

    lines = [
        f"STATUS: {final_status}",
        "",
        "FINAL FILE:",
        f" {path.resolve() if path and path.exists() else (export_path or '(none)')}",
        "",
        "FILE SIZE:",
        f" {format_bytes(size)}",
        "",
        "DURATION:",
        f" {duration} seconds" if duration is not None else " unknown",
        "",
        "VIDEO:",
        f" {vcodec.upper() if isinstance(vcodec, str) else vcodec}, {res}",
        "",
        "AUDIO:",
        f" {acodec.upper() if isinstance(acodec, str) else acodec}",
        "",
        "QC:",
        f" {qc_label}",
        "",
        "FINDER:",
        " Available locally" if path and path.is_file() else " Not available",
    ]
    if warnings:
        lines.extend(["", "WARNINGS:"])
        for w in warnings:
            lines.append(f" - {w}")
    if hard_fails and final_status == FinalStatus.FAILED.value:
        lines.extend(["", "HARD FAILS:"])
        for h in hard_fails:
            lines.append(f" - {h}")
    return "\n".join(lines)


def print_completion_block(**kwargs: Any) -> str:
    block = format_completion_block(**kwargs)
    print(block, flush=True)
    return block
