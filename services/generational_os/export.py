"""Layer 3 verified export — classified Desktop path + manifest + DB."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from services.generational_os.database import update_from_manifest, upsert_production
from services.generational_os.export_classifier import classified_export_dir, classify_domain, unique_path
from services.generational_os.manifest import update_manifest_from_export
from services.media_production.execution_mode import get_execution_context
from services.media_production.verified_export import ffprobe_mp4, reveal_export_in_finder


def export_verified_production(
    source: Path,
    *,
    project_id: str,
    filename: str,
    domain: str = "",
    subject: str = "",
    series: str = "",
    demo_id: str = "",
    qc_score: float | None = None,
    render_duration_sec: float | None = None,
    reveal_finder: bool = True,
) -> dict[str, Any]:
    """Copy to ~/Desktop/AI Start-up/Generational/Videos/{Domain}/ and verify all checks."""
    ctx = get_execution_context()
    if not ctx.can_render_media:
        return {
            "ok": False,
            "status": "awaiting_local_render",
            "message": "Cloud runtime cannot claim local Desktop export.",
        }

    folder = classify_domain(
        domain=domain,
        subject=subject,
        series=series,
        filename=filename,
        demo_id=demo_id,
    )
    dest_dir = classified_export_dir(domain=folder, create=True)
    dest = unique_path(dest_dir, filename)

    if not source.is_file():
        return {"ok": False, "error": f"source missing: {source}"}

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
        "correct_domain_folder": dest.parent.name == folder,
        "local_execution": ctx.can_claim_export_success,
    }
    verification = {
        "ok": all(checks.values()),
        "checks": checks,
        "probe": probe,
        "path": str(dest.resolve()),
        "domain_folder": folder,
    }

    manifest = update_manifest_from_export(
        project_id,
        export_path=dest,
        domain_folder=folder,
        verification=verification,
        qc_score=qc_score,
        render_duration_sec=render_duration_sec,
    )
    update_from_manifest(manifest.to_dict())
    upsert_production(
        project_id,
        {
            "export_path": str(dest),
            "domain": folder,
            "local_render_status": "verified" if verification["ok"] else "failed",
            "publishing_status": manifest.publishing_status,
            "qc_score": qc_score,
        },
    )

    if reveal_finder and verification["ok"]:
        reveal_export_in_finder(dest)

    return {
        "ok": verification["ok"],
        "status": "export_verified" if verification["ok"] else "verification_failed",
        "export_path": str(dest),
        "domain_folder": folder,
        "verification": verification,
        "manifest_path": str(manifest.to_dict().get("export_path")),
    }
