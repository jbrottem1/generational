"""Build / attach Visual Source Intelligence packages."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.visual_source_intelligence.models import PACKAGE_TYPE, PACKAGE_VERSION
from services.visual_source_intelligence.review import creative_review
from services.visual_source_intelligence.select import apply_choice_to_scene, choose_source

ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = ROOT / "data" / "visual_source_intelligence" / "packages"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _scenes(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    vp = candidate.get("visual_package") if isinstance(candidate.get("visual_package"), dict) else {}
    scenes = list(vp.get("scenes") or candidate.get("scenes") or [])
    return [dict(s) for s in scenes if isinstance(s, dict)]


def _ensure_asset_intelligence(candidate: dict[str, Any], *, topic: str) -> dict[str, Any]:
    """Compose Asset Intelligence as a pool when missing — never blocks."""
    out = dict(candidate)
    if out.get("asset_intelligence"):
        return out
    try:
        from services.asset_intelligence.package import (
            attach_package_to_candidate,
            build_asset_intelligence_package,
        )

        keywords = []
        for s in _scenes(out)[:6]:
            q = str(s.get("stock_footage_query") or s.get("subject") or "")
            if q:
                keywords.append(q)
        pkg = build_asset_intelligence_package(
            topic=topic or str(out.get("topic") or "topic"),
            keywords=keywords[:8],
            needed=max(6, len(_scenes(out)) or 6),
        )
        out = attach_package_to_candidate(out, pkg)
    except Exception:  # noqa: BLE001
        out["_asset_intelligence_soft_error"] = "unavailable"
    return out


def build_visual_source_package(
    candidate: dict[str, Any] | None = None,
    *,
    topic: str = "",
    production_id: str = "",
    write: bool = True,
    out_path: str | Path | None = None,
) -> dict[str, Any]:
    """Evaluate every scene and choose the highest-quality available source."""
    candidate = dict(candidate or {})
    topic = topic or str(candidate.get("topic") or candidate.get("title") or "")
    candidate = _ensure_asset_intelligence(candidate, topic=topic)
    scenes = _scenes(candidate)

    used_paths: set[str] = set()
    camera_seen: set[str] = set()
    decisions: list[dict[str, Any]] = []
    updated_scenes: list[dict[str, Any]] = []

    for i, scene in enumerate(scenes):
        choice = choose_source(
            scene,
            candidate=candidate,
            topic=topic,
            used_paths=used_paths,
            camera_seen=camera_seen,
            scene_index=i,
        )
        applied = apply_choice_to_scene(scene, choice)
        path = (choice.get("selected") or {}).get("path")
        if path:
            used_paths.add(str(path))
        cam = choice.get("camera_motion")
        if cam:
            camera_seen.add(str(cam))
        decisions.append(
            {
                "scene_number": applied.get("scene_number") or i + 1,
                "scene_id": applied.get("scene_id") or applied.get("id") or f"scene_{i:02d}",
                "intent": choice.get("intent"),
                "selected": choice.get("selected"),
                "alternatives": choice.get("alternatives"),
                "asset_type": choice.get("asset_type"),
                "tier": choice.get("tier"),
                "tier_label": choice.get("tier_label"),
                "fallback_used": choice.get("fallback_used"),
                "fallback_reason": choice.get("fallback_reason"),
                "camera_motion": choice.get("camera_motion"),
                "media_type": choice.get("media_type"),
                "scene": {
                    "scene_number": applied.get("scene_number") or i + 1,
                    "approved_asset_path": applied.get("approved_asset_path"),
                    "asset_type": applied.get("asset_type"),
                },
            }
        )
        updated_scenes.append(applied)

    # Rebuild provider-agnostic asset_requests from chosen asset_types
    asset_requests: list[dict[str, Any]] = []
    try:
        from services.visual.sources import build_asset_requests

        asset_requests = build_asset_requests(updated_scenes)
        for req, dec in zip(asset_requests, decisions):
            sel = dec.get("selected") or {}
            if sel.get("path"):
                req["path"] = sel["path"]
                req["local_path"] = sel["path"]
                req["resolved_path"] = sel["path"]
            req["vsi_tier"] = dec.get("tier")
            req["vsi_source"] = sel.get("source_key")
            req["vsi_fallback_reason"] = dec.get("fallback_reason")
    except Exception:  # noqa: BLE001
        asset_requests = []

    package: dict[str, Any] = {
        "package_type": PACKAGE_TYPE,
        "package_version": PACKAGE_VERSION,
        "generated_at": _now(),
        "topic": topic,
        "production_id": production_id,
        "scene_count": len(updated_scenes),
        "scene_decisions": decisions,
        "scenes": updated_scenes,
        "asset_requests": asset_requests,
        "fallback_summary": {
            "by_tier": _count_tiers(decisions),
            "fallback_count": sum(1 for d in decisions if d.get("fallback_used")),
            "stock_video_count": sum(
                1 for d in decisions if (d.get("selected") or {}).get("source_key") in {
                    "stock_video",
                    "licensed_stock_video",
                    "library_video",
                    "stock_footage",
                }
            ),
            "ai_video_count": sum(
                1 for d in decisions if (d.get("selected") or {}).get("source_key") == "ai_video"
            ),
            "diagram_count": sum(
                1 for d in decisions if (d.get("selected") or {}).get("source_key") == "animated_diagram"
            ),
            "still_motion_count": sum(
                1 for d in decisions if (d.get("selected") or {}).get("source_key") == "ai_still_motion"
            ),
            "static_count": sum(
                1 for d in decisions if (d.get("selected") or {}).get("source_key") == "static_image"
            ),
        },
        "updated_scenes": updated_scenes,
    }
    package["creative_review"] = creative_review(candidate, package=package)

    if write:
        OUT_ROOT.mkdir(parents=True, exist_ok=True)
        if out_path:
            path = Path(out_path)
        else:
            slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in topic)[:48] or "topic"
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            path = OUT_ROOT / f"{slug}_{stamp}_VSI.json"
        if path.is_dir():
            path = path / "VISUAL_SOURCE_INTELLIGENCE.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(package, indent=2, default=str) + "\n", encoding="utf-8")
        package["path"] = str(path)
        # Companion markdown review
        md_path = path.with_suffix(".md")
        md_path.write_text(str((package.get("creative_review") or {}).get("markdown") or ""), encoding="utf-8")
        package["review_markdown_path"] = str(md_path)

    return package


def attach_visual_source_package(
    candidate: dict[str, Any],
    package: dict[str, Any],
) -> dict[str, Any]:
    """Soft-attach selections onto candidate.visual_package before media fulfilment."""
    out = dict(candidate)
    out["visual_source_intelligence"] = {
        "path": package.get("path"),
        "fallback_summary": package.get("fallback_summary"),
        "creative_review": package.get("creative_review"),
        "scene_count": package.get("scene_count"),
    }
    out["VISUAL_SOURCE_INTELLIGENCE"] = package

    vp = dict(out.get("visual_package") or {})
    scenes = list(package.get("updated_scenes") or package.get("scenes") or [])
    if scenes:
        vp["scenes"] = scenes
    if package.get("asset_requests"):
        vp["asset_requests"] = package["asset_requests"]
    vp["visual_source_intelligence"] = {
        "path": package.get("path"),
        "fallback_summary": package.get("fallback_summary"),
    }
    out["visual_package"] = vp

    # Mirror top-level scenes if present
    if out.get("scenes") and scenes:
        out["scenes"] = scenes

    out["prefer_vsi_asset_requests"] = True
    return out


def _count_tiers(decisions: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for d in decisions:
        label = str(d.get("tier_label") or d.get("tier") or "unknown")
        counts[label] = counts.get(label, 0) + 1
    return counts
