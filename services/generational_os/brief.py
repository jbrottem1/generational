"""Layer 1 output — PRODUCTION_BRIEF.json."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.env import project_root
from services.generational_os.export_classifier import classify_domain
from services.generational_os.layers import ExecutionLayer
from services.generational_os.manifest import ProductionManifest, save_manifest


def build_production_brief(
    *,
    project_id: str,
    title: str,
    subject: str,
    hook: str,
    takeaway: str,
    main_concept: str,
    educational_objective: str,
    target_audience: str = "curious learners 13–35",
    platform: str = "youtube_shorts",
    series: str = "",
    episode: str = "",
    domain: str = "",
    sources: list[str] | None = None,
    seo_keywords: list[str] | None = None,
    retention_notes: list[str] | None = None,
    target_duration_sec: dict[str, float] | None = None,
    thumbnail_plan: str = "",
    scientific_verified: bool = True,
) -> dict[str, Any]:
    folder = classify_domain(subject=subject, series=series, domain=domain, filename=title)
    return {
        "schema_version": 1,
        "layer": ExecutionLayer.INTELLIGENCE.value,
        "project_id": project_id,
        "title": title,
        "series": series,
        "episode": episode,
        "subject": subject,
        "domain": folder,
        "hook": hook,
        "takeaway": takeaway,
        "main_concept": main_concept,
        "educational_objective": educational_objective,
        "target_audience": target_audience,
        "platform": platform,
        "scientific_sources": sources or [],
        "scientific_verified": scientific_verified,
        "seo_keywords": seo_keywords or [],
        "retention_notes": retention_notes or [],
        "target_duration_sec": target_duration_sec or {"min": 15, "max": 32},
        "thumbnail_plan": thumbnail_plan,
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "next_handoff": "pre_production → RENDER_PACKAGE.json",
    }


def write_production_brief(brief: dict[str, Any], path: Path | None = None) -> Path:
    pid = str(brief.get("project_id") or "unknown")
    out = path or (project_root() / "data" / "generational_os" / "productions" / pid / "PRODUCTION_BRIEF.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(brief, indent=2), encoding="utf-8")

    manifest = ProductionManifest(
        project_id=pid,
        series=str(brief.get("series") or ""),
        episode=str(brief.get("episode") or ""),
        subject=str(brief.get("subject") or ""),
        domain=str(brief.get("domain") or "Miscellaneous"),
        scientific_sources=list(brief.get("scientific_sources") or []),
        educational_objective=str(brief.get("educational_objective") or ""),
        target_audience=str(brief.get("target_audience") or ""),
        platform=str(brief.get("platform") or ""),
        target_duration_sec=dict(brief.get("target_duration_sec") or {}),
        hook=str(brief.get("hook") or ""),
        pipeline_stage="research",
        layer="intelligence",
        brief_path=str(out),
    )
    save_manifest(manifest)
    return out
