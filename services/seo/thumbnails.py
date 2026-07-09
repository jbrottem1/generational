"""Thumbnail Optimization — evaluate and rank Visual Intelligence concepts.

Consumes thumbnail concepts produced by the Visual Intelligence engine
(`ThumbnailConcept.to_dict()` dicts, or the refinement-stage one-line
concept) and re-evaluates each on the six click-through dimensions:
curiosity, contrast, text density, facial emotion, object emphasis, and
color psychology. Never regenerates or overwrites the concepts — it adds a
ranked recommendation layer on top.
"""

from __future__ import annotations

from engines.heuristics import CURIOSITY_WORDS, EMOTION_WORDS, clamp, count_hits, stable_jitter, weighted_blend

_EVAL_WEIGHTS = {
    "curiosity": 0.22,
    "contrast": 0.18,
    "text_density": 0.15,
    "facial_emotion": 0.18,
    "object_emphasis": 0.12,
    "color_psychology": 0.15,
}

_WARM_COLOR_WORDS = ("red", "orange", "yellow", "warm", "high-contrast", "saturated", "bold")


def _text_density_score(overlay: str) -> int:
    """Fewer, bigger words win: 1-3 words is the CTR sweet spot."""
    words = len(overlay.split())
    if words == 0:
        return 45
    if words <= 3:
        return 90
    if words <= 5:
        return 65
    return clamp(60 - (words - 5) * 8, low=10)


def evaluate_concept(concept: dict, index: int = 0) -> dict:
    """Six-dimension evaluation + click probability for one concept dict."""
    scores = concept.get("scores", {})
    text = " ".join(
        str(concept.get(field, ""))
        for field in ("description", "label", "emotion", "color_strategy", "concept")
    )
    overlay = concept.get("title_overlay") or concept.get("text_overlay") or ""

    evaluation = {
        "curiosity": int(scores.get("curiosity", 0))
        or clamp(50 + count_hits(text, CURIOSITY_WORDS) * 12 + stable_jitter(text)),
        "contrast": int(concept.get("contrast_score", 0))
        or int(scores.get("contrast", 0))
        or clamp(48 + (14 if "contrast" in text.lower() else 0) + stable_jitter(text + "c")),
        "text_density": _text_density_score(overlay),
        "facial_emotion": int(scores.get("facial_focus", 0))
        or clamp(42 + count_hits(text, EMOTION_WORDS) * 10 + (16 if concept.get("emotion") else 0)),
        "object_emphasis": int(scores.get("object_focus", 0))
        or clamp(45 + (18 if concept.get("focal_subject") or concept.get("focal_point") else 0)),
        "color_psychology": int(scores.get("color", 0))
        or clamp(46 + sum(8 for word in _WARM_COLOR_WORDS if word in text.lower())),
    }
    click_probability = float(concept.get("click_probability_pct", 0.0)) or round(
        weighted_blend(evaluation, _EVAL_WEIGHTS) / 10.0, 1
    )

    weakest = min(evaluation, key=lambda key: evaluation[key])
    recommendation = f"Strengthen {weakest.replace('_', ' ')} — it is the weakest click driver on this concept."

    return {
        "concept_id": concept.get("concept_id", f"concept_{index + 1}"),
        "archetype": concept.get("archetype", concept.get("source", "unknown")),
        "label": concept.get("label") or concept.get("concept", "")[:60],
        "evaluation": evaluation,
        "click_probability_pct": click_probability,
        "recommendation": recommendation,
        "rank": 0,
    }


def rank_thumbnail_concepts(concepts: "list[dict]") -> "list[dict]":
    """Ranked thumbnail recommendations, best click probability first."""
    evaluated = [evaluate_concept(concept, index) for index, concept in enumerate(concepts or [])]
    evaluated.sort(
        key=lambda item: (-item["click_probability_pct"], -sum(item["evaluation"].values()), item["concept_id"])
    )
    for rank, item in enumerate(evaluated, 1):
        item["rank"] = rank
    return evaluated
