"""Production database — lightweight JSON index for thousands of productions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.env import project_root

DB_PATH = project_root() / "data" / "generational_os" / "productions" / "index.json"


def _load_db() -> dict[str, Any]:
    if not DB_PATH.is_file():
        return {"schema_version": 1, "updated_at": "", "productions": {}}
    return json.loads(DB_PATH.read_text(encoding="utf-8"))


def _save_db(db: dict[str, Any]) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db["updated_at"] = datetime.now(timezone.utc).isoformat()
    DB_PATH.write_text(json.dumps(db, indent=2), encoding="utf-8")


def upsert_production(project_id: str, record: dict[str, Any]) -> None:
    db = _load_db()
    productions = db.setdefault("productions", {})
    existing = productions.get(project_id) or {}
    existing.update(record)
    existing["project_id"] = project_id
    existing["updated_at"] = datetime.now(timezone.utc).isoformat()
    productions[project_id] = existing
    _save_db(db)


def get_production(project_id: str) -> dict[str, Any] | None:
    db = _load_db()
    return (db.get("productions") or {}).get(project_id)


def list_productions(*, status: str | None = None) -> list[dict[str, Any]]:
    db = _load_db()
    rows = list((db.get("productions") or {}).values())
    if status:
        rows = [r for r in rows if r.get("publishing_status") == status or r.get("local_render_status") == status]
    return sorted(rows, key=lambda r: r.get("updated_at") or "", reverse=True)


def update_from_manifest(manifest_dict: dict[str, Any]) -> None:
    pid = str(manifest_dict.get("project_id") or "")
    if not pid:
        return
    upsert_production(
        pid,
        {
            "title": manifest_dict.get("subject") or pid,
            "series": manifest_dict.get("series"),
            "domain": manifest_dict.get("domain"),
            "pipeline_stage": manifest_dict.get("pipeline_stage"),
            "publishing_status": manifest_dict.get("publishing_status"),
            "local_render_status": manifest_dict.get("local_render_status"),
            "export_path": manifest_dict.get("export_path"),
            "qc_score": manifest_dict.get("qc_score"),
            "manifest_path": str(
                project_root() / "data" / "generational_os" / "productions" / pid / "PRODUCTION_MANIFEST.json"
            ),
        },
    )
