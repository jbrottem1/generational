"""Trend Intelligence configuration — every knob is data, not code.

One dataclass holds all tunables: forecast horizons, classification
thresholds, quality-control gates, ROI/priority weights, provider
enablement, polling cadence, regions, languages, platforms, and topic
watchlists. Overrides load from `data/trend_intelligence/config.json`
(if present) or arrive programmatically via `configure(**overrides)` —
the Learning Engine tunes weights the same way.

Nothing here mutates Agent 1's scorer weights (`services/trends/scorer.py`
`FACTOR_WEIGHTS`); those remain the base opportunity score. This module
configures the intelligence layered on top.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field

from core.log import get_logger, log_event

logger = get_logger(__name__)

_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "trend_intelligence", "config.json",
)


@dataclass
class TrendIntelligenceConfig:
    """All tunables for forecasting, classification, QC, and the feed."""

    # ------------------------------------------------ discovery scope
    regions: list = field(default_factory=lambda: ["US"])
    languages: list = field(default_factory=lambda: ["en"])
    platforms: list = field(default_factory=lambda: [
        "youtube_shorts", "tiktok", "instagram", "youtube",
    ])
    topics: list = field(default_factory=list)          # optional watchlist
    enabled_providers: list = field(default_factory=list)   # empty = all
    disabled_providers: list = field(default_factory=list)
    poll_interval_minutes: int = 60
    limit_per_provider: int = 3
    top_n: int = 10

    # ------------------------------------------------ forecast thresholds
    max_days_to_peak: int = 14
    base_lifespan_days: int = 3
    evergreen_lifespan_days: int = 120
    explosive_growth_pct: float = 120.0
    explosive_velocity: float = 0.65

    # ------------------------------------------------ classification
    breaking_freshness: float = 0.85
    breaking_growth_pct: float = 80.0
    exploding_growth_pct: float = 150.0
    exploding_velocity: float = 0.7
    emerging_growth_pct: float = 60.0
    emerging_freshness: float = 0.6
    declining_growth_pct: float = 15.0
    declining_freshness: float = 0.4
    peak_velocity: float = 0.35
    peak_competition: float = 0.7
    evergreen_floor: float = 0.75
    niche_search_volume: int = 20_000
    mass_market_search_volume: int = 1_000_000

    # ------------------------------------------------ quality control
    min_confidence: float = 0.2
    max_signal_age_hours: float = 72.0
    min_freshness: float = 0.1
    near_duplicate_similarity: float = 0.75
    conflict_growth_spread_pct: float = 150.0

    # ------------------------------------------------ scoring weights
    # Priority blends the final "act on this now" number (values normalized
    # at use; the Learning Engine may retune them via configure()).
    priority_weights: dict = field(default_factory=lambda: {
        "opportunity_score": 0.30,
        "estimated_roi": 0.25,
        "urgency": 0.20,
        "confidence": 0.15,
        "risk_penalty": 0.10,
    })
    roi_weights: dict = field(default_factory=lambda: {
        "opportunity_score": 0.35,
        "monetization": 0.25,
        "low_competition": 0.20,
        "future_score": 0.20,
    })

    # ---------------------------------------------------------- plumbing
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TrendIntelligenceConfig":
        known = {f for f in cls.__dataclass_fields__}  # noqa: C401 - py3.9-safe
        return cls(**{k: v for k, v in (data or {}).items() if k in known})

    def provider_allowed(self, key: str) -> bool:
        if key in self.disabled_providers:
            return False
        if self.enabled_providers and key not in self.enabled_providers:
            return False
        return True


def _load_from_file() -> TrendIntelligenceConfig:
    if os.path.exists(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as file:
                config = TrendIntelligenceConfig.from_dict(json.load(file))
            log_event(logger, "trend_intelligence.config_loaded", path=_CONFIG_PATH)
            return config
        except (json.JSONDecodeError, OSError, TypeError) as exc:
            log_event(
                logger, "trend_intelligence.config_load_failed", level=30,
                path=_CONFIG_PATH, error=str(exc),
            )
    return TrendIntelligenceConfig()


_config: "TrendIntelligenceConfig | None" = None


def get_trend_intelligence_config() -> TrendIntelligenceConfig:
    """The active config singleton (file overrides applied on first load)."""
    global _config
    if _config is None:
        _config = _load_from_file()
    return _config


def configure(**overrides) -> TrendIntelligenceConfig:
    """Apply programmatic overrides (e.g. from the Learning Engine)."""
    config = get_trend_intelligence_config()
    for key, value in overrides.items():
        if not hasattr(config, key):
            raise ValueError(f"Unknown trend intelligence config key: {key!r}")
        setattr(config, key, value)
    log_event(logger, "trend_intelligence.configured", keys=",".join(sorted(overrides)))
    return config


def reset_trend_intelligence_config() -> None:
    """Drop the singleton (tests / hot-reload)."""
    global _config
    _config = None
