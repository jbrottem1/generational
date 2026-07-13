"""LOCAL_RENDER_JOB.json — cloud prepares, local executes."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.env import project_root
from services.media_production.execution_mode import (
    ExecutionMode,
    canonical_export_dir,
    cloud_status_message,
    get_execution_context,
)
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
        "fetch_url": f"https://commons.wikimedia.org/wiki/Special:FilePath/{Path(entry.path).name}?width=900",
    }


def build_render_job(
    *,
    job_id: str,
    title: str,
    demo_id: str,
    filename: str,
    hook: str,
    takeaway: str,
    main_concept: str,
    beats: list[dict[str, Any]],
    sources: list[str] | None = None,
    narration: dict[str, Any] | None = None,
    render: dict[str, Any] | None = None,
    animations: dict[str, Any] | None = None,
    transitions: list[dict[str, Any]] | None = None,
    image_ids: list[str] | None = None,
    local_command: str | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Build a portable render job package for local execution."""
    ctx = get_execution_context()
    export_dir = canonical_export_dir()
    ids = image_ids or []
    for panel in plan_reality_beats(demo_id):
        ids.extend(panel.image_ids)
    ids = list(dict.fromkeys(ids))

    timing = {
        "beats": beats,
        "target_duration_sec": {"min": 15, "max": 32},
        "fps": (render or {}).get("fps", 24),
    }

    assets = {
        "images": [_image_asset_entry(i) for i in ids],
        "catalog_root": str(project_root() / "data" / "reality"),
        "cache_root": str(project_root() / "data" / "local_cache"),
    }

    job = {
        "schema_version": 2,
        "job_id": job_id,
        "title": title,
        "status": "awaiting_local_render",
        "message": cloud_status_message(),
        "execution_mode": ExecutionMode.CLOUD.value,
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "prepared_on": {
            "platform": ctx.platform,
            "home": ctx.home,
        },
        "script": {
            "hook": hook,
            "takeaway": takeaway,
            "main_concept": main_concept,
            "beats": beats,
            "sources": sources or [],
        },
        "timing": timing,
        "assets": assets,
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
        "transitions": transitions or [],
        "export": {
            "filename": filename,
            "directory": str(export_dir),
            "directory_expanded": str(export_dir.expanduser()),
            "verify": [
                "file_exists",
                "size_gt_zero",
                "video_stream",
                "audio_stream",
                "playable",
                "duration",
                "resolution",
            ],
        },
        "local_command": local_command
        or f"python3 scripts/run_local_render_job.py --job {output_path or 'LOCAL_RENDER_JOB.json'}",
    }
    return job


def write_render_job(job: dict[str, Any], path: Path | None = None) -> Path:
    """Write LOCAL_RENDER_JOB.json (or episode-specific job file)."""
    out = path or (project_root() / "LOCAL_RENDER_JOB.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(job, indent=2), encoding="utf-8")
    return out


def load_render_job(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
