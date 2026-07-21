"""Narration → entity / world / object intent helpers."""

from __future__ import annotations

import re
from typing import Any

from services.animation_engine.models import OBJECT_ANIM_HINTS, WORLD_ENV_TYPES

_PERSON_WORDS = (
    "scientist",
    "researcher",
    "firefighter",
    "doctor",
    "teacher",
    "explorer",
    "sailor",
    "astronaut",
    "king",
    "queen",
    "warrior",
    "farmer",
    "child",
    "woman",
    "man",
    "person",
    "people",
    "figure",
    "historian",
    "irish",
    "celt",
    "leprechaun",
    "fairy",
    "creature",
    "animal",
    "bird",
    "fish",
    "octopus",
    "turtle",
    "bee",
    "human",
)

_HISTORICAL = (
    "einstein",
    "newton",
    "darwin",
    "curie",
    "galileo",
    "tesla",
    "shakespeare",
    "napoleon",
    "cleopatra",
)


def narration_text(scene: dict[str, Any]) -> str:
    return str(
        scene.get("narration")
        or scene.get("voiceover")
        or scene.get("script")
        or scene.get("text")
        or ""
    ).strip()


def detect_characters(scene: dict[str, Any], *, topic: str = "") -> list[dict[str, Any]]:
    """Whenever narration references a person/creature/historical figure."""
    text = f"{narration_text(scene)} {topic} {scene.get('subject') or ''}".lower()
    found: list[dict[str, Any]] = []
    for name in _HISTORICAL:
        if name in text:
            found.append({"name": name.title(), "kind": "historical_figure", "source": "narration"})
    for word in _PERSON_WORDS:
        if re.search(rf"\b{re.escape(word)}\w*\b", text):
            found.append({"name": word, "kind": "character", "source": "keyword"})
    # Dedupe by name
    seen: set[str] = set()
    out = []
    for row in found:
        key = str(row["name"]).lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out[:4]


def detect_world_type(candidate: dict[str, Any], scene: dict[str, Any], *, topic: str = "") -> str:
    blob = " ".join(
        [
            topic,
            narration_text(scene),
            str(scene.get("visual_description") or ""),
            str((candidate.get("world_package") or {}).get("world_type") or ""),
            str((candidate.get("world_package") or {}).get("theme") or ""),
            str(candidate.get("world_type") or ""),
        ]
    ).lower()
    mapping = [
        ("forest", ("forest", "wood", "tree", "jungle")),
        ("ocean", ("ocean", "sea", "wave", "marine", "reef")),
        ("city", ("city", "urban", "street", "traffic", "skyline")),
        ("laboratory", ("lab", "laboratory", "microscope", "experiment")),
        ("space", ("space", "planet", "galaxy", "nebula", "orbit", "black hole")),
        ("countryside", ("ireland", "irish", "countryside", "farm", "field", "suburban", "hydrant")),
    ]
    for env, keys in mapping:
        if any(k in blob for k in keys):
            return env
    return "generic" if "generic" in WORLD_ENV_TYPES else WORLD_ENV_TYPES[-1]


def detect_object_animations(scene: dict[str, Any], *, topic: str = "") -> list[dict[str, Any]]:
    text = f"{narration_text(scene)} {topic} {scene.get('subject') or ''}".lower()
    out: list[dict[str, Any]] = []
    for key, anims in OBJECT_ANIM_HINTS.items():
        if key in text:
            out.append({"object": key, "animations": list(anims), "reason": f"Narration discusses {key}"})
    return out


def muted_comprehension_beat(scene: dict[str, Any]) -> str:
    """What a muted viewer should still understand visually."""
    purpose = str(scene.get("purpose") or "story_beat")
    subject = str(scene.get("subject") or scene.get("viewer_understanding") or "the idea")
    return f"Show {subject} through visible motion so purpose={purpose} reads without audio."
