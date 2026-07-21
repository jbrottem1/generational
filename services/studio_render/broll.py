"""Module 8 — B-Roll Director: authentic supporting footage, no repeats."""

from __future__ import annotations

PREFERRED_BROLL_SOURCES = (
    "NASA",
    "ESA",
    "NOAA",
    "USGS",
    "NIH",
    "Library of Congress",
    "government",
    "public domain",
    "wikimedia",
    "professional stock",
)


def _source_score(asset: dict) -> int:
    blob = " ".join(
        str(asset.get(k) or "")
        for k in ("source", "source_url", "license", "credit", "provider")
    ).lower()
    for i, name in enumerate(PREFERRED_BROLL_SOURCES):
        if name.lower() in blob:
            return 100 - i * 3
    if "ai-generated" in blob or "placeholder" in blob:
        return 15
    return 50


def collect_candidate_assets(candidate: dict) -> list[dict]:
    assets: list[dict] = []
    for key in ("evidence_assets", "visual_assets", "assets", "images", "broll"):
        for a in candidate.get(key) or []:
            if isinstance(a, dict):
                assets.append(a)
    for scene in (candidate.get("visual_package") or {}).get("scenes") or []:
        if scene.get("source_url") or scene.get("source"):
            assets.append(
                {
                    "id": scene.get("scene_id"),
                    "source": scene.get("source_url") or scene.get("source"),
                    "license": scene.get("license") or "",
                    "confidence": scene.get("confidence") or 80,
                    "concepts": scene.get("concepts") or [],
                }
            )
        for a in scene.get("assets") or scene.get("images") or []:
            if isinstance(a, dict):
                assets.append(a)
    return assets


def build_broll_plan(candidate: dict) -> list[dict]:
    assets = collect_candidate_assets(candidate)
    scenes = list((candidate.get("visual_package") or {}).get("scenes") or [])
    if not scenes:
        scenes = [{"scene_id": f"s{i+1}"} for i in range(max(1, len(assets) or 1))]

    ranked = sorted(assets, key=_source_score, reverse=True)
    used_ids: set[str] = set()
    plan: list[dict] = []

    for i, scene in enumerate(scenes):
        sid = str(scene.get("scene_id") or f"s{i+1}")
        pick = None
        for asset in ranked:
            aid = str(asset.get("id") or asset.get("source") or asset.get("filename") or "")
            if aid and aid in used_ids:
                continue
            pick = asset
            if aid:
                used_ids.add(aid)
            break
        # Rotate if exhausted
        if pick is None and ranked:
            pick = ranked[i % len(ranked)]

        plan.append(
            {
                "scene_id": sid,
                "asset_id": (pick or {}).get("id") or (pick or {}).get("source") or "unassigned",
                "source": (pick or {}).get("source") or (pick or {}).get("source_url") or "",
                "license": (pick or {}).get("license") or "",
                "source_score": _source_score(pick) if pick else 0,
                "prefer_real_footage": True,
                "avoid_repeat": True,
                "reason": "Rotated authentic B-roll for engagement",
            }
        )
    return plan
