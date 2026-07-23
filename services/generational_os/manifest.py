"""Production manifest — permanent trace from idea to publish."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.env import project_root


@dataclass
class ProductionManifest:
    """Permanent production record."""

    project_id: str
    series: str = ""
    episode: str = ""
    subject: str = ""
    domain: str = "Miscellaneous"
    scientific_sources: list[str] = field(default_factory=list)
    educational_objective: str = ""
    target_audience: str = "general educational Shorts"
    platform: str = "youtube_shorts"
    target_duration_sec: dict[str, float] = field(default_factory=lambda: {"min": 15, "max": 35})
    hook: str = ""
    script_version: str = "1.0"
    animation_version: str = "foundation_v2"
    character_version: str = "CHAR-PROFESSOR-V2-001"
    asset_registry: list[str] = field(default_factory=list)
    audio_version: str = ""
    title: str = ""
    topic: str = ""
    export_path: str = ""
    export_domain_folder: str = ""
    library_filename: str = ""
    secondary_categories: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    file_hash: str = ""
    companion_path: str = ""
    qc_score: float | None = None
    render_duration_sec: float | None = None
    publishing_status: str = "draft"
    pipeline_stage: str = "idea"
    layer: str = "intelligence"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    brief_path: str = ""
    render_package_path: str = ""
    local_render_status: str = "pending"
    final_status: str = "PENDING"
    verification: dict[str, Any] = field(default_factory=dict)

    def touch(self, **updates: Any) -> None:
        for key, val in updates.items():
            if hasattr(self, key):
                setattr(self, key, val)
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def manifest_dir(project_id: str) -> Path:
    return project_root() / "data" / "generational_os" / "productions" / project_id


def manifest_path(project_id: str) -> Path:
    return manifest_dir(project_id) / "PRODUCTION_MANIFEST.json"


def load_manifest(project_id: str) -> ProductionManifest | None:
    path = manifest_path(project_id)
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return ProductionManifest(**{k: v for k, v in data.items() if k in ProductionManifest.__dataclass_fields__})


def save_manifest(manifest: ProductionManifest) -> Path:
    path = manifest_path(manifest.project_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")
    return path


def update_manifest_from_export(
    project_id: str,
    *,
    export_path: Path,
    domain_folder: str,
    verification: dict[str, Any],
    qc_score: float | None = None,
    render_duration_sec: float | None = None,
    title: str = "",
    topic: str = "",
    secondary_categories: list[str] | None = None,
    keywords: list[str] | None = None,
    file_hash: str = "",
    companion_path: str = "",
    library_filename: str = "",
    final_status: str | None = None,
    publishing_status: str | None = None,
    local_render_status: str | None = None,
) -> ProductionManifest:
    manifest = load_manifest(project_id) or ProductionManifest(project_id=project_id)
    absolute = str(Path(export_path).resolve())
    verified_ok = bool(verification.get("ok"))
    resolved_final = final_status or (
        "SUCCESS" if verified_ok else "FAILED"
    )
    resolved_publishing = publishing_status or (
        "ready_for_review" if verified_ok else "qc_failed"
    )
    resolved_local = local_render_status or (
        "verified" if verified_ok else "failed"
    )
    manifest.touch(
        title=title or manifest.title or manifest.subject,
        topic=topic or manifest.topic or manifest.subject,
        export_path=absolute,
        export_domain_folder=domain_folder,
        library_filename=library_filename,
        secondary_categories=list(secondary_categories or []),
        keywords=list(keywords or manifest.keywords or []),
        file_hash=file_hash,
        companion_path=companion_path,
        verification=verification,
        qc_score=qc_score,
        render_duration_sec=render_duration_sec,
        pipeline_stage="export",
        layer="local_production",
        local_render_status=resolved_local,
        publishing_status=resolved_publishing,
        final_status=resolved_final,
    )
    save_manifest(manifest)
    return manifest
