"""Trend Intelligence data contracts — forecast, classification, recommendation.

The field tuples are the testable contract (same convention as
`services/seo/models.py` and `services/publishing/models.py`). All shapes
are additive-only from v1.0 on and serialize to JSON-safe dicts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

FORECAST_FIELDS = (
    "trend_id",
    "topic",
    "days_to_peak",
    "expected_lifespan_days",
    "trajectory",              # explosive | rising | steady | flattening | declining
    "saturation_risk",         # 0-1
    "publishing_window",       # {start, end, start_in_days, end_in_days}
    "recommended_posts_per_week",
    "future_opportunity_score",  # 0-100 projected score at the window midpoint
    "forecast_confidence",     # 0-1
)

TRAJECTORIES = ("explosive", "rising", "steady", "flattening", "declining")

CLASSIFICATION_FIELDS = (
    "trend_id",
    "topic",
    "lifecycle",       # breaking | exploding | emerging | growing | peak | declining
    "content_type",    # evergreen | seasonal | recurring | topical
    "market_reach",    # niche | mid_market | mass_market
    "labels",          # all of the above as one list
)

LIFECYCLES = ("breaking", "exploding", "emerging", "growing", "peak", "declining")
CONTENT_TYPES = ("evergreen", "seasonal", "recurring", "topical")
MARKET_REACH = ("niche", "mid_market", "mass_market")

RECOMMENDATION_FIELDS = (
    "trend_id",
    "topic",
    "recommended_platform",
    "hook_direction",
    "psychology_strategy",
    "recommended_duration_sec",   # {min, max}
    "recommended_format",
    "thumbnail_direction",
    "title_direction",
    "seo_recommendations",        # {primary_keyword, secondary_keywords, ...}
    "publishing_window",
    "estimated_roi",              # 0-100
    "confidence_score",           # 0-1
    "risk_score",                 # 0-100
    "priority_score",             # 0-100 — the "act on this now" number
)


@dataclass
class TrendForecast:
    """Predicted future behavior of one scored opportunity."""

    trend_id: str = ""
    topic: str = ""
    days_to_peak: int = 7
    expected_lifespan_days: int = 14
    trajectory: str = "steady"
    saturation_risk: float = 0.5
    publishing_window: dict = field(default_factory=dict)
    recommended_posts_per_week: int = 2
    future_opportunity_score: int = 0
    forecast_confidence: float = 0.5

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TrendForecast":
        known = {f for f in cls.__dataclass_fields__}  # noqa: C401
        return cls(**{k: v for k, v in (data or {}).items() if k in known})


@dataclass
class OpportunityRecommendation:
    """Structured 'how to act on this' — never a script, never content."""

    trend_id: str = ""
    topic: str = ""
    recommended_platform: str = "youtube_shorts"
    hook_direction: str = ""
    psychology_strategy: str = ""
    recommended_duration_sec: dict = field(default_factory=dict)
    recommended_format: str = ""
    thumbnail_direction: str = ""
    title_direction: str = ""
    seo_recommendations: dict = field(default_factory=dict)
    publishing_window: dict = field(default_factory=dict)
    estimated_roi: int = 0
    confidence_score: float = 0.5
    risk_score: int = 50
    priority_score: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "OpportunityRecommendation":
        known = {f for f in cls.__dataclass_fields__}  # noqa: C401
        return cls(**{k: v for k, v in (data or {}).items() if k in known})
