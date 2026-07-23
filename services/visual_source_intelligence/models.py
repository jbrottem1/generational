"""Visual Source Intelligence — shared constants (selection only, no renderer)."""

from __future__ import annotations

PACKAGE_TYPE = "VISUAL_SOURCE_INTELLIGENCE"
PACKAGE_VERSION = "1.0.0"

# Mission fallback ladder (best → last resort). Lower rank = better.
SOURCE_FALLBACK_RANK: dict[str, int] = {
    "stock_video": 1,
    "licensed_stock_video": 1,
    "stock_footage": 1,
    "library_video": 1,
    "ai_video": 2,
    "ai_generated_video": 2,
    "animated_diagram": 3,
    "motion_graphics": 3,
    "diagram": 3,
    "map": 3,
    "chart": 3,
    "ai_still_motion": 4,
    "ai_image_motion": 4,
    "ai_image": 4,
    "static_image": 5,
    "photograph": 5,
    "atlas_image": 5,
    "cinematic_fallback": 6,
    "placeholder": 6,
}

SOURCE_LABELS = {
    1: "licensed_stock_video",
    2: "ai_generated_video",
    3: "animated_diagram",
    4: "ai_still_with_motion",
    5: "static_image_last_resort",
    6: "placeholder_rejected_or_emergency",
}

# Map VSI source tiers → existing Visual Intelligence adapter keys (sources.py)
TIER_TO_ASSET_TYPE = {
    1: "stock_footage",
    2: "ai_video",
    3: "ai_image",  # diagrams fulfilled as generative/overlay plates + motion plan
    4: "ai_image",
    5: "ai_image",
    6: "ai_image",
}

REJECT_REASONS = (
    "feels_like_slideshow",
    "repeated_identical_camera",
    "fails_to_explain_narration",
    "obvious_placeholder",
    "lacks_cinematic_interest",
    "broken_or_missing_path",
    "low_relevance",
)

MOTION_CYCLE = (
    "slow cinematic push-in",
    "drone establish then settle",
    "close-up detail reveal",
    "pan left across subject",
    "subtle parallax push",
    "slow zoom out reveal",
    "quick punch-in on key detail",
    "tracking slide right",
)

DIAGRAM_HINTS = (
    "diagram",
    "chart",
    "graph",
    "map",
    "labeled",
    "cross-section",
    "schematic",
    "legend",
    "rate",
    "color meaning",
    "indicates",
    "rating",
    "flow",
    "comparison",
)

MOTION_HINTS = (
    "moving",
    "flow",
    "spray",
    "drone",
    "walking",
    "pour",
    "rush",
    "cascade",
    "spin",
    "open",
    "close",
    "approach",
)
