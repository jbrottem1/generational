"""Visual priority ladder — authentic media before AI / drawings.

Production rule (permanent):
  1. Authentic photographs
  2. Authentic scientific diagrams
  3. Public-domain educational illustrations
  4. Museum-quality reconstructions
  5. High-quality AI-generated imagery ONLY when no suitable real-world visual exists

AI-generated imagery supplements real educational material — it must never replace it
when a suitable authentic asset is available.
"""

from __future__ import annotations

from typing import Any

# Lower rank = higher priority
VISUAL_PRIORITY_RANK: dict[str, int] = {
    # Tier 1 — authentic photographs / instrument captures
    "photograph": 1,
    "microscope": 1,
    "histology": 1,
    "medical_imaging": 1,
    "satellite": 1,
    "astronomical": 1,
    "fossil": 1,
    "specimen": 1,
    "timelapse": 1,
    "comparison": 1,  # photo comparisons
    # Tier 2 — authentic scientific diagrams
    "diagram": 2,
    "map": 2,
    "geological_cross_section": 2,
    "chart": 2,
    # Tier 3 — public-domain / educational illustrations
    "illustration": 3,
    "document": 3,
    # Tier 4 — reconstructions
    "reconstruction": 4,
    "museum_reconstruction": 4,
    # Tier 5 — AI / synthetic (last resort)
    "animation": 5,
    "ai_image": 5,
    "ai_generated": 5,
    "generated": 5,
    "drawing": 5,
    "sketch": 5,
}

TIER_LABELS = {
    1: "authentic_photograph",
    2: "authentic_scientific_diagram",
    3: "public_domain_illustration",
    4: "museum_reconstruction",
    5: "ai_or_synthetic_last_resort",
}

# Visual types that count as "real evidence" for Reality QC
AUTHENTIC_PHOTO_TYPES = frozenset(
    {
        "photograph",
        "microscope",
        "histology",
        "medical_imaging",
        "satellite",
        "astronomical",
        "fossil",
        "specimen",
        "timelapse",
        "comparison",
    }
)

SYNTHETIC_TYPES = frozenset(
    {
        "ai_image",
        "ai_generated",
        "generated",
        "drawing",
        "sketch",
        "animation",
    }
)


def priority_rank(visual_type: str | None) -> int:
    """1 = best (photos), 5 = last resort (AI). Unknown types default to 3."""
    key = str(visual_type or "").strip().lower()
    return int(VISUAL_PRIORITY_RANK.get(key, 3))


def priority_boost(visual_type: str | None) -> float:
    """0–0.35 additive score boost for search ranking (photos win)."""
    rank = priority_rank(visual_type)
    return round(max(0.0, (5 - rank) * 0.07), 3)


def is_authentic_photo(visual_type: str | None) -> bool:
    return priority_rank(visual_type) == 1 or str(visual_type or "").lower() in AUTHENTIC_PHOTO_TYPES


def is_synthetic(visual_type: str | None) -> bool:
    return str(visual_type or "").lower() in SYNTHETIC_TYPES


def prefer_authentic(
    candidates: list[dict[str, Any]],
    *,
    limit: int = 8,
) -> list[dict[str, Any]]:
    """Stable sort: priority rank, then relevance/quality if present."""

    def _key(row: dict[str, Any]) -> tuple:
        vtype = row.get("visual_type") or row.get("type") or ""
        return (
            priority_rank(str(vtype)),
            -float(row.get("relevance") or row.get("quality_score") or 0),
            str(row.get("asset_id") or row.get("image_id") or ""),
        )

    return sorted(candidates, key=_key)[:limit]


def select_visual_source(
    *,
    authentic_hits: list[dict[str, Any]],
    diagram_hits: list[dict[str, Any]] | None = None,
    illustration_hits: list[dict[str, Any]] | None = None,
    reconstruction_hits: list[dict[str, Any]] | None = None,
    ai_hits: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Pick the highest-priority available visual. AI only if all higher tiers empty."""
    for tier, pool in (
        (1, authentic_hits),
        (2, diagram_hits or []),
        (3, illustration_hits or []),
        (4, reconstruction_hits or []),
        (5, ai_hits or []),
    ):
        if pool:
            best = prefer_authentic(pool, limit=1)[0]
            return {
                "ok": True,
                "tier": tier,
                "tier_label": TIER_LABELS[tier],
                "asset": best,
                "ai_fallback": tier == 5,
            }
    return {
        "ok": False,
        "tier": None,
        "tier_label": "none",
        "asset": None,
        "ai_fallback": False,
        "error": "no_visual_candidates",
    }
