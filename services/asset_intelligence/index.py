"""Unified asset index — indexes reality, local_cache, asset_generation registry."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.asset_intelligence.models import COLLECTIONS, empty_metadata

ROOT = Path(__file__).resolve().parents[2]
INTEL_ROOT = ROOT / "data" / "asset_intelligence"
INDEX_PATH = INTEL_ROOT / "LIBRARY_INDEX.json"
USAGE_PATH = INTEL_ROOT / "USAGE_LOG.json"
COLLECTIONS_PATH = INTEL_ROOT / "COLLECTIONS.json"


def ensure_dirs() -> None:
    INTEL_ROOT.mkdir(parents=True, exist_ok=True)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_index() -> dict[str, Any]:
    ensure_dirs()
    if not INDEX_PATH.exists():
        return {"version": "1.0", "assets": {}, "updated_at": ""}
    try:
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": "1.0", "assets": {}, "updated_at": ""}


def save_index(data: dict[str, Any]) -> Path:
    ensure_dirs()
    data["updated_at"] = _now()
    INDEX_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return INDEX_PATH


def upsert_asset(meta: dict[str, Any]) -> dict[str, Any]:
    idx = load_index()
    assets = dict(idx.get("assets") or {})
    aid = str(meta.get("asset_id") or "")
    if not aid:
        return meta
    prev = assets.get(aid) or {}
    merged = {**prev, **meta}
    assets[aid] = merged
    idx["assets"] = assets
    save_index(idx)
    _touch_collection(str(merged.get("collection") or ""), aid)
    return merged


def get_asset(asset_id: str) -> dict[str, Any] | None:
    return (load_index().get("assets") or {}).get(asset_id)


def all_assets() -> list[dict[str, Any]]:
    return list((load_index().get("assets") or {}).values())


def record_usage(
    asset_id: str,
    *,
    channel: str = "",
    audience: str = "",
    platform: str = "",
    topic: str = "",
) -> None:
    ensure_dirs()
    events = []
    if USAGE_PATH.exists():
        try:
            events = json.loads(USAGE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            events = []
    events.append(
        {
            "asset_id": asset_id,
            "at": _now(),
            "channel": channel,
            "audience": audience,
            "platform": platform,
            "topic": topic,
        }
    )
    USAGE_PATH.write_text(json.dumps(events[-2000:], indent=2) + "\n", encoding="utf-8")
    asset = get_asset(asset_id)
    if asset:
        asset["reuse_count"] = int(asset.get("reuse_count") or 0) + 1
        asset["last_usage"] = _now()
        upsert_asset(asset)


def recent_usage(asset_id: str, *, within_hours: float = 72.0) -> int:
    if not USAGE_PATH.exists():
        return 0
    try:
        events = json.loads(USAGE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    cutoff = datetime.now(timezone.utc).timestamp() - within_hours * 3600
    n = 0
    for e in events:
        if e.get("asset_id") != asset_id:
            continue
        try:
            ts = datetime.fromisoformat(str(e.get("at") or "").replace("Z", "+00:00")).timestamp()
        except ValueError:
            continue
        if ts >= cutoff:
            n += 1
    return n


def _touch_collection(collection: str, asset_id: str) -> None:
    if collection not in COLLECTIONS:
        return
    ensure_dirs()
    data = {"collections": {c: [] for c in COLLECTIONS}}
    if COLLECTIONS_PATH.exists():
        try:
            data = json.loads(COLLECTIONS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    coll = dict(data.get("collections") or {})
    ids = list(coll.get(collection) or [])
    if asset_id not in ids:
        ids.insert(0, asset_id)
    coll[collection] = ids[:500]
    data["collections"] = coll
    COLLECTIONS_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def collection_assets(name: str) -> list[dict[str, Any]]:
    if not COLLECTIONS_PATH.exists():
        return []
    try:
        data = json.loads(COLLECTIONS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    ids = (data.get("collections") or {}).get(name) or []
    out = []
    for aid in ids:
        a = get_asset(aid)
        if a:
            out.append(a)
    return out


def seed_from_existing_sources(*, limit_per_source: int = 80) -> dict[str, Any]:
    """Pull entries from Reality catalog, local_cache, asset_generation registry."""
    added = 0
    # Reality
    try:
        from services.reality.catalog import load_catalog

        cat = load_catalog()
        images = (cat.get("images") or cat.get("entries") or []) if isinstance(cat, dict) else []
        if isinstance(cat, dict) and not images and isinstance(cat.get("by_id"), dict):
            images = list(cat["by_id"].values())
        for i, img in enumerate(images[:limit_per_source]):
            if not isinstance(img, dict):
                continue
            aid = str(img.get("id") or img.get("image_id") or img.get("asset_id") or f"reality_{i}")
            upsert_asset(
                empty_metadata(
                    asset_id=aid,
                    kind="image",
                    topic=str(img.get("topic") or img.get("title") or ""),
                    keywords=list(img.get("concepts") or img.get("tags") or img.get("keywords") or [])[:20],
                    category="reality",
                    collection=_guess_collection(str(img.get("topic") or ""), list(img.get("concepts") or [])),
                    scientific_accuracy=int(img.get("scientific_accuracy") or 70),
                    visual_quality=int(img.get("quality") or img.get("visual_quality") or 70),
                    license=str(img.get("license") or "attribution"),
                    uri=str(img.get("path") or img.get("uri") or img.get("local_path") or ""),
                    source_system="reality_catalog",
                    creator=str(img.get("source") or img.get("creator") or "reality"),
                    resolution=str(img.get("resolution") or ""),
                    orientation="portrait" if "9:16" in str(img.get("aspect") or "") else "landscape",
                )
            )
            added += 1
    except Exception:  # noqa: BLE001
        pass

    # Local cache index
    try:
        from services.media_production import local_cache as _local_cache

        index = _local_cache._load_index()
        for key, entry in list((index.get("entries") or {}).items())[:limit_per_source]:
            if not isinstance(entry, dict):
                continue
            aid = f"cache_{key.replace(':', '_')}"
            upsert_asset(
                empty_metadata(
                    asset_id=aid,
                    kind=str(entry.get("kind") or "image"),
                    topic=str(entry.get("identifier") or key),
                    keywords=[str(entry.get("identifier") or ""), str(entry.get("kind") or "")],
                    category="cache",
                    collection=_guess_collection(str(entry.get("identifier") or ""), []),
                    visual_quality=65,
                    uri=str(entry.get("path") or ""),
                    source_system="local_cache",
                    license="cached",
                    creator="cache",
                )
            )
            added += 1
    except Exception:  # noqa: BLE001
        pass

    # Asset generation registry
    try:
        from services.asset_generation.registry import get_asset_registry

        reg = get_asset_registry()
        items = []
        if hasattr(reg, "list_assets"):
            items = reg.list_assets() or []
        elif hasattr(reg, "all"):
            items = reg.all() or []
        elif hasattr(reg, "_read"):
            raw = reg._read()
            items = list((raw.get("assets") or raw).values()) if isinstance(raw, dict) else []
        for a in list(items)[:limit_per_source]:
            if not isinstance(a, dict):
                continue
            meta = a.get("metadata") or {}
            upsert_asset(
                empty_metadata(
                    asset_id=str(a.get("asset_id") or ""),
                    kind=str(a.get("asset_type") or a.get("asset_class") or "image"),
                    topic=str(meta.get("title") or a.get("category") or ""),
                    keywords=list(meta.get("tags") or [])[:20],
                    category=str(a.get("category") or "generated"),
                    collection=_guess_collection(str(meta.get("title") or ""), list(meta.get("tags") or [])),
                    visual_quality=int((a.get("quality") or {}).get("overall") or 70),
                    animation_quality=int((a.get("quality") or {}).get("motion") or 0),
                    license=str(meta.get("license") or "generated"),
                    uri=str(a.get("uri") or ""),
                    source_system="asset_generation",
                    fingerprint=str(a.get("fingerprint") or ""),
                    width=int(a.get("width") or 0),
                    height=int(a.get("height") or 0),
                    duration_sec=float(a.get("duration_sec") or 0),
                    creator=str(a.get("provider") or "asset_generation"),
                    reuse_count=int(a.get("reuse_count") or 0),
                )
            )
            added += 1
    except Exception:  # noqa: BLE001
        pass

    # Seed synthetic collection starters when index still thin (no fake files — metadata placeholders)
    for coll in COLLECTIONS:
        if not collection_assets(coll):
            aid = f"seed_{coll}_overlay"
            upsert_asset(
                empty_metadata(
                    asset_id=aid,
                    kind="educational_graphic",
                    topic=coll,
                    keywords=[coll, "education", "graphic"],
                    category="seed",
                    collection=coll,
                    scientific_accuracy=60,
                    visual_quality=55,
                    license="internal_seed",
                    source_system="asset_intelligence_seed",
                    creator="system",
                    uri="",
                )
            )
            added += 1

    # High-demand topic anchors (metadata only — search/ranking fodder until real media is indexed)
    for topic, keywords, coll, kind in (
        ("DNA double helix", ["dna", "genome", "biology", "cell"], "biology", "scientific_diagram"),
        ("Cell division mitosis", ["cell", "division", "mitosis", "biology"], "biology", "animation"),
        ("Deep space nebula", ["space", "nebula", "astronomy", "galaxy"], "astronomy", "image"),
        ("Earth orbit", ["space", "earth", "orbit", "astronomy"], "astronomy", "render_3d"),
        ("Economic supply demand", ["economics", "finance", "market", "supply"], "finance", "chart"),
        ("Cognitive bias map", ["psychology", "bias", "mind", "behavior"], "psychology", "educational_graphic"),
        ("Historical timeline", ["history", "timeline", "century"], "history", "educational_graphic"),
        ("Force mass acceleration", ["physics", "force", "newton", "mechanics"], "physics", "chart"),
    ):
        aid = f"seed_topic_{coll}_{kind}"
        if not get_asset(aid):
            upsert_asset(
                empty_metadata(
                    asset_id=aid,
                    kind=kind,
                    topic=topic,
                    keywords=keywords,
                    category="seed",
                    collection=coll,
                    scientific_accuracy=75,
                    visual_quality=70,
                    animation_quality=65 if kind in ("animation", "video_clip") else 40,
                    motion_score=60 if kind in ("animation", "video_clip", "background_loop") else 35,
                    resolution="1920x1080",
                    width=1920,
                    height=1080,
                    license="internal_seed",
                    source_system="asset_intelligence_seed",
                    creator="system",
                    uri="",
                )
            )
            added += 1

    return {"ok": True, "upserted": added, "total": len(all_assets()), "index_path": str(INDEX_PATH)}


def _guess_collection(topic: str, keywords: list) -> str:
    blob = f"{topic} {' '.join(str(k) for k in keywords)}".lower()
    mapping = {
        "biology": ("cell", "dna", "bio", "octopus", "marine", "organism"),
        "astronomy": ("space", "planet", "star", "galaxy", "nasa", "orbit"),
        "physics": ("force", "energy", "quantum", "physics", "gravity"),
        "history": ("history", "ancient", "war", "empire", "century"),
        "finance": ("money", "market", "finance", "economy", "invest"),
        "medicine": ("health", "medical", "vaccine", "doctor", "disease"),
        "technology": ("tech", "ai", "software", "computer", "robot"),
        "nature": ("nature", "forest", "animal", "earth", "ocean"),
        "psychology": ("mind", "brain", "bias", "psych", "behavior"),
        "engineering": ("bridge", "engine", "build", "structure", "machine"),
    }
    for coll, words in mapping.items():
        if any(w in blob for w in words):
            return coll
    return "technology"
