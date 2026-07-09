"""Market Intelligence configuration — every strategic knob is data.

One dataclass covers provider priorities, forecast-model selection,
ranking weights, opportunity/confidence thresholds, and the market /
platform / localization / ROI weighting tables. Overrides load from
`data/market_intelligence/config.json` (if present) or arrive
programmatically via `configure(**overrides)` — the Learning Engine
retunes the department the same way.

This config layers ON TOP of `services/trend_intelligence/config.py`
(Agent 11's discovery-layer knobs) and never touches Agent 1's base
scorer weights.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field

from core.log import get_logger, log_event

logger = get_logger(__name__)

_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "market_intelligence", "config.json",
)


@dataclass
class MarketIntelligenceConfig:
    """All tunables for the Market Intelligence Department."""

    # ------------------------------------------------ provider priorities
    # Signal weight per provider key (unlisted providers default to 1.0).
    # Higher = that source's signals count for more in aggregate views.
    provider_priorities: dict = field(default_factory=lambda: {
        "internal_analytics": 1.5,     # our own history is the strongest signal
        "google_trends": 1.2,
        "youtube_trending": 1.2,
        "search_volume": 1.1,
        "keyword_api": 1.0,
        "industry_publications": 1.0,
        "academic_publications": 0.9,
        "ai_research": 0.9,
        "github_trending": 0.9,
        "product_launches": 0.9,
        "developer_communities": 0.8,
        "podcast_rankings": 0.8,
        "blog_feeds": 0.7,
    })

    # ------------------------------------------------ forecast models
    forecast_model: str = "momentum"    # key into forecasting.FORECAST_MODELS

    # ------------------------------------------------ ranking weights
    # How the final opportunity priority blends its component scores.
    ranking_weights: dict = field(default_factory=lambda: {
        "trend_score": 0.25,
        "forecast_score": 0.20,
        "roi_estimate": 0.20,
        "content_gap": 0.15,
        "confidence": 0.10,
        "difficulty_penalty": 0.10,
    })

    # ------------------------------------------------ thresholds
    min_opportunity_score: int = 30       # trend score gate
    min_confidence: float = 0.25          # opportunity confidence gate
    max_opportunities: int = 25           # kept per discovery pass

    # ------------------------------------------------ market weighting
    # Relative strategic value per content category (market attractiveness).
    market_weighting: dict = field(default_factory=lambda: {
        "finance": 1.2, "technology": 1.15, "health": 1.1, "science": 1.05,
        "education": 1.05, "psychology": 1.0, "history": 0.95, "space": 0.95,
        "general": 0.9, "entertainment": 0.85, "news": 0.8,
    })

    # ------------------------------------------------ platform weighting
    platform_weighting: dict = field(default_factory=lambda: {
        "youtube_shorts": 1.15, "tiktok": 1.1, "youtube": 1.05,
        "instagram": 1.0, "facebook": 0.85, "x": 0.85,
    })

    # ------------------------------------------------ localization weighting
    # language → (weight, default region). Drives localization opportunities.
    localization_weighting: dict = field(default_factory=lambda: {
        "en": {"weight": 1.0, "region": "US"},
        "es": {"weight": 0.85, "region": "MX"},
        "pt": {"weight": 0.75, "region": "BR"},
        "hi": {"weight": 0.7, "region": "IN"},
        "de": {"weight": 0.65, "region": "DE"},
        "fr": {"weight": 0.65, "region": "FR"},
    })

    # ------------------------------------------------ ROI weighting
    roi_weights: dict = field(default_factory=lambda: {
        "monetization": 0.30,
        "trend_score": 0.25,
        "competition_gap": 0.20,
        "forecast_score": 0.15,
        "historical_calibration": 0.10,
    })

    # ------------------------------------------------ roadmap shape
    daily_slots: int = 3
    weekly_slots: int = 10
    monthly_slots: int = 20
    queue_size: int = 10

    # ---------------------------------------------------------- plumbing
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MarketIntelligenceConfig":
        known = {f for f in cls.__dataclass_fields__}  # noqa: C401
        return cls(**{k: v for k, v in (data or {}).items() if k in known})

    def provider_priority(self, key: str) -> float:
        return float(self.provider_priorities.get(key, 1.0))

    def market_weight(self, category: str) -> float:
        return float(self.market_weighting.get(category.lower(), 0.9))

    def platform_weight(self, platform: str) -> float:
        return float(self.platform_weighting.get(platform.lower(), 0.9))


def _load_from_file() -> MarketIntelligenceConfig:
    if os.path.exists(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as file:
                config = MarketIntelligenceConfig.from_dict(json.load(file))
            log_event(logger, "market_intelligence.config_loaded", path=_CONFIG_PATH)
            return config
        except (json.JSONDecodeError, OSError, TypeError) as exc:
            log_event(
                logger, "market_intelligence.config_load_failed", level=30,
                path=_CONFIG_PATH, error=str(exc),
            )
    return MarketIntelligenceConfig()


_config: "MarketIntelligenceConfig | None" = None


def get_market_intelligence_config() -> MarketIntelligenceConfig:
    global _config
    if _config is None:
        _config = _load_from_file()
    return _config


def configure(**overrides) -> MarketIntelligenceConfig:
    """Apply programmatic overrides (Learning Engine, operators, tests)."""
    config = get_market_intelligence_config()
    for key, value in overrides.items():
        if not hasattr(config, key):
            raise ValueError(f"Unknown market intelligence config key: {key!r}")
        setattr(config, key, value)
    log_event(logger, "market_intelligence.configured", keys=",".join(sorted(overrides)))
    return config


def reset_market_intelligence_config() -> None:
    global _config
    _config = None
