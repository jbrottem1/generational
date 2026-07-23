"""Persist VISUAL_PACKAGE.json and soft-attach to candidates."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.visual_asset_director.director import direct_visual_assets, validate_visual_package

ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = ROOT / "data" / "visual_asset_director" / "packages"


def _now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_visual_package(
    candidate: dict[str, Any] | None = None,
    *,
    out_path: str | Path | None = None,
    write: bool = True,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build + optionally write VISUAL_PACKAGE.json."""
    package = direct_visual_assets(candidate, **kwargs)
    package["generated_at"] = datetime.now(timezone.utc).isoformat()
    package["validation"] = validate_visual_package(package)

    if write:
        OUT_ROOT.mkdir(parents=True, exist_ok=True)
        if out_path:
            path = Path(out_path)
        else:
            slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(package.get("topic") or "visual"))[:48]
            path = OUT_ROOT / f"{slug}_{_now_stamp()}_VISUAL_PACKAGE.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        # Canonical filename when directory provided without name
        if path.is_dir():
            path = path / "VISUAL_PACKAGE.json"
        path.write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
        package["path"] = str(path)
    return package


def attach_visual_package_to_candidate(candidate: dict[str, Any], package: dict[str, Any]) -> dict[str, Any]:
    """
    Soft attach — updates scene approved paths inside visual_package without
    overwriting cinematic camera/lighting or world placement fields.
    """
    out = dict(candidate)
    out["visual_asset_direction"] = {
        "path": package.get("path"),
        "style_profile": package.get("style_profile"),
        "visual_scores": package.get("visual_scores"),
        "continuity_score": (package.get("continuity_report") or {}).get("continuity_score"),
        "thumbnail_candidate": package.get("thumbnail_candidate"),
        "validation": package.get("validation"),
        "approved_count": len(package.get("approved_assets") or []),
        "rejected_count": len(package.get("rejected_assets") or []),
    }
    out["visual_asset_package"] = package
    out["VISUAL_PACKAGE"] = package

    vp = dict(out.get("visual_package") or {})
    scenes = list(vp.get("scenes") or out.get("scenes") or [])
    by_id = {
        str(a.get("scene_id")): a
        for a in (package.get("approved_assets") or [])
    }
    manifest = {str(m.get("scene_id")): m for m in (package.get("asset_manifest") or [])}
    for i, scene in enumerate(scenes):
        sid = str(scene.get("scene_id") or scene.get("id") or f"scene_{i:02d}")
        if sid in by_id:
            scene = dict(scene)
            scene["approved_asset_path"] = by_id[sid]["path"]
            scene["image"] = scene.get("image") or by_id[sid]["path"]
            scene["visual_asset_scorecard"] = by_id[sid].get("scorecard")
            scene["visual_asset_approved"] = True
            scene["cinematic_ready"] = True
            scenes[i] = scene
        elif sid in manifest and not manifest[sid].get("approved"):
            scene = dict(scene)
            scene["visual_asset_approved"] = False
            scene["cinematic_ready"] = False
            scenes[i] = scene
    if scenes:
        vp["scenes"] = scenes
        out["visual_package"] = vp

    if package.get("thumbnail_candidate"):
        out.setdefault("thumbnail_candidate", package["thumbnail_candidate"])
        out.setdefault("preferred_thumbnail_path", (package["thumbnail_candidate"] or {}).get("path"))

    # Soft preference flags for existing systems
    out.setdefault("prefer_approved_visual_assets", True)
    out.setdefault("visual_style_profile", (package.get("style_profile") or {}).get("style_key"))
    return out


def score_baseline_vs_directed(
    before_package: dict[str, Any],
    after_package: dict[str, Any],
) -> dict[str, Any]:
    """Compare mean scores before (raw evaluate-all) vs after (director selection)."""
    b = (before_package.get("visual_scores") or {})
    a = (after_package.get("visual_scores") or {})
    keys = [
        "mean_overall_professional_quality",
        "approved_count",
        "approval_rate",
    ]
    deltas = {}
    for k in keys:
        try:
            deltas[k] = round(float(a.get(k) or 0) - float(b.get(k) or 0), 2)
        except (TypeError, ValueError):
            deltas[k] = None

    def _mean_field(pkg: dict[str, Any], field: str) -> float:
        per = (pkg.get("visual_scores") or {}).get("per_scene") or {}
        if isinstance(per, dict):
            cards = list(per.values())
        elif isinstance(per, list):
            cards = per
        else:
            cards = []
        vals = [float(c.get(field) or 0) for c in cards if isinstance(c, dict)]
        return round(sum(vals) / len(vals), 1) if vals else 0.0

    dim_keys = [
        "composition",
        "educational_clarity",
        "thumbnail_appeal",
        "continuity",
        "motion_potential",
        "overall_professional_quality",
    ]
    dimension_deltas = {
        d: round(_mean_field(after_package, d) - _mean_field(before_package, d), 2) for d in dim_keys
    }
    return {
        "before": b,
        "after": a,
        "deltas": deltas,
        "dimension_deltas": dimension_deltas,
        "continuity_before": (before_package.get("continuity_report") or {}).get("continuity_score"),
        "continuity_after": (after_package.get("continuity_report") or {}).get("continuity_score"),
        "improved": float(a.get("mean_overall_professional_quality") or 0)
        >= float(b.get("mean_overall_professional_quality") or 0),
    }
