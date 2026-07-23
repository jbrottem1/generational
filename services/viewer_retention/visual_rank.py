"""Module 7 — Visual Intelligence 2.0: prefer authentic scientific sources, rank assets."""

from __future__ import annotations

from core.heuristics import clamp
from services.viewer_retention.models import PREFERRED_IMAGE_SOURCES


def _source_tier(source: str, license_str: str = "") -> int:
    blob = f"{source} {license_str}".lower()
    for i, name in enumerate(PREFERRED_IMAGE_SOURCES):
        if name.lower() in blob:
            return 100 - i * 4
    if "ai-generated" in blob or "synthetic" in blob or "placeholder" in blob:
        return 20
    if "wikimedia" in blob or "cc-" in blob or "public domain" in blob:
        return 78
    return 55


def rank_image(asset: dict, *, topic: str = "") -> dict:
    source = str(
        asset.get("source")
        or asset.get("source_url")
        or asset.get("credit")
        or asset.get("provider")
        or ""
    )
    license_str = str(asset.get("license") or "")
    confidence = float(asset.get("confidence") or asset.get("confidence_score") or 70)
    concepts = " ".join(str(c) for c in (asset.get("concepts") or [])).lower()
    topic_l = topic.lower()

    educational = 60
    if any(w in concepts or w in source.lower() for w in topic_l.split()[:4] if len(w) > 3):
        educational += 20
    beauty = clamp(55 + (8 if "nasa" in source.lower() else 0) + (5 if confidence >= 90 else 0), 0, 100)
    relevance = clamp(50 + (25 if topic_l and topic_l.split()[0] in (concepts + source.lower()) else 0), 0, 100)
    emotional = clamp(45 + (15 if any(w in concepts for w in ("human", "face", "earth", "animal")) else 0), 0, 100)
    composition = clamp(int(asset.get("composition_score") or 70), 0, 100)
    color = clamp(int(asset.get("color_quality") or 72), 0, 100)
    source_score = _source_tier(source, license_str)

    overall = clamp(
        round(
            educational * 0.22
            + beauty * 0.12
            + relevance * 0.22
            + emotional * 0.1
            + composition * 0.1
            + color * 0.08
            + source_score * 0.1
            + confidence * 0.06
        ),
        0,
        100,
    )

    return {
        "id": asset.get("id") or asset.get("filename") or source[:40],
        "source": source,
        "license": license_str,
        "confidence": confidence,
        "scores": {
            "educational_value": educational,
            "beauty": beauty,
            "relevance": relevance,
            "emotional_impact": emotional,
            "composition": composition,
            "color_quality": color,
            "source_tier": source_score,
            "confidence": int(confidence),
            "overall": overall,
        },
        "prefer_authentic": source_score >= 70,
        "ai_generated": source_score <= 25,
    }


def collect_assets(candidate: dict) -> list[dict]:
    assets: list[dict] = []
    for key in ("evidence_assets", "visual_assets", "assets", "images"):
        for a in candidate.get(key) or []:
            if isinstance(a, dict):
                assets.append(a)
    ep = candidate.get("evidence_package") or {}
    for a in ep.get("assets") or ep.get("images") or []:
        if isinstance(a, dict):
            assets.append(a)
    vp = candidate.get("visual_package") or {}
    for scene in vp.get("scenes") or []:
        for a in scene.get("assets") or scene.get("images") or []:
            if isinstance(a, dict):
                assets.append(a)
        if scene.get("source_url"):
            assets.append(
                {
                    "id": scene.get("scene_id"),
                    "source": scene.get("source_url") or scene.get("source"),
                    "license": scene.get("license") or "",
                    "confidence": scene.get("confidence") or 80,
                    "concepts": scene.get("concepts") or [],
                }
            )
    return assets


def build_visual_ranking(candidate: dict, *, topic: str = "") -> dict:
    topic = topic or str(candidate.get("title") or candidate.get("topic") or "")
    assets = collect_assets(candidate)
    ranked = [rank_image(a, topic=topic) for a in assets]
    ranked.sort(key=lambda r: r["scores"]["overall"], reverse=True)

    real_pct = 100.0
    if ranked:
        ai = sum(1 for r in ranked if r["ai_generated"])
        real_pct = round(100.0 * (len(ranked) - ai) / len(ranked), 1)

    avg = int(round(sum(r["scores"]["overall"] for r in ranked) / max(1, len(ranked)))) if ranked else 62
    # Prefer authentic sources — penalize AI-heavy packs
    if real_pct < 80:
        avg = clamp(avg - 15, 0, 100)

    weak = [r for r in ranked if r["scores"]["overall"] < 70]
    return {
        "ranked": ranked,
        "count": len(ranked),
        "real_image_pct": real_pct,
        "average_score": avg,
        "weak_assets": [r["id"] for r in weak],
        "preferred_sources": list(PREFERRED_IMAGE_SOURCES),
        "score": avg if ranked else 58,
        "guidance": [
            "Prefer NASA/NOAA/ESA/USGS/NIH/government/museum archives",
            "AI imagery only when authentic media is unavailable",
            "Replace weak assets automatically during polish",
        ],
    }
