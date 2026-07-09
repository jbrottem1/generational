"""Optimization Laboratory configuration — every knob is data, not code.

One dataclass holds all tunables: scoring weights, confidence and
duplicate thresholds, ranking logic, prediction-model selection, variant
and experiment limits, and provider enablement. Overrides load from
`data/optimization/config.json` (if present) or arrive programmatically
via `configure(**overrides)` — the Learning Engine tunes weights the same
way it tunes trend intelligence.

Nothing here mutates another engine's weights (psychology, ranking, SEO,
scripts). This module configures the laboratory layered on top of their
outputs.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field

from core.log import get_logger, log_event
from services.optimization.models import DEFAULT_SCORING_WEIGHTS, EXPERIMENT_TYPES

logger = get_logger(__name__)

_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "optimization", "config.json",
)


@dataclass
class OptimizationConfig:
    """All tunables for variant generation, scoring, ranking, and experiments."""

    # ------------------------------------------------ variant generation
    # experiment_type → how many variants to generate (unlisted types use
    # default_variant_count). Counts are capped by max_variants_per_type.
    variant_counts: dict = field(default_factory=lambda: {
        "hook": 20,
        "title": 15,
        "thumbnail": 25,
        "caption": 8,
        "narration_style": 5,
        "cta_placement": 10,
    })
    default_variant_count: int = 6
    max_variants_per_type: int = 50
    # Normalized-text similarity above which two variants count as duplicates.
    duplicate_similarity: float = 0.9

    # ------------------------------------------------ scoring & ranking
    scoring_weights: dict = field(default_factory=lambda: dict(DEFAULT_SCORING_WEIGHTS))
    # Ranking logic: "score" (composite only) or "score_with_history"
    # (composite blended with historical winner priors).
    ranking_strategy: str = "score_with_history"
    # How much historical priors move a variant's ranking score (0-1).
    history_influence: float = 0.15
    # Active prediction model key (see services/optimization/predictions.py).
    prediction_model: str = "heuristic"

    # ------------------------------------------------ thresholds
    # Winner confidence (0-100) an experiment needs to conclude COMPLETED.
    min_winner_confidence: int = 60
    # Recommendations below this confidence carry a low-confidence warning.
    low_confidence_threshold: int = 40
    # Historical records needed before priors influence rankings.
    min_history_samples: int = 3

    # ------------------------------------------------ experiment limits
    max_concurrent_experiments: int = 10
    max_experiments_per_run: int = 40
    # Experiment types the pipeline stage runs automatically per item.
    active_experiment_types: list = field(default_factory=lambda: [
        "hook", "title", "thumbnail", "caption", "narration_style",
        "cta_placement", "publishing_time",
    ])
    # Future experiment types register here — validation accepts them
    # everywhere EXPERIMENT_TYPES values are accepted.
    extra_experiment_types: list = field(default_factory=list)

    # ------------------------------------------------ providers
    enabled_providers: list = field(default_factory=list)   # empty = all
    disabled_providers: list = field(default_factory=list)

    # ---------------------------------------------------------- plumbing
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "OptimizationConfig":
        known = {f for f in cls.__dataclass_fields__}  # noqa: C401 - py3.9-safe
        return cls(**{k: v for k, v in (data or {}).items() if k in known})

    def variant_count(self, experiment_type: str) -> int:
        count = int(self.variant_counts.get(experiment_type, self.default_variant_count))
        return max(2, min(count, self.max_variants_per_type))

    def provider_allowed(self, key: str) -> bool:
        if key in self.disabled_providers:
            return False
        if self.enabled_providers and key not in self.enabled_providers:
            return False
        return True


def all_experiment_types(config: "OptimizationConfig | None" = None) -> list:
    """Built-in plus configured future experiment types."""
    config = config or get_optimization_config()
    return list(EXPERIMENT_TYPES) + [
        t for t in config.extra_experiment_types if t not in EXPERIMENT_TYPES
    ]


def _load_from_file() -> OptimizationConfig:
    if os.path.exists(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as file:
                config = OptimizationConfig.from_dict(json.load(file))
            log_event(logger, "optimization.config_loaded", path=_CONFIG_PATH)
            return config
        except (json.JSONDecodeError, OSError, TypeError) as exc:
            log_event(
                logger, "optimization.config_load_failed", level=30,
                path=_CONFIG_PATH, error=str(exc),
            )
    return OptimizationConfig()


_config: "OptimizationConfig | None" = None


def get_optimization_config() -> OptimizationConfig:
    """The active config singleton (file overrides applied on first load)."""
    global _config
    if _config is None:
        _config = _load_from_file()
    return _config


def configure(**overrides) -> OptimizationConfig:
    """Apply programmatic overrides (e.g. from the Learning Engine)."""
    config = get_optimization_config()
    for key, value in overrides.items():
        if not hasattr(config, key):
            raise ValueError(f"Unknown optimization config key: {key!r}")
        setattr(config, key, value)
    log_event(logger, "optimization.configured", keys=",".join(sorted(overrides)))
    return config


def reset_optimization_config() -> None:
    """Drop the singleton (tests / hot-reload)."""
    global _config
    _config = None
