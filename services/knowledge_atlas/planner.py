"""Knowledge Atlas visual evidence planner — script concepts → assets + layouts."""

from __future__ import annotations

from typing import Any

from services.knowledge_atlas.catalog import get_asset, load_atlas
from services.knowledge_atlas.search import search_visuals


def extract_concepts_from_beats(beats: list[dict[str, Any]], main_concept: str = "") -> list[str]:
    """Light concept extraction from lesson beats."""
    concepts: list[str] = []
    if main_concept:
        concepts.extend(main_concept.lower().replace(":", " ").split())
    keywords = (
        "hoverfly",
        "wasp",
        "mimic",
        "model",
        "batesian",
        "coral",
        "kingsnake",
        "snake",
        "monarch",
        "viceroy",
        "butterfly",
        "warning",
        "predator",
        "evolution",
        "arms",
        "race",
    )
    text = " ".join(str(b.get("text") or "") for b in beats).lower()
    for kw in keywords:
        if kw in text and kw not in concepts:
            concepts.append(kw)
    return list(dict.fromkeys(concepts))


def plan_visual_evidence(
    *,
    main_concept: str,
    beats: list[dict[str, Any]] | None = None,
    demo_id: str | None = None,
    domain: str = "biology",
) -> dict[str, Any]:
    """Plan authentic visual evidence for a lesson."""
    beats = beats or []
    concepts = extract_concepts_from_beats(beats, main_concept)

    # Demo-linked assets take priority
    demo_assets = []
    if demo_id:
        for asset in load_atlas().values():
            if demo_id in asset.demo_ids:
                demo_assets.append(asset.asset_id)

    search_hits = search_visuals(query=main_concept, concepts=concepts, domain=domain, limit=8)
    recommended_ids = list(dict.fromkeys(demo_assets + [h["asset_id"] for h in search_hits]))

    panels: list[dict[str, Any]] = []
    if demo_id == "foundation_batesian_101":
        panels = _panel_plan_batesian_101(recommended_ids)
    elif demo_id == "foundation_coral_102":
        panels = _panel_plan_coral_102(recommended_ids)
    elif demo_id == "foundation_bluffing_103":
        panels = _panel_plan_bluffing_103(recommended_ids)
    elif len(recommended_ids) >= 2:
        panels = [
            {
                "layout": "split_compare",
                "asset_ids": recommended_ids[:2],
                "title": "Compare",
            }
        ]
    elif recommended_ids:
        panels = [
            {
                "layout": "evidence_tray",
                "asset_ids": [recommended_ids[0]],
                "title": "Evidence",
            }
        ]

    return {
        "main_concept": main_concept,
        "concepts": concepts,
        "domain": domain,
        "demo_id": demo_id,
        "recommended_asset_ids": recommended_ids,
        "panels": panels,
        "search_hits": search_hits,
    }


def _panel_plan_batesian_101(ids: list[str]) -> list[dict[str, Any]]:
    hover = _pick(ids, "hoverfly_lateral")
    wasp = _pick(ids, "wasp_lateral")
    panels = []
    if hover:
        panels.append({"layout": "board_inset", "asset_ids": [hover], "start": 0.08, "end": 0.38})
    if wasp and hover:
        panels.append(
            {
                "layout": "split_compare",
                "asset_ids": [wasp, hover],
                "start": 0.38,
                "end": 0.72,
                "title": "Model vs mimic",
            }
        )
    return panels


def _panel_plan_coral_102(ids: list[str]) -> list[dict[str, Any]]:
    coral = _pick(ids, "coral_snake")
    king = _pick(ids, "scarlet_kingsnake")
    if coral and king:
        return [
            {
                "layout": "split_compare",
                "asset_ids": [coral, king],
                "start": 0.18,
                "end": 0.78,
                "title": "Which is venomous?",
            }
        ]
    return []


def _panel_plan_bluffing_103(ids: list[str]) -> list[dict[str, Any]]:
    wasp = _pick(ids, "wasp_lateral")
    hover = _pick(ids, "hoverfly_lateral")
    mon = _pick(ids, "monarch_adult")
    vic = _pick(ids, "viceroy_adult")
    panels = []
    if wasp and hover:
        panels.append(
            {
                "layout": "split_compare",
                "asset_ids": [wasp, hover],
                "start": 0.16,
                "end": 0.48,
                "title": "False warning colors",
            }
        )
    if mon and vic:
        panels.append(
            {
                "layout": "split_compare",
                "asset_ids": [mon, vic],
                "start": 0.48,
                "end": 0.78,
                "title": "Revised science",
            }
        )
    return panels


def _pick(ids: list[str], asset_id: str) -> str | None:
    if asset_id in ids:
        return asset_id
    if get_asset(asset_id):
        return asset_id
    return None
