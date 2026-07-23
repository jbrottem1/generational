"""Build / validate production Asset Intelligence packages (renderer feed, no pipeline edit)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.asset_intelligence.index import record_usage, seed_from_existing_sources
from services.asset_intelligence.models import PACKAGE_VERSION
from services.asset_intelligence.search import duplicate_risk, score_asset_quality, semantic_search

ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = ROOT / "data" / "asset_intelligence" / "packages"


def build_asset_intelligence_package(
    *,
    topic: str,
    keywords: list[str] | None = None,
    collection: str = "",
    platform: str = "youtube_shorts",
    audience: str = "general_public",
    channel: str = "",
    needed: int = 6,
    backups_per_slot: int = 2,
) -> dict[str, Any]:
    """Select best assets + backups with diversity / license / quality analysis."""
    seed_from_existing_sources(limit_per_source=60)
    queries = [topic] + list(keywords or [])
    selected: list[dict[str, Any]] = []
    backups: list[dict[str, Any]] = []
    exclude: set[str] = set()

    for q in queries:
        hits = semantic_search(q, limit=needed * 3, collection=collection)
        for hit in hits:
            risk = duplicate_risk(hit, selected)
            if risk["is_duplicate"]:
                continue
            if recent_overuse(hit):
                continue
            scores = hit.get("scores") or score_asset_quality(hit, query=q)
            if float(scores.get("overall_score") or 0) < 40:
                continue
            row = {**hit, "scores": scores, "selected_for_query": q}
            if len(selected) < needed:
                selected.append(row)
                exclude.add(str(row.get("asset_id")))
            elif len(backups) < needed * backups_per_slot:
                if str(row.get("asset_id")) not in exclude:
                    backups.append(row)
                    exclude.add(str(row.get("asset_id")))
        if len(selected) >= needed:
            break

    # Fill from broader search if short
    if len(selected) < needed:
        for hit in semantic_search(topic, limit=40):
            if str(hit.get("asset_id")) in exclude:
                continue
            if duplicate_risk(hit, selected)["is_duplicate"]:
                continue
            selected.append(hit)
            exclude.add(str(hit.get("asset_id")))
            if len(selected) >= needed:
                break

    diversity = _visual_diversity(selected)
    package = {
        "package_version": PACKAGE_VERSION,
        "package_type": "asset_intelligence",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "topic": topic,
        "keywords": keywords or [],
        "collection": collection,
        "platform": platform,
        "audience": audience,
        "channel": channel,
        "selected_media": selected,
        "backup_choices": backups,
        "licensing": [
            {
                "asset_id": a.get("asset_id"),
                "license": a.get("license"),
                "creator": a.get("creator"),
                "source_system": a.get("source_system"),
            }
            for a in selected + backups
        ],
        "quality_scores": {a.get("asset_id"): a.get("scores") for a in selected},
        "reuse_analysis": {
            a.get("asset_id"): {
                "reuse_count": a.get("reuse_count"),
                "last_usage": a.get("last_usage"),
                "recent_72h": recent_overuse(a, as_bool=False),
            }
            for a in selected
        },
        "visual_diversity_score": diversity,
        "renderer_feed": {
            "evidence_assets": [_renderer_shape(a) for a in selected if a.get("kind") in ("image", "chart", "map", "scientific_diagram", "educational_graphic")],
            "visual_assets": [_renderer_shape(a) for a in selected],
            "note": "Optional attach to candidate — does not modify production pipeline stages",
        },
    }
    package["validation"] = validate_asset_intelligence_package(package)

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in topic)[:48] or "topic"
    path = OUT_ROOT / f"{slug}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
    package["path"] = str(path)

    # Record usage for selected (library learning)
    for a in selected:
        record_usage(
            str(a.get("asset_id")),
            channel=channel,
            audience=audience,
            platform=platform,
            topic=topic,
        )
    return package


def attach_package_to_candidate(candidate: dict[str, Any], package: dict[str, Any]) -> dict[str, Any]:
    """Optional non-pipeline mutation of a candidate dict for renderer consumption."""
    out = dict(candidate)
    feed = package.get("renderer_feed") or {}
    if feed.get("evidence_assets"):
        out["evidence_assets"] = list(feed["evidence_assets"])
    if feed.get("visual_assets"):
        out["visual_assets"] = list(feed["visual_assets"])
    out["asset_intelligence_package"] = {
        "path": package.get("path"),
        "visual_diversity_score": package.get("visual_diversity_score"),
        "validation": package.get("validation"),
        "selected_ids": [a.get("asset_id") for a in package.get("selected_media") or []],
    }
    # Do not overwrite asset_generation asset_package; store intelligence alongside
    out["asset_intelligence"] = package
    return out


def validate_asset_intelligence_package(package: dict[str, Any]) -> dict[str, Any]:
    selected = package.get("selected_media") or []
    fails: list[str] = []
    warnings: list[str] = []

    ids = [str(a.get("asset_id")) for a in selected]
    if len(ids) != len(set(ids)):
        fails.append("contains_duplicates")

    for a in selected:
        scores = a.get("scores") or {}
        w = int(a.get("width") or 0)
        h = int(a.get("height") or 0)
        res = str(a.get("resolution") or "")
        if w and w < 640 and h and h < 640:
            fails.append(f"low_resolution:{a.get('asset_id')}")
        if "360" in res or "480p" in res.lower():
            fails.append(f"low_resolution:{a.get('asset_id')}")
        if float(a.get("animation_quality") or 0) and float(a.get("animation_quality") or 0) < 40:
            if str(a.get("kind") or "") in ("animation", "video_clip", "particle_effect"):
                fails.append(f"poor_animation_quality:{a.get('asset_id')}")
        if float(scores.get("overall_score") or 0) < 35:
            warnings.append(f"low_overall:{a.get('asset_id')}")
        if int(a.get("reuse_count") or 0) > 12:
            warnings.append(f"excessive_reuse:{a.get('asset_id')}")

    diversity = float(package.get("visual_diversity_score") or 0)
    if diversity < 40 and len(selected) >= 3:
        fails.append("fails_visual_diversity_threshold")

    # Excessive identical topics
    topics = [str(a.get("topic") or "").lower() for a in selected if a.get("topic")]
    if topics and len(topics) >= 3 and len(set(topics)) == 1:
        fails.append("repeat_assets_excessively")

    return {
        "ok": not fails,
        "passed": not fails,
        "hard_fails": sorted(set(fails)),
        "warnings": sorted(set(warnings)),
        "selected_count": len(selected),
        "diversity_score": diversity,
    }


def recent_overuse(asset: dict[str, Any], *, as_bool: bool = True) -> Any:
    from services.asset_intelligence.index import recent_usage

    n = recent_usage(str(asset.get("asset_id") or ""), within_hours=48)
    if as_bool:
        return n >= 3
    return n


def _visual_diversity(selected: list[dict[str, Any]]) -> float:
    if not selected:
        return 0.0
    kinds = {str(a.get("kind") or "") for a in selected}
    collections = {str(a.get("collection") or "") for a in selected}
    topics = {str(a.get("topic") or "")[:40] for a in selected}
    sources = {str(a.get("source_system") or "") for a in selected}
    # 0–100
    score = (
        min(40, len(kinds) * 12)
        + min(25, len(collections) * 8)
        + min(20, len(topics) * 5)
        + min(15, len(sources) * 5)
    )
    return float(min(100, score))


def _renderer_shape(asset: dict[str, Any]) -> dict[str, Any]:
    return {
        "asset_id": asset.get("asset_id"),
        "uri": asset.get("uri"),
        "path": asset.get("uri"),
        "license": asset.get("license"),
        "concepts": asset.get("keywords") or [],
        "topic": asset.get("topic"),
        "source": asset.get("source_system"),
        "score": (asset.get("scores") or {}).get("overall_score"),
        "kind": asset.get("kind"),
    }
