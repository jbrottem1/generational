"""Market Intelligence data contracts — the department's testable shapes.

Field tuples follow the repository convention (`services/seo/models.py`,
`services/analytics/models.py`): additive-only from v1.0 on, everything
JSON-safe. The `MarketOpportunity` is the atom of the department — the
ONLY thing it hands to the Production Pipeline. Never scripts, never
creative assets.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field

MARKET_INTELLIGENCE_VERSION = "1.0.0"

# ---------------------------------------------------------------- forecast

MARKET_FORECAST_FIELDS = (
    "growth_rate_pct",          # projected period-over-period growth
    "peak_date",                # ISO date the trend is expected to peak
    "decline_date",             # ISO date meaningful decline is expected
    "lifespan_days",            # expected total earning lifespan
    "virality_potential",       # 0-100
    "market_saturation",        # 0-1
    "competition_level",        # low | medium | high
    "forecast_confidence",      # 0-1
    "expected_longevity",       # short | medium | long | evergreen
    "historical_similarity",    # 0-1 — how closely this matches past winners
    "model",                    # forecast model key that produced this
)

LONGEVITY_CLASSES = ("short", "medium", "long", "evergreen")
COMPETITION_LEVELS = ("low", "medium", "high")

# ------------------------------------------------------------- competition

COMPETITION_PROFILE_FIELDS = (
    "publishing_frequency",     # estimated posts/week in the niche
    "creator_saturation",       # 0-1 share of active creators covering it
    "average_views",
    "average_engagement",       # engagements per 100 views
    "average_retention",        # 0-100
    "average_ctr",              # 0-100
    "market_difficulty",        # 0-100 — how hard it is to break in
    "content_gap_score",        # 0-100 — demand unmet by supply
)

# ------------------------------------------------------------ opportunity

# Content-nature classes assigned by the evergreen engine.
CONTENT_NATURES = ("trending", "seasonal", "evergreen", "educational", "news", "reference")

# Strategic actions the recommendation layer can issue.
class STRATEGIC_ACTION:
    PUBLISH_IMMEDIATELY = "publish_immediately"
    MONITOR = "monitor"
    DELAY = "delay"
    EXPAND_INTO_SERIES = "expand_into_series"
    REPURPOSE_EXISTING = "repurpose_existing_content"
    TRANSLATE = "translate"
    LOCALIZE = "localize"
    CREATE_LONG_FORM = "create_long_form_version"
    CREATE_SHORT_FORM = "create_short_form_version"
    CREATE_VARIANTS = "create_multiple_variants"

    ALL = (
        PUBLISH_IMMEDIATELY, MONITOR, DELAY, EXPAND_INTO_SERIES,
        REPURPOSE_EXISTING, TRANSLATE, LOCALIZE,
        CREATE_LONG_FORM, CREATE_SHORT_FORM, CREATE_VARIANTS,
    )


MARKET_OPPORTUNITY_FIELDS = (
    "opportunity_id",
    "version",
    "platform",
    "topic",
    "category",
    "audience",                 # audience descriptor (niche/mid_market/mass_market + hint)
    "language",
    "region",
    "difficulty",               # 0-100 (from competition analysis)
    "confidence",               # 0-1
    "roi_estimate",             # 0-100
    "competition_score",        # 0-100 (higher = MORE open, less competition)
    "trend_score",              # 0-100 (Agent 1's opportunity score)
    "forecast_score",           # 0-100 (future potential from the forecast)
    "priority",                 # 0-100 — the department's final ranking number
    "recommended_publish_window",   # {start, end, ...}
    "recommended_content_length",   # {min_sec, max_sec}
    "recommended_content_type",     # short_form | long_form | series | ...
    "content_nature",           # CONTENT_NATURES value
    "strategic_actions",        # ordered STRATEGIC_ACTION list
    "forecast",                 # MARKET_FORECAST_FIELDS dict
    "competition",              # COMPETITION_PROFILE_FIELDS dict
    "signals",                  # provenance: sources, platforms, keyword set
    "created_at",
)


@dataclass
class MarketOpportunity:
    """One structured, ranked, fully-analyzed content opportunity."""

    opportunity_id: str = field(default_factory=lambda: f"opp_{uuid.uuid4().hex[:12]}")
    version: str = MARKET_INTELLIGENCE_VERSION
    platform: str = "youtube_shorts"
    topic: str = ""
    category: str = "general"
    audience: str = ""
    language: str = "en"
    region: str = "US"
    difficulty: int = 50
    confidence: float = 0.5
    roi_estimate: int = 0
    competition_score: int = 50
    trend_score: int = 0
    forecast_score: int = 0
    priority: int = 0
    recommended_publish_window: dict = field(default_factory=dict)
    recommended_content_length: dict = field(default_factory=dict)
    recommended_content_type: str = "short_form"
    content_nature: str = "trending"
    strategic_actions: list = field(default_factory=list)
    forecast: dict = field(default_factory=dict)
    competition: dict = field(default_factory=dict)
    signals: dict = field(default_factory=dict)
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MarketOpportunity":
        known = {f for f in cls.__dataclass_fields__}  # noqa: C401
        return cls(**{k: v for k, v in (data or {}).items() if k in known})


# ---------------------------------------------------------------- roadmap

ROADMAP_FIELDS = (
    "generated_at",
    "topic",
    "daily",                # today's slots (highest priority, act now)
    "weekly",               # this week's plan
    "monthly",              # this month's plan
    "quarterly_strategy",   # category/market-level strategic direction
    "queues",               # evergreen / trending / high_roi / low_competition
    "calendar",             # ordered publish-calendar entries
)

ROADMAP_QUEUES = ("evergreen", "trending", "high_roi", "low_competition")

CALENDAR_ENTRY_FIELDS = (
    "date",
    "opportunity_id",
    "topic",
    "platform",
    "content_type",
    "priority",
)

# ---------------------------------------------------------------- reports

MARKET_REPORT_SECTIONS = (
    "executive_summary",
    "opportunity_report",
    "trend_forecast_report",
    "competition_report",
    "roi_report",
    "platform_opportunity_report",
)

MARKET_REPORT_FIELDS = (
    "report_version",
    "generated_at",
    "topic",
    "category",
    *MARKET_REPORT_SECTIONS,
    "quality",              # validation findings (duplicates, low confidence, ...)
    "learning",             # calibration factors applied from Analytics history
)
