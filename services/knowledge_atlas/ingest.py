"""Knowledge Atlas ingest — add assets, deduplicate, sync from Reality."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from services.knowledge_atlas.catalog import (
    ATLAS_DIR,
    COLLECTIONS_PATH,
    CATALOG_PATH,
    find_by_fingerprint,
    fingerprint_for,
    load_atlas,
    save_catalog,
)
from services.knowledge_atlas.evaluator import score_asset
from services.knowledge_atlas.models import AtlasAsset
from services.knowledge_atlas.qc import validate_asset

ROOT = Path(__file__).resolve().parents[2]
REALITY_CATALOG = ROOT / "data" / "reality" / "catalog.json"

# Seed metadata for Project Reality assets
REALITY_SEED: dict[str, dict[str, Any]] = {
    "hoverfly_lateral": {
        "topic": "Hoverfly Batesian mimic",
        "category": "evolution",
        "keywords": ["hoverfly", "syrphid", "mimicry", "insect", "pollinator"],
        "description": "Lateral photograph of a hoverfly (Syrphid) — harmless Batesian mimic of wasps.",
        "visual_type": "photograph",
        "suggested_uses": ["model_vs_mimic_intro", "insect_comparison"],
        "compare_with": ["wasp_lateral"],
        "demo_ids": ["foundation_batesian_101", "foundation_bluffing_103"],
    },
    "wasp_lateral": {
        "topic": "German wasp warning model",
        "category": "evolution",
        "keywords": ["wasp", "vespula", "sting", "warning coloration"],
        "description": "Photograph of a German wasp — harmful model for Batesian mimicry lessons.",
        "visual_type": "photograph",
        "suggested_uses": ["harmful_model", "split_compare"],
        "compare_with": ["hoverfly_lateral"],
        "demo_ids": ["foundation_batesian_101", "foundation_bluffing_103"],
    },
    "coral_snake": {
        "topic": "Eastern coral snake",
        "category": "biology",
        "keywords": ["coral snake", "venomous", "elapidae", "warning bands"],
        "description": "Photograph of an eastern coral snake — venomous aposematic model.",
        "visual_type": "photograph",
        "suggested_uses": ["snake_id_warning", "dangerous_model"],
        "compare_with": ["scarlet_kingsnake"],
        "demo_ids": ["foundation_coral_102"],
    },
    "scarlet_kingsnake": {
        "topic": "Scarlet kingsnake mimic",
        "category": "evolution",
        "keywords": ["kingsnake", "lampropeltis", "harmless", "mimic"],
        "description": "Photograph of scarlet kingsnake — harmless mimic of coral snake banding.",
        "visual_type": "photograph",
        "suggested_uses": ["harmless_mimic", "split_compare"],
        "compare_with": ["coral_snake"],
        "demo_ids": ["foundation_coral_102"],
    },
    "monarch_adult": {
        "topic": "Monarch butterfly",
        "category": "ecology",
        "keywords": ["monarch", "danaus", "milkweed", "warning"],
        "description": "Photograph of adult monarch butterfly — aposematic coloration.",
        "visual_type": "photograph",
        "suggested_uses": ["monarch_viceroy_case", "butterfly_comparison"],
        "compare_with": ["viceroy_adult"],
        "demo_ids": ["foundation_bluffing_103"],
    },
    "viceroy_adult": {
        "topic": "Viceroy butterfly",
        "category": "evolution",
        "keywords": ["viceroy", "limenitis", "mimic", "butterfly"],
        "description": "Photograph of viceroy butterfly — historically taught as monarch mimic; relationship is complex.",
        "visual_type": "photograph",
        "suggested_uses": ["monarch_viceroy_case", "complex_mimicry"],
        "compare_with": ["monarch_adult"],
        "demo_ids": ["foundation_bluffing_103"],
    },
}


def ingest_asset(raw: dict[str, Any], *, dry_run: bool = False) -> tuple[str, AtlasAsset | None]:
    """Add one asset; returns ('added'|'skipped'|'rejected', asset)."""
    asset = AtlasAsset.from_dict(raw)
    fp = asset.fingerprint or fingerprint_for(asset.source, asset.path)
    object.__setattr__(asset, "fingerprint", fp)

    if find_by_fingerprint(fp):
        return "skipped", None

    asset_qc = validate_asset(asset, require_file=True)
    if not asset_qc.passed:
        return "rejected", None

    qs = score_asset(asset)
    object.__setattr__(asset, "quality_score", qs)

    catalog = load_atlas()
    catalog[asset.asset_id] = asset
    if not dry_run:
        save_catalog(catalog)
        _update_collections(asset)
    return "added", asset


def ingest_from_reality_catalog(*, dry_run: bool = False) -> tuple[int, int]:
    """Import data/reality/catalog.json into Knowledge Atlas."""
    if not REALITY_CATALOG.is_file():
        return 0, 0
    data = json.loads(REALITY_CATALOG.read_text(encoding="utf-8"))
    added = skipped = 0
    today = date.today().isoformat()

    for raw in data.get("images") or []:
        image_id = str(raw["image_id"])
        seed = REALITY_SEED.get(image_id, {})
        entry = {
            "asset_id": image_id,
            "topic": seed.get("topic", raw.get("organism", image_id)),
            "keywords": seed.get("keywords", list(raw.get("concepts") or [])),
            "species": raw.get("organism", ""),
            "scientific_name": raw.get("scientific_name", ""),
            "description": seed.get("description", f"Licensed photograph: {raw.get('organism', image_id)}"),
            "source": raw.get("source_url", ""),
            "license": raw.get("license", ""),
            "path": f"data/reality/{raw.get('path', '')}",
            "category": seed.get("category", "biology"),
            "visual_type": seed.get("visual_type", "photograph"),
            "quality_score": 0.0,
            "suggested_uses": seed.get("suggested_uses", []),
            "date_added": today,
            "reuse_count": 0,
            "reuse_history": [],
            "concepts": raw.get("concepts", []),
            "credit": raw.get("credit", ""),
            "resolution": {"width": raw.get("width", 0), "height": raw.get("height", 0)},
            "compare_with": seed.get("compare_with", []),
            "demo_ids": seed.get("demo_ids", []),
        }
        status, _ = ingest_asset(entry, dry_run=dry_run)
        if status == "added":
            added += 1
        else:
            skipped += 1
    return added, skipped


def _update_collections(asset: AtlasAsset) -> None:
    ATLAS_DIR.mkdir(parents=True, exist_ok=True)
    if COLLECTIONS_PATH.is_file():
        data = json.loads(COLLECTIONS_PATH.read_text(encoding="utf-8"))
    else:
        data = {"schema_version": 1, "collections": []}

    coll_map = {c["id"]: c for c in data.get("collections") or []}
    cat = asset.category
    if cat not in coll_map:
        coll_map[cat] = {
            "id": cat,
            "name": cat.replace("_", " ").title(),
            "domain": cat,
            "asset_ids": [],
        }
    ids = coll_map[cat].setdefault("asset_ids", [])
    if asset.asset_id not in ids:
        ids.append(asset.asset_id)
    data["collections"] = sorted(coll_map.values(), key=lambda x: x["id"])
    COLLECTIONS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
