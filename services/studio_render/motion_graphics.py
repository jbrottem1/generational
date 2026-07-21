"""Module 2 — Advanced Motion Graphics."""

from __future__ import annotations

import re

from services.studio_render.models import MOTION_GRAPHICS_TYPES


def _needs_stat(text: str) -> bool:
    return bool(re.search(r"\d", text)) or any(
        w in text.lower() for w in ("percent", "%", "million", "billion", "rate")
    )


def _scenes(candidate: dict) -> list[dict]:
    vp = candidate.get("visual_package")
    if not isinstance(vp, dict):
        vp = {}
    scenes = list(vp.get("scenes") or [])
    if scenes:
        return [s for s in scenes if isinstance(s, dict)]
    ep = candidate.get("evidence_package")
    if not isinstance(ep, dict):
        ep = {}
    return [s for s in list(ep.get("scenes") or []) if isinstance(s, dict)]


def build_motion_graphics(candidate: dict) -> list[dict]:
    """Context-driven motion graphics — never random."""
    scenes = _scenes(candidate)
    graphics: list[dict] = []

    for i, scene in enumerate(scenes or [{"scene_id": "s1", "narration": str(candidate.get("title") or "")}]):
        sid = str(scene.get("scene_id") or f"s{i+1}")
        text = str(scene.get("narration") or scene.get("voiceover") or "").lower()
        items: list[dict] = []

        if any(w in text for w in ("notice", "look", "this detail", "highlight")):
            items.append(
                {
                    "type": "highlight_box",
                    "easing": "ease_out",
                    "duration_sec": 1.2,
                    "reason": "Narration asks viewer to notice a detail",
                }
            )
            items.append(
                {
                    "type": "animated_arrow",
                    "easing": "ease_in_out",
                    "duration_sec": 0.8,
                    "reason": "Direct attention to focal region",
                }
            )
        if _needs_stat(text):
            items.append(
                {
                    "type": "popup_statistic",
                    "easing": "spring",
                    "duration_sec": 1.5,
                    "reason": "Numeric claim → pop-up stat",
                }
            )
        if any(w in text for w in ("versus", "compared", "vs", "difference")):
            items.append(
                {
                    "type": "comparison_graphic",
                    "easing": "ease_in_out",
                    "duration_sec": 2.0,
                    "reason": "Comparison language",
                }
            )
        if any(w in text for w in ("process", "steps", "first", "then", "finally", "flow")):
            items.append(
                {
                    "type": "flow_diagram",
                    "easing": "linear",
                    "duration_sec": 2.4,
                    "reason": "Process / sequence narration",
                }
            )
        if any(w in text for w in ("because", "equals", "formula", "equation", "force", "energy")):
            items.append(
                {
                    "type": "animated_equation",
                    "easing": "ease_out",
                    "duration_sec": 1.8,
                    "reason": "Scientific / math claim",
                }
            )
        if i == 0:
            items.append(
                {
                    "type": "dynamic_text_reveal",
                    "easing": "ease_out",
                    "duration_sec": 1.0,
                    "reason": "Hook kinetic typography",
                }
            )
        # Every educational beat gets kinetic type + callout — avoid empty / static visuals
        items.append(
            {
                "type": "kinetic_caption_pop",
                "easing": "ease_out",
                "duration_sec": 0.9,
                "reason": "Kinetic educational overlay every beat",
            }
        )
        if i % 2 == 1:
            items.append(
                {
                    "type": "emphasis_pulse",
                    "easing": "spring",
                    "duration_sec": 0.7,
                    "reason": "Emphasis animation reinforces understanding",
                }
            )
        if not any(g["type"] in ("flow_diagram", "comparison_graphic", "animated_equation", "popup_statistic") for g in items):
            items.append(
                {
                    "type": "infographic_callout",
                    "easing": "ease_in_out",
                    "duration_sec": 1.4,
                    "reason": "Educational callout — prefer motion over static hold",
                }
            )
        if not items:
            items.append(
                {
                    "type": "animated_label",
                    "easing": "ease_out",
                    "duration_sec": 1.0,
                    "reason": "Default educational label — never empty graphics track",
                }
            )

        for g in items:
            assert g["type"] in MOTION_GRAPHICS_TYPES
            graphics.append({"scene_id": sid, **g})

    return graphics
