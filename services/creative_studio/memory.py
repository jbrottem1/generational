"""Creative Memory — the studio's persistent creative knowledge.

Append-only JSON store (`data/creative_studio/memory.json`, same
convention as the analytics store) remembering characters, worlds,
brands, art styles, successful visual motifs, scene structures,
transitions, recurring themes, and creative assets across productions —
so every future production can recall what worked before.

Integration with Analytics (Agent 9) and the Optimization Laboratory
(Agent 13) is one-way and orchestrator-mediated: they read this store's
entries (JSON-safe dicts, MEMORY_ENTRY_FIELDS) and their recommendations
reach the studio through context keys (see guidance.py) — never through
engine-to-engine calls.

Tests isolate by constructing with `directory=` (or by swapping the
module `_DEFAULT_DIR`, mirroring services/analytics/store.py).
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

from core.log import get_logger, log_event

logger = get_logger(__name__)

_DEFAULT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "creative_studio",
)

_MEMORY_FILE = "memory.json"


class MemoryKind:
    """What a creative memory entry remembers. Additive-only."""

    CHARACTER = "character"
    WORLD = "world"
    BRAND = "brand"
    STYLE = "style"
    MOTIF = "motif"
    SCENE_STRUCTURE = "scene_structure"
    TRANSITION = "transition"
    THEME = "theme"
    ASSET = "asset"

    ALL = (
        CHARACTER, WORLD, BRAND, STYLE, MOTIF,
        SCENE_STRUCTURE, TRANSITION, THEME, ASSET,
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class CreativeMemory:
    """Append-only JSON store for creative knowledge."""

    def __init__(self, directory: str = "") -> None:
        self.directory = directory or _DEFAULT_DIR

    # ------------------------------------------------------------ plumbing

    def _path(self) -> str:
        return os.path.join(self.directory, _MEMORY_FILE)

    def _read(self) -> list:
        path = self._path()
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to read creative memory: %s", exc)
            return []

    def _write(self, entries: list) -> None:
        os.makedirs(self.directory, exist_ok=True)
        with open(self._path(), "w", encoding="utf-8") as file:
            json.dump(entries, file, indent=2)

    # -------------------------------------------------------------- entries

    def remember(self, kind: str, key: str, content: dict, project_id: str = "", brand_id: str = "") -> dict:
        """Append one memory entry (history is never overwritten)."""
        entry = {
            "entry_id": f"cmem_{uuid.uuid4().hex[:10]}",
            "kind": kind,
            "key": key,
            "content": dict(content),
            "project_id": project_id,
            "brand_id": brand_id,
            "created_at": _now_iso(),
        }
        entries = self._read()
        entries.append(entry)
        self._write(entries)
        log_event(logger, "creative_studio.memory_added", kind=kind, key=key)
        return entry

    def recall(self, kind: str = "", key: str = "", brand_id: str = "", limit: "int | None" = None) -> list:
        """Entries newest-first, optionally filtered."""
        entries = list(reversed(self._read()))
        if kind:
            entries = [e for e in entries if e.get("kind") == kind]
        if key:
            entries = [e for e in entries if e.get("key") == key]
        if brand_id:
            entries = [e for e in entries if e.get("brand_id") == brand_id]
        return entries[:limit] if limit else entries

    def latest(self, kind: str, key: str) -> "dict | None":
        """The most recent entry for one kind + key (recall by identity)."""
        entries = self.recall(kind=kind, key=key, limit=1)
        return entries[0] if entries else None

    def entry_count(self) -> int:
        return len(self._read())


def get_creative_memory() -> CreativeMemory:
    """A memory bound to the current default directory (test-swappable)."""
    return CreativeMemory()


def record_production(package: dict, item: "dict | None" = None) -> "list[dict]":
    """Remember what one production used — characters, world, style, the
    scene structure, transitions, and the theme. Returns the entries.
    A broken store never breaks the studio."""
    item = item or {}
    memory = get_creative_memory()
    entries = []
    try:
        project_id = str(package.get("project_id", ""))
        brand_id = str(item.get("brand_id", ""))
        blueprint = package.get("creative_blueprint", {})
        storyboard = package.get("storyboard", [])

        for character in package.get("character_plan", {}).get("cast", []):
            entries.append(
                memory.remember(
                    MemoryKind.CHARACTER, character.get("character_id", ""),
                    {"name": character.get("name", ""), "visual_signature": character.get("visual_signature", "")},
                    project_id, brand_id,
                )
            )

        world = package.get("world_plan", {}).get("world", {})
        if world.get("world_id"):
            entries.append(
                memory.remember(
                    MemoryKind.WORLD, world["world_id"],
                    {"label": world.get("label", ""), "mood": world.get("mood", "")},
                    project_id, brand_id,
                )
            )

        if blueprint.get("visual_style"):
            entries.append(
                memory.remember(
                    MemoryKind.STYLE, blueprint["visual_style"],
                    {"production_type": blueprint.get("production_type", "")},
                    project_id, brand_id,
                )
            )

        entries.append(
            memory.remember(
                MemoryKind.SCENE_STRUCTURE,
                blueprint.get("storytelling_style", "narrative_arc"),
                {"purposes": [scene.get("purpose", "") for scene in storyboard]},
                project_id, brand_id,
            )
        )

        transitions = sorted(
            {
                scene.get("transitions", {}).get("out", "")
                for scene in storyboard
                if scene.get("transitions", {}).get("out")
            }
        )
        if transitions:
            entries.append(
                memory.remember(
                    MemoryKind.TRANSITION, blueprint.get("visual_style", ""),
                    {"transitions": transitions}, project_id, brand_id,
                )
            )

        if item.get("topic"):
            entries.append(
                memory.remember(
                    MemoryKind.THEME, str(item.get("niche", "general")),
                    {"topic": str(item["topic"])}, project_id, brand_id,
                )
            )
    except Exception as exc:  # noqa: BLE001 - memory must never break design
        log_event(logger, "creative_studio.memory_write_failed", level=30, error=str(exc)[:120])
    return entries
