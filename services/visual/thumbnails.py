"""Thumbnail engine — five scored thumbnail concepts per idea.

Five archetypes compete for every idea (shock face close-up, mystery object
macro, before/after split, extreme scale contrast, bold-text tease). Each is
scored 0-100 on seven dimensions — curiosity, readability, contrast, facial
focus, object focus, color, emotion — blended into one overall score, and
mapped to an expected CTR %. Deterministic, so results are reproducible and
the future Learning Engine can recalibrate against real CTR data by editing
weights, never scoring code.
"""

from __future__ import annotations

from engines.heuristics import (
    CURIOSITY_WORDS,
    EMOTION_WORDS,
    clamp,
    count_hits,
    stable_jitter,
)
from services.visual.models import THUMBNAIL_SCORE_KEYS, ThumbnailConcept

# How much each dimension contributes to a thumbnail's overall score.
# Curiosity and contrast dominate because they decide the impression-to-click
# moment; readability matters at feed-render sizes. Sum == 1.0.
THUMBNAIL_SCORE_WEIGHTS = {
    "curiosity": 0.24,
    "readability": 0.16,
    "contrast": 0.18,
    "facial_focus": 0.12,
    "object_focus": 0.10,
    "color": 0.08,
    "emotion": 0.12,
}

# Five archetypes with per-dimension base scores (before idea-specific
# adjustments). Data, not code — tuning an archetype is a table edit.
THUMBNAIL_ARCHETYPES = [
    {
        "key": "shock_face",
        "label": "Shock Face Close-Up",
        "description": "Extreme close-up of a stunned human face, eyes locked on the viewer, mouth mid-gasp.",
        "focal_point": "eyes and raised eyebrows, dead center",
        "color_scheme": "warm skin tones against a single saturated background color",
        "composition": "face fills 70% of frame, text in remaining negative space",
        "base": {"curiosity": 70, "readability": 72, "contrast": 74, "facial_focus": 95, "object_focus": 35, "color": 70, "emotion": 92},
    },
    {
        "key": "mystery_object",
        "label": "Mystery Object Macro",
        "description": "Macro shot of the story's key object, half-lit, partially concealed in shadow.",
        "focal_point": "the object's most recognizable edge emerging from darkness",
        "color_scheme": "low-key black with one rim-lit accent color",
        "composition": "object off-center right, question-inducing shadow left",
        "base": {"curiosity": 90, "readability": 62, "contrast": 82, "facial_focus": 15, "object_focus": 95, "color": 60, "emotion": 58},
    },
    {
        "key": "before_after",
        "label": "Before / After Split",
        "description": "Vertical split frame — the 'before' state versus the transformed 'after' state.",
        "focal_point": "the seam between the two states",
        "color_scheme": "desaturated cool left half, vivid warm right half",
        "composition": "50/50 split with a hard dividing line and an arrow across the seam",
        "base": {"curiosity": 82, "readability": 70, "contrast": 92, "facial_focus": 25, "object_focus": 80, "color": 82, "emotion": 62},
    },
    {
        "key": "scale_contrast",
        "label": "Extreme Scale Contrast",
        "description": "A tiny familiar reference dwarfed by the story's subject at impossible scale.",
        "focal_point": "the size gap between the reference and the subject",
        "color_scheme": "deep atmospheric backdrop with a bright, small focal reference",
        "composition": "wide framing, subject towering from bottom-left to top-right diagonal",
        "base": {"curiosity": 80, "readability": 60, "contrast": 76, "facial_focus": 10, "object_focus": 85, "color": 66, "emotion": 60},
    },
    {
        "key": "bold_text_tease",
        "label": "Bold Text Tease",
        "description": "Three-word unfinished claim in massive type over a blurred hint of the reveal.",
        "focal_point": "the missing word implied by the cropped text",
        "color_scheme": "high-contrast white/yellow type on a dark defocused photo",
        "composition": "text occupies top two thirds, teaser image bleeding in from below",
        "base": {"curiosity": 86, "readability": 94, "contrast": 84, "facial_focus": 12, "object_focus": 45, "color": 72, "emotion": 55},
    },
]

# Expected CTR calibration: overall 0-100 → realistic 1.5-14% short-form CTR.
CTR_FLOOR_PCT = 1.5
CTR_CEILING_PCT = 14.0


def expected_ctr_pct(overall: int) -> float:
    """Map an overall thumbnail score to a realistic expected CTR %."""
    return round(CTR_FLOOR_PCT + (CTR_CEILING_PCT - CTR_FLOOR_PCT) * (overall / 100), 1)


def _text_overlay(idea: dict, archetype: dict) -> str:
    source = idea.get("title") or idea.get("hook") or "The untold story"
    words = source.split()
    if archetype["key"] == "bold_text_tease":
        return " ".join(words[:3]).upper() + "…"
    return " ".join(words[:4]).upper()


def score_thumbnail(archetype: dict, idea: dict) -> dict:
    """Idea-adjusted 0-100 scores for one archetype across all 7 dimensions."""
    text = f"{idea.get('title', '')} {idea.get('hook', '')}"
    jitter = stable_jitter(f"{archetype['key']}|{text}", span=6)
    curiosity_hits = count_hits(text, CURIOSITY_WORDS)
    emotion_hits = count_hits(text, EMOTION_WORDS)

    scores = {}
    for key in THUMBNAIL_SCORE_KEYS:
        value = archetype["base"][key] + jitter
        if key == "curiosity":
            value += 4 * min(curiosity_hits, 3)
        elif key == "emotion":
            value += 4 * min(emotion_hits, 3)
        scores[key] = clamp(value)
    return scores


def thumbnail_overall(scores: dict) -> int:
    """Single weighted 0-100 score from the 7 thumbnail dimensions."""
    return clamp(
        sum(scores[key] * weight for key, weight in THUMBNAIL_SCORE_WEIGHTS.items()),
        low=0,
        high=100,
    )


def build_thumbnail_concepts(idea: dict, *, palette: str = "") -> "list[ThumbnailConcept]":
    """Five scored thumbnail concepts for one idea, strongest first."""
    subject = idea.get("title") or idea.get("hook") or "the subject"
    concepts = []
    for archetype in THUMBNAIL_ARCHETYPES:
        scores = score_thumbnail(archetype, idea)
        overall = thumbnail_overall(scores)
        concepts.append(
            ThumbnailConcept(
                concept_id=archetype["key"],
                archetype=archetype["key"],
                label=archetype["label"],
                description=f"{archetype['description']} Subject: {subject}.",
                focal_point=archetype["focal_point"],
                text_overlay=_text_overlay(idea, archetype),
                color_scheme=f"{archetype['color_scheme']}" + (f"; brand palette: {palette}" if palette else ""),
                composition=archetype["composition"],
                scores=scores,
                overall=overall,
                expected_ctr_pct=expected_ctr_pct(overall),
            )
        )
    return sorted(concepts, key=lambda concept: concept.overall, reverse=True)
