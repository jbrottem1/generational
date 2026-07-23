"""V1 Launch Pilot — 25 educational briefs across six categories.

Composes topics from the Validation Program catalog — no new content engines.
"""

from __future__ import annotations

from typing import Any

from services.validation_program.catalog import build_validation_catalog

# Mission categories → validation catalog category keys
LAUNCH_CATEGORIES: tuple[str, ...] = (
    "biology",
    "artificial_intelligence",
    "astronomy",  # Space
    "physics",
    "psychology",
    "medicine",
)

# Per-category allotment sums to 25
_ALLOTMENT: dict[str, int] = {
    "biology": 5,
    "artificial_intelligence": 4,
    "astronomy": 4,
    "physics": 4,
    "psychology": 4,
    "medicine": 4,
}


def build_pilot_catalog() -> list[dict[str, Any]]:
    """Return exactly 25 launch pilot briefs with launch_id keys."""
    full = build_validation_catalog()
    by_cat: dict[str, list[dict[str, Any]]] = {c: [] for c in LAUNCH_CATEGORIES}
    for row in full:
        cat = row.get("category")
        if cat in by_cat:
            by_cat[cat].append(row)

    pilot: list[dict[str, Any]] = []
    idx = 0
    for cat in LAUNCH_CATEGORIES:
        need = _ALLOTMENT[cat]
        for row in by_cat[cat][:need]:
            idx += 1
            pilot.append(
                {
                    **row,
                    "launch_id": f"launch_{idx:02d}_{cat}",
                    "launch_category": cat,
                    "launch_label": {
                        "biology": "Biology",
                        "artificial_intelligence": "AI",
                        "astronomy": "Space",
                        "physics": "Physics",
                        "psychology": "Psychology",
                        "medicine": "Medicine",
                    }.get(cat, cat),
                }
            )
    assert len(pilot) == 25, f"expected 25 pilots, got {len(pilot)}"
    return pilot


def filter_pilot(*, limit: int | None = None, offset: int = 0, categories: list[str] | None = None) -> list[dict[str, Any]]:
    rows = build_pilot_catalog()
    if categories:
        wanted = {c.lower().replace(" ", "_") for c in categories}
        # accept aliases
        aliases = {"ai": "artificial_intelligence", "space": "astronomy"}
        wanted = {aliases.get(c, c) for c in wanted}
        rows = [r for r in rows if r["launch_category"] in wanted]
    if offset:
        rows = rows[offset:]
    if limit is not None:
        rows = rows[: max(0, int(limit))]
    return rows
