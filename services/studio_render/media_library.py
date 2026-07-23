"""Module 12 — Media Library project folders (reproducible productions)."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.studio_render.models import MEDIA_LIBRARY_V3_PARTS, PROJECT_SUBFOLDERS


def media_library_root(*, create: bool = False) -> Path:
    root = Path.home().joinpath(*MEDIA_LIBRARY_V3_PARTS)
    if create:
        root.mkdir(parents=True, exist_ok=True)
    return root


def _slug(text: str, *, fallback: str = "project") -> str:
    cleaned = re.sub(r"[^\w\s-]", "", text or "").strip()
    cleaned = re.sub(r"[\s_-]+", "_", cleaned)
    return (cleaned[:60] or fallback).strip("_")


def topic_dir(topic: str, *, create: bool = False) -> Path:
    path = media_library_root(create=create) / _slug(topic, fallback="General")
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_project_tree(
    topic: str,
    project_name: str,
    *,
    create: bool = True,
) -> Path:
    """Create Topic/Project/{Scripts,Voice,...,Archive}/ tree."""
    project = topic_dir(topic, create=create) / _slug(project_name)
    if create:
        project.mkdir(parents=True, exist_ok=True)
        for sub in PROJECT_SUBFOLDERS:
            (project / sub).mkdir(parents=True, exist_ok=True)
    return project


def write_studio_project(
    candidate: dict,
    package: dict,
    *,
    create: bool = True,
) -> dict[str, Any]:
    """Persist editable/reproducible studio package into Media Library V3 tree."""
    topic = str(candidate.get("topic") or candidate.get("category") or candidate.get("title") or "General")
    project_name = str(
        candidate.get("project_id")
        or candidate.get("id")
        or candidate.get("title")
        or "studio_render"
    )
    root = ensure_project_tree(topic, project_name, create=create)

    # Timeline
    timeline_path = root / "Timeline" / "master_timeline.json"
    timeline_path.write_text(json.dumps(package.get("master_timeline") or {}, indent=2), encoding="utf-8")

    # Reports
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": package.get("version") or "3.0.0",
        "overall_score": package.get("overall_score"),
        "quality_scores": package.get("quality_scores"),
        "export_plan": package.get("export_plan"),
        "improvements_vs_baseline": package.get("improvements_vs_baseline"),
        "revision_fixes": package.get("revision_fixes"),
    }
    (root / "Reports" / "Studio_Render_Report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    (root / "Reports" / "Studio_Render_Report.md").write_text(
        f"# Studio Render Report\n\nOverall: **{report['overall_score']}**\n\n"
        f"```json\n{json.dumps(report['quality_scores'], indent=2)}\n```\n",
        encoding="utf-8",
    )

    # Assets / plans (editable)
    assets_dir = root / "Assets"
    (assets_dir / "studio_render_package.json").write_text(
        json.dumps(package, indent=2), encoding="utf-8"
    )
    (assets_dir / "motion_graphics.json").write_text(
        json.dumps(package.get("motion_graphics") or [], indent=2), encoding="utf-8"
    )
    (assets_dir / "transitions.json").write_text(
        json.dumps(package.get("transitions") or [], indent=2), encoding="utf-8"
    )
    (root / "Diagrams" / "diagram_plan.json").write_text(
        json.dumps(package.get("diagrams") or [], indent=2), encoding="utf-8"
    )
    (root / "B-Roll" / "broll_plan.json").write_text(
        json.dumps(package.get("broll_plan") or [], indent=2), encoding="utf-8"
    )
    (root / "Animations" / "camera_choreography.json").write_text(
        json.dumps(package.get("camera_choreography") or [], indent=2), encoding="utf-8"
    )

    # Script snapshot
    script_text = str(
        (candidate.get("structured_script") or {}).get("full_script")
        or candidate.get("script")
        or candidate.get("hook")
        or candidate.get("title")
        or ""
    )
    (root / "Scripts" / "script.md").write_text(f"# Script\n\n{script_text}\n", encoding="utf-8")

    # Manifest for reproducibility
    manifest = {
        "topic": topic,
        "project": project_name,
        "path": str(root),
        "subfolders": list(PROJECT_SUBFOLDERS),
        "package_version": package.get("version"),
        "reproducible": True,
    }
    (root / "project_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return {"project_root": str(root), "manifest": manifest}
