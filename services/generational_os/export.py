"""Layer 3 verified export — permanent media library + manifest + DB.

Atomic order:
1. Verify temporary source
2. Copy to canonical destination
3. Wait until destination exists
4. Verify destination (ffprobe)
5. Write companions
6. Update library index
7. Persist manifest with final verification
8. Assign final production status
9. Print verified absolute path
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Any

from services.generational_os.database import update_from_manifest, upsert_production
from services.generational_os.final_status import (
    FinalStatus,
    assign_final_status,
    print_completion_block,
)
from services.generational_os.manifest import load_manifest, save_manifest, update_manifest_from_export
from services.generational_os.media_library import (
    build_library_filename,
    category_dir,
    classify_production,
    companion_dir_for,
    file_sha256,
    find_duplicate,
    library_root,
    register_library_entry,
    versioned_export_path,
    write_companion_files,
)
from services.media_production.execution_mode import get_execution_context
from services.media_production.verified_export import (
    assess_export_technical_validity,
    ffprobe_mp4,
    reveal_export_in_finder,
    wait_for_file,
)


def _resolve_library_filename(
    *,
    filename: str,
    category: str,
    series: str,
    episode: str,
    topic: str,
    title: str,
    subject: str,
) -> str:
    if filename and filename.endswith(".mp4"):
        return filename
    topic_token = topic or title or subject or "Untitled"
    return build_library_filename(
        category=category,
        series=series or "001",
        episode=episode or "001",
        topic=topic_token,
    )


def _media_checks(dest: Path, probe: dict[str, Any], category: str, *, local_ok: bool) -> dict[str, bool]:
    tech = assess_export_technical_validity(dest, probe=probe)
    return {
        "file_exists": dest.is_file(),
        "size_gt_zero": dest.is_file() and dest.stat().st_size > 0,
        "video_stream": bool(probe.get("has_video")),
        "audio_stream": bool(probe.get("has_audio")),
        "playable": bool(probe.get("ok")),
        "duration": float(probe.get("duration_sec") or 0) > 0.5,
        "resolution": bool(probe.get("width") and probe.get("height")),
        "correct_category_folder": dest.parent.name == category,
        "under_library_root": str(dest.resolve()).startswith(str(library_root().resolve())),
        "not_placeholder": not bool(tech.get("is_placeholder")),
        "technical_valid": bool(tech.get("ok")),
        "local_execution": local_ok,
    }


def _copy_with_retry(source: Path, dest: Path, *, attempts: int = 3) -> Path:
    last_err: Exception | None = None
    for i in range(attempts):
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            if wait_for_file(dest):
                return dest
        except OSError as exc:  # noqa: PERF203
            last_err = exc
            time.sleep(0.05 * (i + 1))
    if last_err:
        raise last_err
    raise OSError(f"failed to copy export to {dest}")


def export_verified_production(
    source: Path,
    *,
    project_id: str,
    filename: str = "",
    domain: str = "",
    subject: str = "",
    title: str = "",
    series: str = "",
    episode: str = "",
    topic: str = "",
    demo_id: str = "",
    keywords: list[str] | None = None,
    sources: list[str] | None = None,
    script_md: str = "",
    qc_score: float | None = None,
    render_duration_sec: float | None = None,
    platform: str = "youtube_shorts",
    character: str = "Professor Gen",
    reveal_finder: bool = True,
    render_manifest: dict[str, Any] | None = None,
    qc_warnings: list[str] | None = None,
    qc_hard_fails: list[str] | None = None,
    print_completion: bool = True,
) -> dict[str, Any]:
    """Export to ~/Desktop/AI Start-Up/Videos/{Category}/ with companions + index."""
    ctx = get_execution_context()
    if not ctx.can_claim_export_success:
        return {
            "ok": False,
            "final_status": FinalStatus.FAILED.value,
            "status": "export_root_unreachable",
            "message": "Desktop media library is unreachable. Expected ~/Desktop/AI Start-Up/Videos/.",
            "export_path": None,
        }

    source = Path(source)
    if not source.is_file():
        return {
            "ok": False,
            "final_status": FinalStatus.FAILED.value,
            "error": f"source missing: {source}",
            "export_path": None,
        }

    # 1. Verify temporary source before promoting to library
    source_probe = ffprobe_mp4(source)
    source_tech = assess_export_technical_validity(source, probe=source_probe)
    if not source_tech.get("ok"):
        return {
            "ok": False,
            "final_status": FinalStatus.FAILED.value,
            "status": "source_verification_failed",
            "error": "temporary render failed technical verification",
            "source_probe": source_probe,
            "source_hard_fails": source_tech.get("hard_fails") or [],
            "export_path": None,
        }

    manifest = load_manifest(project_id)
    classification = classify_production(
        subject=subject or (manifest.subject if manifest else ""),
        title=title or (manifest.subject if manifest else subject),
        series=series or (manifest.series if manifest else ""),
        filename=filename,
        domain=domain or (manifest.domain if manifest else ""),
        demo_id=demo_id,
        keywords=keywords,
    )
    category = classification["primary"]
    secondary = classification["secondary"]

    resolved_series = series or (manifest.series if manifest else "") or "001"
    resolved_episode = episode or (manifest.episode if manifest else "") or "001"
    resolved_title = title or subject or (manifest.subject if manifest else "") or project_id
    resolved_topic = topic or resolved_title
    resolved_sources = list(sources or (manifest.scientific_sources if manifest else []) or [])
    resolved_keywords = list(keywords or [])

    library_filename = _resolve_library_filename(
        filename=filename,
        category=category,
        series=resolved_series,
        episode=resolved_episode,
        topic=resolved_topic,
        title=resolved_title,
        subject=subject,
    )

    file_hash = file_sha256(source)
    duplicate = find_duplicate(file_hash, project_id=project_id)
    if duplicate and duplicate.get("file_path"):
        existing = Path(str(duplicate["file_path"]))
        if existing.is_file():
            probe = ffprobe_mp4(existing)
            status_info = assign_final_status(
                export_verified=bool(probe.get("ok")),
                export_path=existing,
                hard_fails=qc_hard_fails,
                warnings=qc_warnings,
            )
            if print_completion:
                print_completion_block(
                    final_status=status_info["final_status"],
                    export_path=existing,
                    probe=probe,
                    warnings=status_info["warnings"],
                    hard_fails=status_info["hard_fails"],
                )
            return {
                "ok": status_info["ok"],
                "final_status": status_info["final_status"],
                "status": "export_verified" if status_info["ok"] else "verification_failed",
                "export_path": str(existing.resolve()),
                "domain_folder": category,
                "deduplicated": True,
                "warnings": status_info["warnings"],
                "hard_fails": status_info["hard_fails"],
                "verification": {
                    "ok": bool(probe.get("ok")),
                    "checks": {"duplicate_reused": True},
                    "probe": probe,
                    "path": str(existing.resolve()),
                    "domain_folder": category,
                },
                "completion": format_completion_if_needed(status_info, existing, probe),
            }

    dest_dir = category_dir(category, create=True)
    dest, versioned = versioned_export_path(dest_dir, library_filename, file_hash=file_hash)

    # 2–3. Atomic promote: copy, wait, verify destination
    try:
        _copy_with_retry(source, dest)
    except OSError as exc:
        return {
            "ok": False,
            "final_status": FinalStatus.FAILED.value,
            "status": "destination_not_created",
            "error": str(exc),
            "export_path": None,
            "temp_source": str(source),
        }

    if not wait_for_file(dest):
        return {
            "ok": False,
            "final_status": FinalStatus.FAILED.value,
            "status": "destination_not_created",
            "error": f"final export missing after copy: {dest}",
            "export_path": None,
            "temp_source": str(source),
        }

    # 4. Verify final destination only (never temp) for bookkeeping
    probe = ffprobe_mp4(dest)
    tech = assess_export_technical_validity(dest, probe=probe, expected_duration_sec=render_duration_sec)
    checks = _media_checks(dest, probe, category, local_ok=ctx.can_claim_export_success)
    checks["companion_files"] = False
    checks["library_index_updated"] = False
    checks["manifest_updated"] = False

    media_ok = all(
        checks[k]
        for k in (
            "file_exists",
            "size_gt_zero",
            "video_stream",
            "audio_stream",
            "playable",
            "duration",
            "resolution",
            "correct_category_folder",
            "under_library_root",
            "not_placeholder",
            "technical_valid",
            "local_execution",
        )
    )

    companion_dir = companion_dir_for(dest)
    companion_paths = write_companion_files(
        companion_dir,
        script_md=script_md or f"# {resolved_title}\n\n(TBD)\n",
        sources=resolved_sources,
        metadata={
            "project_id": project_id,
            "title": resolved_title,
            "category": category,
            "secondary_categories": secondary,
            "series": resolved_series,
            "episode": resolved_episode,
            "topic": resolved_topic,
            "keywords": resolved_keywords,
            "platform": platform,
            "character": character,
            "file_hash": file_hash,
            "export_path": str(dest.resolve()),
        },
        production_report_md=f"# Production Report — {resolved_title}\n\n- Category: {category}\n- QC: {qc_score}\n",
        render_manifest=render_manifest or {"project_id": project_id, "demo_id": demo_id},
    )
    checks["companion_files"] = all(Path(p).exists() for p in companion_paths.values())

    export_hard = list(tech.get("hard_fails") or [])
    export_warnings = list(tech.get("warnings") or [])
    if not checks["companion_files"]:
        export_warnings.append("companion_files_incomplete")

    # 5–6. Library index BEFORE final manifest so both bookkeeping flags are true when persisted
    absolute_export = str(dest.resolve())
    library_entry = {
        "project_id": project_id,
        "title": resolved_title,
        "topic": resolved_topic,
        "category": category,
        "secondary_categories": secondary,
        "series": resolved_series,
        "episode": resolved_episode,
        "duration_sec": probe.get("duration_sec"),
        "keywords": resolved_keywords,
        "scientific_sources": resolved_sources,
        "created_at": (manifest.created_at if manifest else None),
        "file_path": absolute_export,
        "companion_path": str(companion_dir),
        "thumbnail": companion_paths.get("thumbnail", ""),
        "qc_score": qc_score,
        "publishing_status": "ready_for_review" if media_ok else "qc_failed",
        "platform": platform,
        "character": character,
        "file_hash": file_hash,
        "demo_id": demo_id,
    }
    register_library_entry(library_entry)
    checks["library_index_updated"] = True

    # Bookkeeping complete — mark before persisting so verification.ok matches reality
    checks["manifest_updated"] = True
    verification = {
        "ok": media_ok and checks["companion_files"] and checks["library_index_updated"] and checks["manifest_updated"],
        "checks": dict(checks),
        "probe": probe,
        "technical": tech,
        "path": absolute_export,
        "domain_folder": category,
        "category": category,
        "secondary_categories": secondary,
        "versioned": versioned,
        "companion_dir": str(companion_dir),
    }

    status_info = assign_final_status(
        export_verified=bool(verification["ok"]),
        export_path=dest,
        hard_fails=(qc_hard_fails or []) + export_hard,
        warnings=(qc_warnings or []) + export_warnings,
    )
    verification["final_status"] = status_info["final_status"]
    verification["warnings"] = status_info["warnings"]
    verification["hard_fails"] = status_info["hard_fails"]

    # 7. Persist manifest with final verification (never a premature failed snapshot)
    manifest_obj = update_manifest_from_export(
        project_id,
        export_path=dest,
        domain_folder=category,
        verification=verification,
        qc_score=qc_score,
        render_duration_sec=render_duration_sec,
        title=resolved_title,
        topic=resolved_topic,
        secondary_categories=secondary,
        keywords=resolved_keywords,
        file_hash=file_hash,
        companion_path=str(companion_dir),
        library_filename=library_filename,
        final_status=status_info["final_status"],
        publishing_status=status_info["publishing_status"],
        local_render_status=status_info["local_render_status"],
    )

    # Keep library publishing_status aligned with final status
    library_entry["publishing_status"] = status_info["publishing_status"]
    library_entry["final_status"] = status_info["final_status"]
    register_library_entry(library_entry)

    update_from_manifest(manifest_obj.to_dict())
    upsert_production(
        project_id,
        {
            "export_path": absolute_export,
            "domain": category,
            "local_render_status": status_info["local_render_status"],
            "publishing_status": status_info["publishing_status"],
            "final_status": status_info["final_status"],
            "qc_score": qc_score,
        },
    )

    # Re-assert absolute path on manifest if anything left it null
    if not manifest_obj.export_path:
        manifest_obj.export_path = absolute_export
        save_manifest(manifest_obj)
        status_info["warnings"] = list(status_info["warnings"]) + ["manifest_path_null_recovered"]
        status_info = assign_final_status(
            export_verified=bool(verification["ok"]),
            export_path=dest,
            hard_fails=status_info["hard_fails"],
            warnings=status_info["warnings"],
        )

    if reveal_finder and status_info["ok"]:
        reveal_export_in_finder(dest)

    completion = ""
    if print_completion:
        completion = print_completion_block(
            final_status=status_info["final_status"],
            export_path=dest,
            probe=probe,
            warnings=status_info["warnings"],
            hard_fails=status_info["hard_fails"],
        )

    return {
        "ok": status_info["ok"],
        "final_status": status_info["final_status"],
        "status": "export_verified" if status_info["ok"] else "verification_failed",
        "export_path": absolute_export,
        "domain_folder": category,
        "category": category,
        "secondary_categories": secondary,
        "library_filename": library_filename,
        "companion_dir": str(companion_dir),
        "file_hash": file_hash,
        "versioned": versioned,
        "verification": verification,
        "warnings": status_info["warnings"],
        "hard_fails": status_info["hard_fails"],
        "publishing_status": status_info["publishing_status"],
        "manifest_path": absolute_export,
        "temp_source": str(source),
        "completion": completion,
    }


def format_completion_if_needed(
    status_info: dict[str, Any],
    path: Path,
    probe: dict[str, Any],
) -> str:
    from services.generational_os.final_status import format_completion_block

    return format_completion_block(
        final_status=status_info["final_status"],
        export_path=path,
        probe=probe,
        warnings=status_info.get("warnings"),
        hard_fails=status_info.get("hard_fails"),
    )
