"""Stage geometry — floors, walls, ceilings, openings, furniture, props."""

from __future__ import annotations

from typing import Any

from services.stage_world_simulation.models import GEOMETRY_ELEMENTS


def build_geometry(definition: dict[str, Any], *, world_id: str) -> dict[str, Any]:
    dims = definition.get("dimensions_m") or {"x": 12.0, "y": 3.5, "z": 10.0}
    x, y, z = float(dims["x"]), float(dims["y"]), float(dims["z"])
    outdoor = bool(definition.get("outdoor"))

    floors = [
        {
            "id": "main_floor",
            "bounds": [[-x / 2, 0, -z / 2], [x / 2, 0, z / 2]],
            "walkable": True,
            "material": "exterior_ground" if outdoor else "interior_floor",
        }
    ]
    walls = [] if outdoor else [
        {"id": "wall_n", "plane": "north", "openings": ["window_n"] if not outdoor else []},
        {"id": "wall_s", "plane": "south", "openings": ["door_main"]},
        {"id": "wall_e", "plane": "east", "openings": []},
        {"id": "wall_w", "plane": "west", "openings": ["window_w"]},
    ]
    ceilings = [] if outdoor else [
        {"id": "main_ceiling", "height_m": y, "material": "acoustic_or_structural"}
    ]
    doors = [
        {
            "id": "door_main",
            "position": [0.0, 0.0, -z / 2 + 0.1],
            "swing": "inward",
            "interactable": True,
        }
    ]
    windows = [] if outdoor else [
        {"id": "window_n", "position": [0.0, y * 0.55, z / 2 - 0.05]},
        {"id": "window_w", "position": [-x / 2 + 0.05, y * 0.55, 0.0]},
    ]

    furniture = []
    for i, name in enumerate(definition.get("furniture") or []):
        furniture.append(
            {
                "id": f"furn_{name}_{i}",
                "type": _normalize_prop(name),
                "position": _slot(i, x, z, lane=0.0),
                "collision": True,
                "navigable_around": True,
            }
        )

    props = []
    for i, name in enumerate(definition.get("props") or []):
        props.append(
            {
                "id": f"prop_{name}_{i}",
                "type": _normalize_prop(name),
                "position": _slot(i, x, z, lane=1.2),
                "collision": name.lower() not in {"hologram", "steam"},
                "interactable": True,
            }
        )

    return {
        "world_id": world_id,
        "elements_required": list(GEOMETRY_ELEMENTS),
        "dimensions_m": {"x": x, "y": y, "z": z},
        "floor": floors,
        "walls": walls,
        "ceilings": ceilings,
        "doors": doors,
        "windows": windows,
        "furniture": furniture,
        "props": props,
        "not_a_flat_image": True,
        "explorable_volume": True,
        "persistent": True,
    }


def _normalize_prop(name: str) -> str:
    n = str(name).lower()
    for key in (
        "chair",
        "desk",
        "microscope",
        "whiteboard",
        "door",
        "hologram",
        "console",
        "bookshelf",
        "bench",
        "exhibit",
    ):
        if key in n:
            return key
    if "seat" in n or "stool" in n:
        return "chair"
    if "screen" in n or "monitor" in n:
        return "console"
    return n.replace(" ", "_")


def _slot(i: int, x: float, z: float, *, lane: float) -> list[float]:
    col = i % 3
    row = i // 3
    return [
        -x * 0.25 + col * (x * 0.2),
        0.0,
        -z * 0.15 + row * 1.4 + lane,
    ]
