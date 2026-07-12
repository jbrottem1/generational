"""Self-improvement — recommend before implementing."""

from __future__ import annotations

from typing import Any


def analyze_improvements(productions: list[dict[str, Any]] | None = None) -> list[str]:
    """Ranked recommendations — quality and reliability over feature creep."""
    productions = productions or []
    awaiting = sum(1 for p in productions if p.get("local_render_status") == "awaiting_local_render")
    failed = sum(1 for p in productions if p.get("local_render_status") == "failed")
    recs: list[str] = []

    if awaiting > 0:
        recs.append(
            f"Clear render backlog ({awaiting} awaiting local render) — run `run_render_package.py` on Mac batch."
        )
    if failed:
        recs.append(
            f"Repair {failed} failed verification(s) before new productions — check manifest verification blocks."
        )

    recs.extend(
        [
            "Unify legacy export paths into Generational/Videos/{Domain} — migrate Test run 2 generational archive.",
            "Add phoneme lip-sync driver to reduce re-render cycles on local workstation.",
            "Batch Intelligence layer: SEO + scientific verification in single PRODUCTION_BRIEF pass.",
            "Expand asset_registry seed entries for characters, motion templates, and whiteboard strokes.",
            "Automate post-production READY_TO_PUBLISH packaging after verified export (metadata + captions).",
        ]
    )
    return recs[:5]
