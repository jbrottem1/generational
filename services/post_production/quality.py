"""Quality control — detect broken cuts, sync errors, caption overlap, audio clipping."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.post_production.config import PostProductionConfig


def validate_post_production(
    package: dict,
    render_package: dict | None = None,
) -> dict:
    """Run QC checks on the post-production package. Never raises."""
    issues = []
    checks_passed = 0
    checks_failed = 0

    render_package = render_package or {}

    # Check 1: Timeline has segments.
    timeline = package.get("edit_timeline") or {}
    tracks = timeline.get("tracks") or []
    video_track = next((t for t in tracks if t.get("track_type") == "video"), None)
    if video_track and video_track.get("clips"):
        checks_passed += 1
    else:
        checks_failed += 1
        issues.append(_issue("error", "timing", "No video clips in edit timeline"))

    # Check 2: Scene cuts are valid (edited_end > edited_start).
    for cut in package.get("scene_cuts") or []:
        if cut.get("edited_end", 0) <= cut.get("edited_start", 0):
            checks_failed += 1
            issues.append(_issue(
                "error", "cut",
                f"Invalid cut for scene {cut.get('scene_id')}: end <= start",
                scene_id=cut.get("scene_id"),
            ))
        else:
            checks_passed += 1

    # Check 3: Caption overlap detection.
    entries = (package.get("caption_timeline") or {}).get("entries") or []
    for i, entry in enumerate(entries):
        for other in entries[i + 1:]:
            if _overlaps(entry, other):
                checks_failed += 1
                issues.append(_issue(
                    "warning", "caption",
                    f"Caption overlap: '{entry.get('text', '')[:30]}' and '{other.get('text', '')[:30]}'",
                    time=entry.get("start_time"),
                ))
            else:
                checks_passed += 1

    # Check 4: Audio mix loudness target present.
    audio = package.get("audio_mix") or {}
    if audio.get("loudness_target"):
        checks_passed += 1
    else:
        checks_failed += 1
        issues.append(_issue("warning", "audio", "Missing loudness target in audio mix"))

    # Check 5: Missing assets from render validation.
    render_validation = render_package.get("validation") or {}
    for problem in render_validation.get("problems") or []:
        checks_failed += 1
        issues.append(_issue("warning", "asset", str(problem)))

    # Check 6: Duplicate clips.
    if video_track:
        clip_ids = [c.get("clip_id") for c in video_track.get("clips", [])]
        if len(clip_ids) != len(set(clip_ids)):
            checks_failed += 1
            issues.append(_issue("warning", "timing", "Duplicate clip IDs detected"))
        else:
            checks_passed += 1

    # Check 7: Black frame detection (zero-duration clips).
    if video_track:
        for clip in video_track.get("clips", []):
            if clip.get("duration", 0) <= 0:
                checks_failed += 1
                issues.append(_issue(
                    "error", "timing",
                    f"Zero-duration clip: {clip.get('clip_id')}",
                    time=clip.get("start_time"),
                ))
            else:
                checks_passed += 1

    # Check 8: Sync — total duration consistency.
    total = float(timeline.get("total_duration_sec") or 0.0)
    render_total = float((render_package.get("timeline") or {}).get("total_duration_sec") or 0.0)
    if render_total > 0 and abs(total - render_total) > 5.0:
        checks_failed += 1
        issues.append(_issue(
            "warning", "sync",
            f"Duration mismatch: edit={total:.1f}s vs render={render_total:.1f}s",
        ))
    elif render_total > 0:
        checks_passed += 1

    errors = sum(1 for i in issues if i["severity"] == "error")
    score = max(0, 100 - errors * 20 - (checks_failed - errors) * 5)
    ready = errors == 0 and score >= 60

    return {
        "status": "pass" if ready else ("warning" if errors == 0 else "fail"),
        "score": score,
        "issues": issues,
        "checks_passed": checks_passed,
        "checks_failed": checks_failed,
        "ready_for_export": ready,
    }


def package_readiness(quality_report: dict) -> dict:
    """Map quality report to package readiness status."""
    score = int(quality_report.get("score", 0))
    ready = quality_report.get("ready_for_export", False)
    errors = sum(1 for i in quality_report.get("issues", []) if i.get("severity") == "error")

    if ready and score >= 80:
        status = "ready"
    elif errors == 0 and score >= 50:
        status = "needs_review"
    else:
        status = "incomplete"

    return {"status": status, "score": score}


def _issue(severity: str, category: str, message: str, time: float = 0.0, scene_id: int = 0) -> dict:
    return {
        "issue_id": uuid.uuid4().hex[:8],
        "severity": severity,
        "category": category,
        "message": message,
        "time": time,
        "scene_id": scene_id,
    }


def _overlaps(a: dict, b: dict) -> bool:
    a_start = float(a.get("start_time", 0))
    a_end = float(a.get("end_time", 0))
    b_start = float(b.get("start_time", 0))
    b_end = float(b.get("end_time", 0))
    return a_start < b_end and b_start < a_end
