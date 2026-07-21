"""Visual asset readiness — can we teach this with quality visuals?"""

from __future__ import annotations

from services.trends.models import Trend


_TOPIC_ASSET_HINTS = {
    "turtle": ["green_sea_turtle", "turtle_fossil"],
    "fossil": ["turtle_fossil"],
    "mimicry": ["hoverfly_lateral", "wasp_lateral"],
    "coral": ["coral_snake"],
    "brain": [],
    "cell": [],
    "dna": [],
    "space": [],
    "black hole": [],
}


def visual_asset_score(trend: Trend) -> float:
    """0–1 readiness based on Reality/Atlas catalog hits + category prior."""
    blob = f"{trend.topic} {' '.join(trend.keywords)}".lower()
    catalog_ids: set[str] = set()
    try:
        from services.reality.catalog import CATALOG_PATH
        import json

        if CATALOG_PATH.is_file():
            raw = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
            entries = raw if isinstance(raw, list) else raw.get("images") or raw.get("entries") or []
            for entry in entries:
                if isinstance(entry, dict):
                    catalog_ids.add(str(entry.get("image_id") or ""))
    except Exception:  # noqa: BLE001
        catalog_ids = set()

    hits = 0
    for needle, ids in _TOPIC_ASSET_HINTS.items():
        if needle in blob:
            hits += 1
            for image_id in ids:
                if image_id in catalog_ids:
                    hits += 2

    cat_prior = {
        "science": 0.72,
        "space": 0.78,
        "history": 0.65,
        "education": 0.60,
        "psychology": 0.55,
        "health": 0.58,
        "technology": 0.55,
        "news": 0.40,
        "general": 0.50,
    }.get(trend.category.lower(), 0.5)

    score = min(0.98, cat_prior + 0.08 * hits)
    return round(score, 3)
