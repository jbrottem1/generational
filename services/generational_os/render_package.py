"""Layer 2 output — RENDER_PACKAGE.json (successor to LOCAL_RENDER_JOB.json)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.env import project_root
from services.generational_os.export_classifier import classified_export_dir, classify_domain
from services.generational_os.layers import ExecutionLayer
from services.generational_os.manifest import load_manifest, save_manifest
from services.media_production.execution_mode import cloud_status_message, get_execution_context
from services.reality.catalog import get_image
from services.reality.planner import plan_reality_beats


def _image_asset_entry(image_id: str) -> dict[str, Any]:
    entry = get_image(image_id)
    if entry is None:
        return {"image_id": image_id, "missing": True}
    return {
        "image_id": image_id,
        "path": str(entry.path),
        "license": entry.license,
        "source_url": entry.source_url,
        "credit": entry.credit,
        "organism": entry.organism,
    }


def build_render_package(
    *,
    project_id: str,
    title: str,
    demo_id: str,
    filename: str,
    hook: str,
    takeaway: str,
    main_concept: str,
    beats: list[dict[str, Any]],
    domain: str = "",
    subject: str = "",
    series: str = "",
    sources: list[str] | None = None,
    narration: dict[str, Any] | None = None,
    render: dict[str, Any] | None = None,
    animations: dict[str, Any] | None = None,
    choreography: dict[str, Any] | None = None,
    image_ids: list[str] | None = None,
) -> dict[str, Any]:
    ctx = get_execution_context()
    folder = classify_domain(subject=subject, series=series, domain=domain, filename=filename, demo_id=demo_id)
    export_dir = classified_export_dir(domain=folder, create=False)

    ids = list(image_ids or [])
    for panel in plan_reality_beats(demo_id):
        ids.extend(panel.image_ids)
    ids = list(dict.fromkeys(ids))

    return {
        "schema_version": 3,
        "os_version": "2.5",
        "layer": ExecutionLayer.PRE_PRODUCTION.value,
        "project_id": project_id,
        "job_id": project_id,
        "title": title,
        "status": "awaiting_local_render",
        "message": cloud_status_message(),
        "execution_mode": ctx.mode.value,
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "domain": folder,
        "script": {
            "hook": hook,
            "takeaway": takeaway,
            "main_concept": main_concept,
            "beats": beats,
            "sources": sources or [],
        },
        "timing": {
            "beats": beats,
            "target_duration_sec": {"min": 15, "max": 32},
            "fps": int((render or {}).get("fps") or 24),
        },
        "assets": {
            "images": [_image_asset_entry(i) for i in ids],
            "catalog_root": str(project_root() / "data" / "reality"),
            "cache_root": str(project_root() / "data" / "local_cache"),
            "asset_registry_ids": ids,
        },
        "narration": narration
        or {
            "provider": "openai",
            "voice": "nova",
            "model": "tts-1-hd",
            "builder": "services.animation.communicator_delivery.build_paused_narration",
            "smoke_fallback": "services.reality.smoke_narration.build_smoke_narration",
        },
        "animations": animations
        or {
            "demo_id": demo_id,
            "educator_mode": True,
            "renderer": "services.animation.performer.render_lip_sync_performance",
        },
        "choreography": choreography or {"plan_id": demo_id},
        "transitions": [],
        "export": {
            "filename": filename,
            "domain_folder": folder,
            "directory": str(export_dir),
            "directory_expanded": str(export_dir.expanduser()),
            "legacy_directory": str(Path.home() / "Desktop" / "AI Start-up" / "videos" / "Test run 2 generational"),
            "verify": [
                "file_exists",
                "size_gt_zero",
                "video_stream",
                "audio_stream",
                "playable",
                "duration",
                "resolution",
                "manifest_updated",
                "production_db_updated",
            ],
        },
        "local_command": f"python3 scripts/run_render_package.py --package RENDER_PACKAGE.json",
        "handoff": {
            "from_layer": ExecutionLayer.PRE_PRODUCTION.value,
            "to_layer": ExecutionLayer.LOCAL_PRODUCTION.value,
            "owner": "Local Workstation",
        },
    }


def write_render_package(package: dict[str, Any], path: Path | None = None) -> Path:
    pid = str(package.get("project_id") or package.get("job_id") or "unknown")
    out = path or (project_root() / "RENDER_PACKAGE.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(package, indent=2), encoding="utf-8")

    per_project = project_root() / "data" / "generational_os" / "productions" / pid / "RENDER_PACKAGE.json"
    per_project.parent.mkdir(parents=True, exist_ok=True)
    per_project.write_text(json.dumps(package, indent=2), encoding="utf-8")

    manifest = load_manifest(pid)
    if manifest:
        manifest.touch(
            render_package_path=str(out),
            pipeline_stage="render_package",
            layer="pre_production",
            local_render_status="awaiting_local_render",
            asset_registry=list((package.get("assets") or {}).get("asset_registry_ids") or []),
        )
        save_manifest(manifest)
    return out


def load_render_package(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
