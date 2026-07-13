"""Reality beat planner — map concepts to licensed images."""

from __future__ import annotations

from typing import Any

from services.reality.panel import RealityPanel

# Batesian benchmark lesson plans
BATESIAN_101_PANELS: list[RealityPanel] = [
    RealityPanel(
        layout="board_inset",
        start=0.08,
        end=0.38,
        image_ids=["hoverfly_lateral"],
        labels=["Real hoverfly"],
        title="Evidence",
    ),
    RealityPanel(
        layout="split_compare",
        start=0.38,
        end=0.72,
        image_ids=["wasp_lateral", "hoverfly_lateral"],
        labels=["Wasp (model)", "Hoverfly (mimic)"],
        tags=["MODEL · sting", "MIMIC · harmless"],
        title="Side-by-side",
        annotations=[
            {"kind": "label", "x": 0, "y": 0, "text": "", "start": 0.0},  # filled at render
        ],
    ),
]

CORAL_102_PANELS: list[RealityPanel] = [
    RealityPanel(
        layout="split_compare",
        start=0.18,
        end=0.78,
        image_ids=["coral_snake", "scarlet_kingsnake"],
        labels=["Coral snake", "Scarlet kingsnake"],
        tags=["DANGEROUS", "HARMLESS"],
        title="Which is venomous?",
    ),
]

BLUFFING_103_PANELS: list[RealityPanel] = [
    RealityPanel(
        layout="split_compare",
        start=0.16,
        end=0.48,
        image_ids=["wasp_lateral", "hoverfly_lateral"],
        labels=["Bee / wasp model", "Hoverfly mimic"],
        tags=["MODEL", "MIMIC"],
        title="False warning colors",
    ),
    RealityPanel(
        layout="split_compare",
        start=0.48,
        end=0.78,
        image_ids=["monarch_adult", "viceroy_adult"],
        labels=["Monarch", "Viceroy"],
        tags=["Complex case", "More than Batesian alone"],
        title="Revised science",
    ),
]

TURTLE_202_PANELS: list[RealityPanel] = [
    RealityPanel(
        layout="board_inset",
        start=0.10,
        end=0.28,
        image_ids=["green_sea_turtle"],
        labels=["Modern sea turtle"],
        title="Living turtle",
    ),
    RealityPanel(
        layout="split_compare",
        start=0.28,
        end=0.52,
        image_ids=["turtle_fossil", "green_sea_turtle"],
        labels=["Ancient fossil", "Today"],
        tags=["200+ Ma", "Evolved shell"],
        title="Deep time",
    ),
    RealityPanel(
        layout="board_inset",
        start=0.55,
        end=0.78,
        image_ids=["turtle_fossil"],
        labels=["Intermediate fossil form"],
        title="Fossil evidence",
    ),
]

PLANS: dict[str, list[RealityPanel]] = {
    "foundation_batesian_101": BATESIAN_101_PANELS,
    "foundation_coral_102": CORAL_102_PANELS,
    "foundation_bluffing_103": BLUFFING_103_PANELS,
    "foundation_v2_turtle_202": TURTLE_202_PANELS,
}


def plan_reality_beats(demo_id: str) -> list[RealityPanel]:
    return list(PLANS.get(demo_id) or [])


def plan_reality_for_concepts(concepts: list[str]) -> list[dict[str, Any]]:
    """Lightweight concept → image_id hints for scripts."""
    mapping = {
        "hoverfly": "hoverfly_lateral",
        "wasp": "wasp_lateral",
        "coral_snake": "coral_snake",
        "kingsnake": "scarlet_kingsnake",
        "monarch": "monarch_adult",
        "viceroy": "viceroy_adult",
        "turtle": "green_sea_turtle",
        "fossil": "turtle_fossil",
        "shell_evolution": "turtle_fossil",
    }
    out = []
    for c in concepts:
        key = c.lower().replace(" ", "_")
        if key in mapping:
            out.append({"concept": c, "image_id": mapping[key]})
    return out
