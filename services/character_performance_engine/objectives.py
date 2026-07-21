"""Scene objectives — every performance answers why the actor moves."""

from __future__ import annotations

from typing import Any


_OBJECTIVE_HINTS: list[tuple[str, tuple[str, ...]]] = [
    ("demonstrate_equipment", ("show", "equipment", "microscope", "display", "tool", "machine")),
    ("walk_and_explain", ("walk", "explain", "because", "means", "how", "why")),
    ("point_to_evidence", ("point", "look", "see", "evidence", "hologram", "screen")),
    ("care_for_patient", ("patient", "care", "heal", "safe", "reassure")),
    ("open_space", ("enter", "door", "arrive", "leave", "exit")),
    ("celebrate_discovery", ("amazing", "discover", "wonder", "celebrate")),
]


def infer_objective(narration: str, *, expression: str = "", scene: dict[str, Any] | None = None) -> dict[str, Any]:
    text = f"{narration} {expression} {(scene or {}).get('purpose') or ''}".lower()
    for name, keys in _OBJECTIVE_HINTS:
        if any(k in text for k in keys):
            return {
                "id": name,
                "statement": _statement(name, narration),
                "must_move": True,
                "dramatic_hold_allowed": False,
            }
    chunk = (narration or "").split(".")[0].strip()
    if len(chunk) > 100:
        chunk = chunk[:97] + "..."
    return {
        "id": "communicate_idea_in_space",
        "statement": chunk or f"Communicate {expression or 'idea'} while occupying the world",
        "must_move": True,
        "dramatic_hold_allowed": False,
    }


def _statement(name: str, narration: str) -> str:
    lead = (narration or "").split(".")[0].strip()
    if lead and len(lead) < 120:
        return lead
    return name.replace("_", " ")
