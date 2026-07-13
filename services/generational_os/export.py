"""Layer 3 verified export — permanent media library + manifest + DB."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from services.generational_os.database import update_from_manifest, upsert_production
from services.generational_os.manifest import load_manifest, update_manifest_from_export
from services.generational_os.media_library import (
    build_library_filename,
    category_dir,
    classify_production,
    companion_dir_for,
    file_sha256,
    find_duplicate,
    register_library_entry,
    versioned_export_path,
    write_companion_files,
)
from services.media_production.execution_mode import get_execution_context
from services.media_production.verified_export import ffprobe_mp4, reveal_export_in_finder


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
) -> dict[str, Any]:
    """Export to ~/Desktop/AI Start-Up/Videos/{Category}/ with companions + index."""
    ctx = get_execution_context()
    if not ctx.can_render_media:
        return {
            "ok": False,
            "status": "awaiting_local_render",
            "message": "Cloud runtime cannot claim local Desktop export.",
        }

    if not source.is_file():
        return {"ok": False, "error": f"source missing: {source}"}

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
            return {
                "ok": True,
                "status": "export_verified",
                "export_path": str(existing),
                "domain_folder": category,
                "deduplicated": True,
                "verification": {
                    "ok": True,
                    "checks": {"duplicate_reused": True},
                    "probe": probe,
                    "path": str(existing.resolve()),
                    "domain_folder": category,
                },
            }

    dest_dir = category_dir(category, create=True)
    dest, versioned = versioned_export_path(dest_dir, library_filename, file_hash=file_hash)
    shutil.copy2(source, dest)
    probe = ffprobe_mp4(dest)
    checks = {
        "file_exists": dest.is_file(),
        "size_gt_zero": dest.stat().st_size > 0,
        "video_stream": bool(probe.get("has_video")),
        "audio_stream": bool(probe.get("has_audio")),
        "playable": bool(probe.get("ok")),
        "duration": float(probe.get("duration_sec") or 0) > 0.5,
        "resolution": bool(probe.get("width") and probe.get("height")),
        "correct_category_folder": dest.parent.name == category,
        "companion_files": False,
        "library_index_updated": False,
        "manifest_updated": False,
        "local_execution": ctx.can_claim_export_success,
    }

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
            "export_path": str(dest),
        },
        production_report_md=f"# Production Report — {resolved_title}\n\n- Category: {category}\n- QC: {qc_score}\n",
        render_manifest=render_manifest or {"project_id": project_id, "demo_id": demo_id},
    )
    checks["companion_files"] = all(Path(p).exists() for p in companion_paths.values())

    verification = {
        "ok": all(checks.values()),
        "checks": checks,
        "probe": probe,
        "path": str(dest.resolve()),
        "domain_folder": category,
        "category": category,
        "secondary_categories": secondary,
        "versioned": versioned,
        "companion_dir": str(companion_dir),
    }

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
    )
    checks["manifest_updated"] = True

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
        "created_at": manifest_obj.created_at,
        "file_path": str(dest.resolve()),
        "companion_path": str(companion_dir),
        "thumbnail": companion_paths.get("thumbnail", ""),
        "qc_score": qc_score,
        "publishing_status": manifest_obj.publishing_status,
        "platform": platform,
        "character": character,
        "file_hash": file_hash,
        "demo_id": demo_id,
    }
    register_library_entry(library_entry)
    checks["library_index_updated"] = True
    verification["checks"] = checks
    verification["ok"] = all(checks.values())

    update_from_manifest(manifest_obj.to_dict())
    upsert_production(
        project_id,
        {
            "export_path": str(dest),
            "domain": category,
            "local_render_status": "verified" if verification["ok"] else "failed",
            "publishing_status": manifest_obj.publishing_status,
            "qc_score": qc_score,
        },
    )

    if reveal_finder and verification["ok"]:
        reveal_export_in_finder(dest)

    return {
        "ok": verification["ok"],
        "status": "export_verified" if verification["ok"] else "verification_failed",
        "export_path": str(dest),
        "domain_folder": category,
        "category": category,
        "secondary_categories": secondary,
        "library_filename": library_filename,
        "companion_dir": str(companion_dir),
        "file_hash": file_hash,
        "versioned": versioned,
        "verification": verification,
        "manifest_path": str(manifest_obj.to_dict().get("export_path")),
    }
