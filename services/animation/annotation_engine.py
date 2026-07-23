"""Semantic annotation engine — every mark teaches something intentional.

Before drawing an arrow/circle/highlight:
1. What object is discussed? (semantic target required)
2. Where is it (resolved bbox)?
3. Is it visible now?
4. What is the teaching purpose? (narration_cue required)
5. Will another annotation of the same type interfere?

Annotations fade in while discussed and fade out when the beat ends.
Max simultaneous: one arrow, one circle, one highlight, one label.
Free-floating coordinates are a fallback only when explicitly allowed.
Decorative / random markings are never drawn.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable

from PIL import Image, ImageDraw

from services.animation.layout_engine import (
    BoardLayoutResult,
    TextBox,
    keyword_bbox_lookup,
    visibility_envelope,
)


@dataclass
class SemanticTarget:
    """Resolved educational focus region."""

    kind: str  # keyword | panel | shell_stage | board | custom
    rect: tuple[int, int, int, int]
    label: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticAnnotation:
    """Narration-tied annotation with optional semantic target.

    ``target`` examples:
      - ``keyword:Gradual shell``
      - ``panel:0`` / ``panel:living`` / ``panel:fossil``
      - ``shell:0`` / ``shell:1`` / ``shell:2``
      - ``board``
    """

    kind: str  # point | tap | underline | circle | trace | highlight
    start: float
    end: float
    target: str = ""
    # Fallback normalized coords (used only if target cannot resolve)
    x0: float = 0.55
    y0: float = 0.30
    x1: float = 0.75
    y1: float = 0.45
    color: tuple[int, int, int] = (210, 45, 35)
    narration_cue: str = ""
    extras: dict[str, Any] = field(default_factory=dict)


def parse_target(target: str) -> tuple[str, str]:
    raw = (target or "").strip()
    if not raw:
        return "", ""
    if ":" in raw:
        kind, rest = raw.split(":", 1)
        return kind.strip().lower(), rest.strip()
    return raw.lower(), ""


def resolve_target(
    target: str,
    *,
    canvas_size: tuple[int, int],
    board_layout: BoardLayoutResult | None = None,
    board_rect: tuple[int, int, int, int] | None = None,
    panel_slots: dict[str, tuple[int, int, int, int]] | None = None,
    shell_stages: list[tuple[int, int, int, int]] | None = None,
) -> SemanticTarget | None:
    """Map a semantic target string to a pixel rect, or None if not visible."""
    kind, rest = parse_target(target)
    w, h = canvas_size
    if kind in ("", "none"):
        return None
    if kind == "board" and board_rect:
        return SemanticTarget("board", board_rect, label="board")
    if kind == "keyword" and board_layout is not None and board_rect is not None:
        bbox = keyword_bbox_lookup(board_layout, rest, board_rect)
        if bbox:
            return SemanticTarget("keyword", bbox, label=rest)
        return None
    if kind == "panel" and panel_slots:
        key = rest if rest in panel_slots else None
        if key is None and rest.isdigit():
            keys = sorted(panel_slots.keys())
            idx = int(rest)
            key = keys[idx] if 0 <= idx < len(keys) else None
        if key and key in panel_slots:
            return SemanticTarget("panel", panel_slots[key], label=key)
        return None
    if kind == "shell" and shell_stages:
        try:
            idx = int(rest)
        except ValueError:
            idx = 0
        if 0 <= idx < len(shell_stages):
            return SemanticTarget("shell_stage", shell_stages[idx], label=f"stage_{idx}")
        return None
    # Unknown — no silent free placement
    return None


def _fade_alpha(p: float, start: float, end: float) -> float:
    return visibility_envelope(p, start, end, fade_in=0.025, fade_out=0.045)


def _blend(color: tuple[int, int, int], alpha: float, bg: tuple[int, int, int] = (255, 255, 255)) -> tuple[int, int, int]:
    a = max(0.0, min(1.0, alpha))
    return tuple(int(c * a + bg[i] * (1 - a)) for i, c in enumerate(color))  # type: ignore[return-value]


def _rect_center(rect: tuple[int, int, int, int]) -> tuple[int, int]:
    return (rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2


def _approach_point(
    rect: tuple[int, int, int, int],
    *,
    from_left: bool = True,
) -> tuple[tuple[int, int], tuple[int, int]]:
    """Return (origin, tip) for an arrow aimed at the rect."""
    cx, cy = _rect_center(rect)
    if from_left:
        origin = (rect[0] - 36, cy + 24)
        tip = (rect[0] + 8, cy)
    else:
        origin = (rect[2] + 36, cy + 24)
        tip = (rect[2] - 8, cy)
    return origin, tip


def draw_semantic_annotations(
    canvas: Image.Image,
    annotations: list[SemanticAnnotation],
    p: float,
    *,
    board_layout: BoardLayoutResult | None = None,
    board_rect: tuple[int, int, int, int] | None = None,
    panel_slots: dict[str, tuple[int, int, int, int]] | None = None,
    shell_stages: list[tuple[int, int, int, int]] | None = None,
    allow_fallback_coords: bool = False,
    require_teaching_purpose: bool = True,
) -> list[dict[str, Any]]:
    """Draw narration-tied annotations. Returns per-annotation QC records.

    Production rules (permanent):
    - Every annotation needs a semantic target AND a narration_cue (teaching purpose)
    - Fade in while discussed; fade out when the beat ends
    - At most one arrow, one circle, one highlight, one label simultaneously
    - Never draw decorative / random geometry
    """
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    records: list[dict[str, Any]] = []

    # Collect visible annotations with purpose/target gates
    candidates: list[tuple[float, SemanticAnnotation]] = []
    for ann in annotations:
        alpha = _fade_alpha(p, ann.start, ann.end)
        if alpha <= 0.05:
            continue
        if require_teaching_purpose and not str(ann.narration_cue or "").strip():
            records.append(
                {
                    "kind": ann.kind,
                    "target": ann.target,
                    "drawn": False,
                    "reason": "missing_teaching_purpose",
                    "narration_cue": ann.narration_cue,
                }
            )
            continue
        if not str(ann.target or "").strip() and not allow_fallback_coords:
            records.append(
                {
                    "kind": ann.kind,
                    "target": ann.target,
                    "drawn": False,
                    "reason": "missing_semantic_target",
                    "narration_cue": ann.narration_cue,
                }
            )
            continue
        candidates.append((alpha, ann))

    if not candidates:
        return records

    # Cap: one per type family (arrow / circle / highlight / label)
    family_of = {
        "point": "arrow",
        "tap": "arrow",
        "underline": "highlight",
        "highlight": "highlight",
        "trace": "highlight",
        "circle": "circle",
        "label": "label",
    }
    candidates.sort(key=lambda t: (-t[0], -t[1].start))
    selected: list[tuple[float, SemanticAnnotation]] = []
    used_families: set[str] = set()
    for alpha, ann in candidates:
        family = family_of.get(ann.kind.lower(), ann.kind.lower() or "other")
        if family in used_families:
            records.append(
                {
                    "kind": ann.kind,
                    "target": ann.target,
                    "drawn": False,
                    "reason": "suppressed_clutter_same_family",
                    "family": family,
                    "narration_cue": ann.narration_cue,
                }
            )
            continue
        used_families.add(family)
        selected.append((alpha, ann))
        if len(selected) >= 4:
            break

    for alpha, primary in selected:
        target = resolve_target(
            primary.target,
            canvas_size=(w, h),
            board_layout=board_layout,
            board_rect=board_rect,
            panel_slots=panel_slots,
            shell_stages=shell_stages,
        )
        used_fallback = False
        if target is None:
            if not allow_fallback_coords or not primary.target:
                records.append(
                    {
                        "kind": primary.kind,
                        "target": primary.target,
                        "drawn": False,
                        "reason": "target_not_visible",
                        "narration_cue": primary.narration_cue,
                    }
                )
                continue
            used_fallback = True
            x0, y0 = int(primary.x0 * w), int(primary.y0 * h)
            x1, y1 = int(primary.x1 * w), int(primary.y1 * h)
            rect = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
            target = SemanticTarget("custom", rect, label="fallback")

        rect = target.rect
        col = _blend(primary.color, alpha)
        stick = _blend((50, 50, 55), alpha)
        kind = primary.kind.lower()

        if kind in ("point", "tap"):
            origin, tip = _approach_point(rect, from_left=True)
            if kind == "tap":
                tip = _rect_center(rect)
                pulse = 0.5 + 0.5 * math.sin(alpha * math.pi * 4)
                r = int(10 + 8 * pulse)
                d.ellipse((tip[0] - r, tip[1] - r, tip[0] + r, tip[1] + r), outline=col, width=3)
            d.line((origin[0], origin[1], tip[0], tip[1]), fill=stick, width=4)
            if kind == "point":
                d.polygon(
                    [(tip[0] + 14, tip[1]), (tip[0] - 6, tip[1] - 8), (tip[0] - 6, tip[1] + 8)],
                    fill=col,
                )
        elif kind == "underline":
            y = rect[3] + 4
            x0, x1 = rect[0], rect[0] + int((rect[2] - rect[0]) * alpha)
            d.line((x0, y, x1, y), fill=col, width=5)
            origin = (rect[0] - 28, rect[1] + 20)
            d.line((origin[0], origin[1], x0, y - 4), fill=stick, width=3)
        elif kind == "circle":
            cx, cy = _rect_center(rect)
            rx = max(12, (rect[2] - rect[0]) // 2 + 14)
            ry = max(10, (rect[3] - rect[1]) // 2 + 12)
            rx = min(rx, int(w * 0.18))
            ry = min(ry, int(h * 0.08))
            steps = max(8, int(40 * alpha))
            pts = []
            for i in range(steps + 1):
                ang = -math.pi / 2 + 2 * math.pi * (i / 40)
                pts.append((cx + int(rx * math.cos(ang)), cy + int(ry * math.sin(ang))))
            if len(pts) >= 2:
                d.line(pts, fill=col, width=4)
        elif kind == "trace":
            x0, y0 = rect[0] + 8, (rect[1] + rect[3]) // 2
            x1, y1 = rect[2] - 8, y0
            steps = max(2, int(20 * alpha))
            pts = []
            for i in range(steps + 1):
                t = i / 20
                pts.append((int(x0 + (x1 - x0) * t), int(y0 + 12 * math.sin(t * math.pi))))
            if len(pts) >= 2:
                d.line(pts, fill=col, width=4)
        elif kind == "highlight":
            pad = 6
            d.rounded_rectangle(
                (rect[0] - pad, rect[1] - pad, rect[2] + pad, rect[3] + pad),
                radius=8,
                outline=col,
                width=4,
            )
        else:
            # Unknown kind — never draw decorative scribbles
            records.append(
                {
                    "kind": kind,
                    "target": primary.target,
                    "drawn": False,
                    "reason": "unsupported_annotation_kind",
                    "narration_cue": primary.narration_cue,
                }
            )
            continue

        records.append(
            {
                "kind": kind,
                "target": primary.target,
                "drawn": True,
                "resolved_kind": target.kind,
                "rect": list(rect),
                "fallback": used_fallback,
                "narration_cue": primary.narration_cue,
                "teaching_purpose": primary.narration_cue,
                "alpha": round(alpha, 3),
            }
        )
    return records


def annotations_from_pointer_actions(actions: list[Any]) -> list[SemanticAnnotation]:
    """Adapt legacy PointerAction objects (with optional .extras['target'])."""
    out: list[SemanticAnnotation] = []
    for a in actions:
        extras = getattr(a, "extras", None) or {}
        if isinstance(extras, dict):
            target = str(extras.get("target") or getattr(a, "target", "") or "")
            cue = str(
                extras.get("narration_cue")
                or getattr(a, "narration_cue", "")
                or ""
            )
        else:
            target = str(getattr(a, "target", "") or "")
            cue = str(getattr(a, "narration_cue", "") or "")
        out.append(
            SemanticAnnotation(
                kind=str(getattr(a, "kind", "point")),
                start=float(getattr(a, "start", 0)),
                end=float(getattr(a, "end", 1)),
                target=target,
                x0=float(getattr(a, "x0", 0.55)),
                y0=float(getattr(a, "y0", 0.30)),
                x1=float(getattr(a, "x1", 0.75)),
                y1=float(getattr(a, "y1", 0.45)),
                color=tuple(getattr(a, "color", (210, 45, 35)) or (210, 45, 35)),  # type: ignore[arg-type]
                narration_cue=cue,
                extras=dict(extras) if isinstance(extras, dict) else {},
            )
        )
    return out
