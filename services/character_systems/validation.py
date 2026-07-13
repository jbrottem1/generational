"""Consistency validation rules for Generational characters (Agent 26)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.animation.fluid_motion import GESTURE_POSES
from services.animation.stick_figure import StickFigureSpec

REPO_ROOT = Path(__file__).resolve().parents[2]
UNIVERSE_CHARACTERS = REPO_ROOT / "data" / "universe" / "characters"
CHARACTER_SYSTEMS_DIR = REPO_ROOT / "data" / "character_systems"
CHARACTER_SYSTEMS_REGISTRY = CHARACTER_SYSTEMS_DIR / "registry.json"

PROFESSOR_CHARACTER_ID = "CHAR-PROFESSOR-001"

PROFESSOR_LOCKED_PALETTE = {
    "outline": (0, 0, 0, 255),
    "face_fill": (255, 255, 255, 255),
}

# Gen Foundation attire lock — lab coat forbidden without version bump.
PROFESSOR_LOCKED_ATTIRE = "none"
FORBIDDEN_FOUNDATION_ATTIRE: frozenset[str] = frozenset({"lab_coat", "coat"})

# Wave spam + slapstick react are forbidden in professor / Foundation mode.
FORBIDDEN_PROFESSOR_GESTURES: frozenset[str] = frozenset({"wave", "react"})

PROFESSOR_PREFERRED_GESTURES: frozenset[str] = frozenset(
    {"idle", "write", "point", "think", "present", "push"}
)

HEAD_RATIO_TOLERANCE = 0.01


class ConsistencyError(ValueError):
    """Raised when a character fails Character Systems consistency rules."""


def _as_rgba(value: Any) -> tuple[int, int, int, int] | None:
    if value is None:
        return None
    if isinstance(value, tuple) and len(value) >= 3:
        r, g, b = int(value[0]), int(value[1]), int(value[2])
        a = int(value[3]) if len(value) > 3 else 255
        return (r, g, b, a)
    if isinstance(value, list) and len(value) >= 3:
        r, g, b = int(value[0]), int(value[1]), int(value[2])
        a = int(value[3]) if len(value) > 3 else 255
        return (r, g, b, a)
    if isinstance(value, str) and value.startswith("#") and len(value) in (7, 9):
        r = int(value[1:3], 16)
        g = int(value[3:5], 16)
        b = int(value[5:7], 16)
        a = int(value[7:9], 16) if len(value) == 9 else 255
        return (r, g, b, a)
    return None


def load_character_systems_registry(path: Path | None = None) -> dict[str, Any]:
    p = path or CHARACTER_SYSTEMS_REGISTRY
    return json.loads(p.read_text(encoding="utf-8"))


def load_character(character_id: str, *, root: Path | None = None) -> dict[str, Any]:
    """Load CHARACTER folder assets for a character_id."""
    base = (root or UNIVERSE_CHARACTERS) / character_id
    if not base.is_dir():
        raise FileNotFoundError(f"Character folder not found: {base}")

    design_path = base / "design_spec.json"
    if not design_path.is_file():
        raise FileNotFoundError(f"Missing design_spec.json for {character_id}")

    design = json.loads(design_path.read_text(encoding="utf-8"))
    payload: dict[str, Any] = {
        "character_id": character_id,
        "path": str(base),
        "design_spec": design,
    }

    for name in ("expression_sheet.json", "gesture_sheet.json"):
        fp = base / name
        if fp.is_file():
            payload[name.replace(".json", "")] = json.loads(fp.read_text(encoding="utf-8"))

    char_md = base / "CHARACTER.md"
    if char_md.is_file():
        payload["character_md"] = char_md.read_text(encoding="utf-8")

    return payload


def validate_palette(
    design_or_spec: dict[str, Any] | StickFigureSpec,
    *,
    character_id: str | None = None,
) -> list[str]:
    """Return list of palette error strings (empty if ok)."""
    errors: list[str] = []
    cid = character_id
    outline = None
    face = None

    if isinstance(design_or_spec, StickFigureSpec):
        cid = cid or design_or_spec.character_id
        outline = design_or_spec.outline
        face = design_or_spec.face_fill
    else:
        cid = cid or str(design_or_spec.get("character_id") or "")
        stick = design_or_spec.get("stick_figure") or {}
        silhouette = design_or_spec.get("silhouette") or {}
        outline = _as_rgba(stick.get("outline") or design_or_spec.get("outline") or silhouette.get("outline_color"))
        face = _as_rgba(stick.get("face_fill") or design_or_spec.get("face_fill") or silhouette.get("fill_color"))

    if cid == PROFESSOR_CHARACTER_ID:
        locked_o = PROFESSOR_LOCKED_PALETTE["outline"]
        locked_f = PROFESSOR_LOCKED_PALETTE["face_fill"]
        if outline != locked_o:
            errors.append(f"palette.outline must be {locked_o}, got {outline}")
        if face != locked_f:
            errors.append(f"palette.face_fill must be {locked_f}, got {face}")
    return errors


def validate_attire(
    design_or_spec: dict[str, Any] | StickFigureSpec,
    *,
    character_id: str | None = None,
) -> list[str]:
    """Flag lab_coat attire as inconsistency for Gen Foundation productions."""
    errors: list[str] = []
    cid = character_id
    attire: str | None = None

    if isinstance(design_or_spec, StickFigureSpec):
        cid = cid or design_or_spec.character_id
        attire = str(design_or_spec.attire or "none")
    else:
        cid = cid or str(design_or_spec.get("character_id") or "")
        stick = design_or_spec.get("stick_figure") or {}
        attire = design_or_spec.get("attire") or stick.get("attire")
        if attire is not None:
            attire = str(attire)

    if cid == PROFESSOR_CHARACTER_ID:
        resolved = (attire or PROFESSOR_LOCKED_ATTIRE).strip().lower()
        if resolved in FORBIDDEN_FOUNDATION_ATTIRE:
            errors.append(
                f"attire '{resolved}' forbidden for {PROFESSOR_CHARACTER_ID} Foundation "
                f"(locked attire={PROFESSOR_LOCKED_ATTIRE!r}; lab coat needs version bump)"
            )
        elif attire is not None and resolved != PROFESSOR_LOCKED_ATTIRE:
            errors.append(
                f"attire must be {PROFESSOR_LOCKED_ATTIRE!r} for Gen Foundation, got {attire!r}"
            )
    return errors


def validate_proportions(
    design_or_spec: dict[str, Any] | StickFigureSpec,
    *,
    character_id: str | None = None,
) -> list[str]:
    """Return proportion error strings for locked characters."""
    errors: list[str] = []
    cid = character_id
    stroke: float | None = None
    head_ratio: float | None = None

    if isinstance(design_or_spec, StickFigureSpec):
        cid = cid or design_or_spec.character_id
        stroke = float(design_or_spec.stroke)
        head_ratio = float(design_or_spec.head_ratio)
    else:
        cid = cid or str(design_or_spec.get("character_id") or "")
        stick = design_or_spec.get("stick_figure") or {}
        props = design_or_spec.get("proportions") or {}
        silhouette = design_or_spec.get("silhouette") or {}
        if "stroke" in stick:
            stroke = float(stick["stroke"])
        elif "stroke" in design_or_spec:
            stroke = float(design_or_spec["stroke"])
        elif "stroke" in props:
            stroke = float(props["stroke"])
        if "head_ratio" in stick:
            head_ratio = float(stick["head_ratio"])
        elif "head_ratio" in design_or_spec:
            head_ratio = float(design_or_spec["head_ratio"])
        elif "head_ratio_of_height" in silhouette:
            head_ratio = float(silhouette["head_ratio_of_height"])
        elif "head_diameter" in props:
            head_ratio = float(props["head_diameter"])

    if cid == PROFESSOR_CHARACTER_ID:
        if stroke is None or int(stroke) != 7:
            errors.append(f"proportions.stroke must be 7, got {stroke}")
        if head_ratio is None or abs(float(head_ratio) - 0.34) > HEAD_RATIO_TOLERANCE:
            errors.append(f"proportions.head_ratio must be 0.34±{HEAD_RATIO_TOLERANCE}, got {head_ratio}")
    return errors


def validate_gesture_for_character(
    gesture: str,
    *,
    character_id: str,
    professor_mode: bool = False,
) -> list[str]:
    """Reject forbidden gestures (e.g. wave spam) for professor mode."""
    errors: list[str] = []
    g = (gesture or "idle").lower().strip()
    is_professor = professor_mode or character_id == PROFESSOR_CHARACTER_ID

    if is_professor and g in FORBIDDEN_PROFESSOR_GESTURES:
        errors.append(
            f"forbidden gesture '{g}' for professor mode ({character_id}); "
            f"wave spam / slapstick react not allowed"
        )

    # Unknown keys that are neither locked code poses nor planned registry slots:
    # planned keys are allowed as names but should not claim code backing.
    registry = load_character_systems_registry()
    known = {str(item.get("gesture_key") or "").lower() for item in registry.get("gestures") or []}
    if g not in GESTURE_POSES and g not in known:
        errors.append(f"unknown gesture '{g}' — not in GESTURE_POSES or character_systems registry")
    return errors


def validate_production_character(
    character: dict[str, Any] | StickFigureSpec | str,
    *,
    gestures: list[str] | None = None,
    professor_mode: bool | None = None,
) -> dict[str, Any]:
    """Validate a production character for consistency.

    Accepts character_id string, loaded character dict, or StickFigureSpec.
    Returns ``{"ok": bool, "character_id": str, "errors": [...], "warnings": [...]}``.
    """
    errors: list[str] = []
    warnings: list[str] = []
    design: dict[str, Any] | StickFigureSpec
    cid: str

    if isinstance(character, str):
        loaded = load_character(character)
        cid = str(loaded.get("character_id") or character)
        design = loaded.get("design_spec") or {}
        if professor_mode is None and cid == PROFESSOR_CHARACTER_ID:
            professor_mode = True
    elif isinstance(character, StickFigureSpec):
        cid = character.character_id
        design = character
        if professor_mode is None and cid == PROFESSOR_CHARACTER_ID:
            professor_mode = True
    else:
        cid = str(character.get("character_id") or (character.get("design_spec") or {}).get("character_id") or "")
        design = character.get("design_spec") or character
        if professor_mode is None and cid == PROFESSOR_CHARACTER_ID:
            professor_mode = True

    if not cid:
        errors.append("character_id is required")
    elif isinstance(design, dict) and design.get("character_id") and design["character_id"] != cid:
        errors.append(
            f"character_id mismatch: folder/payload '{cid}' vs design_spec '{design['character_id']}'"
        )

    if cid == PROFESSOR_CHARACTER_ID:
        # Wrong id on StickFigureSpec defaults used as Gen
        if isinstance(design, StickFigureSpec) and design.character_id != PROFESSOR_CHARACTER_ID:
            errors.append(
                f"character_id must be {PROFESSOR_CHARACTER_ID} for Professor Gen, got {design.character_id}"
            )
        errors.extend(validate_palette(design, character_id=cid))
        errors.extend(validate_proportions(design, character_id=cid))
        errors.extend(validate_attire(design, character_id=cid))

        # Identity check: rejecting wrong id masquerading as professor production
        expected_name = None
        if isinstance(design, dict):
            expected_name = design.get("name") or design.get("short_name")
        elif isinstance(design, StickFigureSpec):
            expected_name = design.name
        if expected_name and expected_name not in ("Professor Gen", "Gen", "Generational Professor"):
            warnings.append(f"unexpected display name for Gen: {expected_name}")

    for g in gestures or []:
        errors.extend(
            validate_gesture_for_character(
                g,
                character_id=cid,
                professor_mode=bool(professor_mode),
            )
        )

    # Detect wave spam: more than one wave in a short gesture list for professor
    if professor_mode or cid == PROFESSOR_CHARACTER_ID:
        wave_count = sum(1 for g in (gestures or []) if (g or "").lower() == "wave")
        if wave_count >= 1:
            # Already flagged per-gesture; reinforce spam policy
            if wave_count > 1:
                errors.append(f"wave spam detected: {wave_count} wave gestures in professor mode")

    return {
        "ok": len(errors) == 0,
        "character_id": cid,
        "errors": errors,
        "warnings": warnings,
        "professor_mode": bool(professor_mode),
    }


def professor_stick_figure_spec() -> StickFigureSpec:
    """Canonical StickFigureSpec for Professor Gen."""
    return StickFigureSpec(
        character_id=PROFESSOR_CHARACTER_ID,
        name="Professor Gen",
        outline=PROFESSOR_LOCKED_PALETTE["outline"],
        face_fill=PROFESSOR_LOCKED_PALETTE["face_fill"],
        stroke=7,
        head_ratio=0.34,
        attire=PROFESSOR_LOCKED_ATTIRE,
    )
