"""Prediction models — pluggable performance predictors for variants.

A `PredictionModel` turns one variant (plus item/context signals) into
predicted CTR, retention, engagement, and revenue scores (0-100). The
default is a deterministic heuristic model (Demo Mode convention); ML or
platform-informed models register with `register_prediction_model()` and
activate via `configure(prediction_model="<key>")` — zero scoring-engine
changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from engines.heuristics import (
    CURIOSITY_WORDS,
    EMOTION_WORDS,
    SURPRISE_WORDS,
    clamp,
    count_hits,
    has_digit,
    stable_jitter,
)

PREDICTION_KEYS = (
    "ctr_prediction",
    "retention_prediction",
    "engagement_prediction",
    "revenue_prediction",   # explicit placeholder until monetization lands
)


class PredictionModel(ABC):
    """Contract for anything that predicts variant performance."""

    key: str = "base"

    @abstractmethod
    def predict(self, variant: dict, item: "dict | None" = None, context: "dict | None" = None) -> dict:
        """Return a dict covering every PREDICTION_KEYS entry (0-100)."""


class HeuristicPredictionModel(PredictionModel):
    """Deterministic word-bank predictions — same input, same numbers."""

    key = "heuristic"

    def predict(self, variant: dict, item: "dict | None" = None, context: "dict | None" = None) -> dict:
        item = item or {}
        content = variant.get("content", "")
        text = content if isinstance(content, str) else " ".join(str(v) for v in content.values()) if isinstance(content, dict) else str(content)
        lower = text.lower()
        jitter = stable_jitter(f"{variant.get('variant_id', '')}:{text}", span=6)

        ctr = 42 + jitter
        ctr += min(count_hits(lower, CURIOSITY_WORDS + SURPRISE_WORDS), 3) * 9
        if "?" in text:
            ctr += 6
        if has_digit(text):
            ctr += 7
        if isinstance(content, str) and 0 < len(text.split()) <= 12:
            ctr += 8

        retention = 44 + jitter
        retention += min(count_hits(lower, EMOTION_WORDS), 2) * 8
        if "you" in lower:
            retention += 7
        retention += min(int(item.get("attention_score", 0)) // 12, 8)

        engagement = 40 + jitter
        engagement += min(count_hits(lower, EMOTION_WORDS + CURIOSITY_WORDS), 3) * 7
        if any(word in lower for word in ("comment", "share", "save", "follow", "subscribe")):
            engagement += 10
        engagement += min(int(item.get("psychology_score", 0)) // 15, 6)

        return {
            "ctr_prediction": clamp(ctr),
            "retention_prediction": clamp(retention),
            "engagement_prediction": clamp(engagement),
            # Placeholder until monetization APIs land — neutral midpoint so
            # its (small) weight never distorts rankings.
            "revenue_prediction": 50,
        }


_models: "dict[str, PredictionModel]" = {}


def register_prediction_model(model: PredictionModel) -> PredictionModel:
    _models[model.key] = model
    return model


def get_prediction_model(key: str = "") -> PredictionModel:
    """The requested model, falling back to the heuristic default."""
    if not key:
        from services.optimization.config import get_optimization_config

        key = get_optimization_config().prediction_model
    return _models.get(key) or _models["heuristic"]


def prediction_model_keys() -> list:
    return sorted(_models)


register_prediction_model(HeuristicPredictionModel())
