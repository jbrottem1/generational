"""Semantic-ish search + quality ranking + duplicate awareness."""

from __future__ import annotations

import re
from typing import Any

from services.asset_intelligence.index import all_assets, recent_usage
from services.asset_intelligence.models import QUALITY_FIELDS


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(t) > 1}


def score_asset_quality(asset: dict[str, Any], *, query: str = "") -> dict[str, Any]:
    """Compute visual / educational / retention / motion / thumbnail / overall scores."""
    visual = float(asset.get("visual_quality") or 50)
    edu = float(asset.get("scientific_accuracy") or 50)
    motion = float(asset.get("motion_score") or asset.get("animation_quality") or 40)
    # Thumbnail usefulness: sharp stills / graphics
    kind = str(asset.get("kind") or "")
    thumb = 70.0 if kind in ("image", "educational_graphic", "chart", "icon", "logo") else 40.0
    if int(asset.get("width") or 0) >= 1080 or "1920" in str(asset.get("resolution") or ""):
        thumb = min(100, thumb + 15)
        visual = min(100, visual + 8)
    retention = (visual * 0.4 + edu * 0.25 + motion * 0.35)
    # Recency penalty when overused
    reuse = int(asset.get("reuse_count") or 0)
    recent = recent_usage(str(asset.get("asset_id") or ""), within_hours=72)
    diversity_penalty = min(25, reuse * 2 + recent * 8)
    overall = max(0, (visual + edu + retention + motion + thumb) / 5.0 - diversity_penalty * 0.35)

    # Query relevance boost
    q = _tokens(query)
    if q:
        hay = _tokens(
            " ".join(
                [
                    str(asset.get("topic") or ""),
                    str(asset.get("category") or ""),
                    str(asset.get("collection") or ""),
                    " ".join(str(k) for k in (asset.get("keywords") or [])),
                ]
            )
        )
        overlap = len(q & hay) / max(1, len(q))
        overall = min(100, overall + overlap * 25)
        edu = min(100, edu + overlap * 10)

    scores = {
        "visual_score": round(visual, 1),
        "educational_score": round(edu, 1),
        "retention_score": round(retention, 1),
        "motion_score": round(motion, 1),
        "thumbnail_usefulness": round(thumb, 1),
        "overall_score": round(overall, 1),
        "diversity_penalty": round(diversity_penalty, 1),
        "query_overlap": round(len(q & _tokens(str(asset.get("topic") or ""))) / max(1, len(q)), 3) if q else 0,
    }
    for k in QUALITY_FIELDS:
        scores.setdefault(k, 0)
    return scores


def semantic_search(
    query: str,
    *,
    limit: int = 12,
    collection: str = "",
    kind: str = "",
    exclude_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Return highest-scoring assets for a query (keyword semantic ranking)."""
    exclude_ids = exclude_ids or set()
    rows = []
    for asset in all_assets():
        aid = str(asset.get("asset_id") or "")
        if not aid or aid in exclude_ids:
            continue
        if collection and asset.get("collection") != collection:
            continue
        if kind and kind not in str(asset.get("kind") or ""):
            continue
        scores = score_asset_quality(asset, query=query)
        # Soft filter: require some relevance unless query empty
        if query.strip():
            hay = f"{asset.get('topic')} {asset.get('collection')} {' '.join(map(str, asset.get('keywords') or []))}".lower()
            qtoks = _tokens(query)
            if not any(t in hay for t in qtoks) and scores["overall_score"] < 55:
                continue
        rows.append({**asset, "scores": scores, "rank_score": scores["overall_score"]})
    rows.sort(key=lambda r: (-float(r.get("rank_score") or 0), int(r.get("reuse_count") or 0)))
    return rows[:limit]


def duplicate_risk(asset: dict[str, Any], selected: list[dict[str, Any]]) -> dict[str, Any]:
    """Detect identical or overly similar assets already selected."""
    aid = str(asset.get("asset_id") or "")
    fp = str(asset.get("fingerprint") or "")
    uri = str(asset.get("uri") or "")
    topic = str(asset.get("topic") or "").lower().strip()
    reasons = []
    for s in selected:
        if aid and aid == s.get("asset_id"):
            reasons.append("same_asset_id")
        if fp and fp == s.get("fingerprint"):
            reasons.append("same_fingerprint")
        if uri and uri and uri == s.get("uri"):
            reasons.append("same_uri")
        if topic and topic == str(s.get("topic") or "").lower().strip() and asset.get("kind") == s.get("kind"):
            reasons.append("same_topic_kind")
    return {"is_duplicate": bool(reasons), "reasons": reasons}
