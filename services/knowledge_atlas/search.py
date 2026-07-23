"""Knowledge Atlas search — find visual evidence by concept, keyword, domain."""

from __future__ import annotations

from typing import Any

from services.knowledge_atlas.catalog import load_atlas
from services.knowledge_atlas.evaluator import score_asset
from services.knowledge_atlas.models import AtlasAsset
from services.quality.visual_priority import prefer_authentic, priority_boost, priority_rank


def _tokenize(text: str) -> set[str]:
    return {w.lower() for w in text.replace("_", " ").split() if len(w) > 2}


def search_visuals(
    *,
    query: str = "",
    concepts: list[str] | None = None,
    domain: str | None = None,
    visual_type: str | None = None,
    limit: int = 12,
    prefer_photos: bool = True,
) -> list[dict[str, Any]]:
    """Search Atlas assets; returns ranked hits with scores.

    When ``prefer_photos`` is True (default), authentic photographs outrank
    diagrams, illustrations, and AI/synthetic assets at equal relevance.
    """
    concepts = concepts or []
    wanted = _tokenize(query) | _tokenize(" ".join(concepts))
    hits: list[tuple[float, AtlasAsset]] = []

    for asset in load_atlas().values():
        if domain and asset.category.lower() != domain.lower():
            continue
        if visual_type and asset.visual_type.lower() != visual_type.lower():
            continue

        hay = _tokenize(
            " ".join(
                [
                    asset.topic,
                    asset.description,
                    asset.species,
                    asset.scientific_name,
                    " ".join(asset.keywords),
                    " ".join(asset.concepts),
                    " ".join(asset.suggested_uses),
                ]
            )
        )
        concept_set = {c.lower() for c in asset.concepts}
        concept_hits = len({c.lower() for c in concepts} & concept_set) if concepts else 0
        text_hits = len(wanted & hay) if wanted else 0

        if not wanted and not concepts:
            relevance = score_asset(asset)
        else:
            relevance = concept_hits * 0.40 + text_hits * 0.22 + score_asset(asset) * 0.28
            if prefer_photos:
                relevance += priority_boost(asset.visual_type)

        if relevance <= 0 and (wanted or concepts):
            continue
        hits.append((relevance, asset))

    if prefer_photos:
        # Sort by priority rank first, then relevance
        hits.sort(key=lambda x: (priority_rank(x[1].visual_type), -x[0], -x[1].reuse_count, x[1].asset_id))
    else:
        hits.sort(key=lambda x: (-x[0], -x[1].reuse_count, x[1].asset_id))

    out: list[dict[str, Any]] = []
    for rel, asset in hits[: max(limit * 2, limit)]:
        out.append(
            {
                "asset_id": asset.asset_id,
                "relevance": round(rel, 3),
                "quality_score": asset.quality_score,
                "visual_type": asset.visual_type,
                "priority_rank": priority_rank(asset.visual_type),
                "category": asset.category,
                "topic": asset.topic,
                "path": asset.path,
                "suggested_layout": _suggest_layout(asset),
            }
        )
    if prefer_photos:
        out = prefer_authentic(out, limit=limit)
    return out[:limit]


def _suggest_layout(asset: AtlasAsset) -> str:
    if asset.compare_with:
        return "split_compare"
    if asset.visual_type in ("diagram", "map", "chart", "geological_cross_section"):
        return "board_inset"
    return "evidence_tray"
