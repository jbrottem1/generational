"""Self-improvement — recommend before implementing."""

from __future__ import annotations

from typing import Any


def analyze_improvements(productions: list[dict[str, Any]] | None = None) -> list[str]:
    """Ranked recommendations — quality and reliability over feature creep."""
    productions = productions or []
    awaiting = sum(
        1
        for p in productions
        if p.get("local_render_status") in ("ready_to_render", "awaiting_local_render", "pending")
    )
    failed = sum(1 for p in productions if p.get("local_render_status") == "failed")
    recs: list[str] = []

    if awaiting > 0:
        recs.append(
            f"Clear render backlog ({awaiting} ready/pending) — run local render on Mac."
        )
    if failed:
        recs.append(
            f"Repair {failed} failed verification(s) before new productions — check manifest verification blocks."
        )

    recs.extend(
        [
            "Legacy export paths migrated to ~/Desktop/AI Start-Up/Videos/{Category}/ — archive Test run 2 generational separately.",
            "Add phoneme lip-sync driver to reduce re-render cycles on local workstation.",
            "Batch Intelligence layer: SEO + scientific verification in single PRODUCTION_BRIEF pass.",
            "Expand asset_registry seed entries for characters, motion templates, and whiteboard strokes.",
            "Automate post-production READY_TO_PUBLISH packaging after verified export (metadata + captions).",
        ]
    )
    return recs[:5]
