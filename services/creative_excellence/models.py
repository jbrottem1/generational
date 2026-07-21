"""Creative Excellence models — attention dimensions, not code quality."""

from __future__ import annotations

# Viewer-outcome questions (binary judgment aids)
VIEWER_OUTCOME_QUESTIONS = (
    "would_stop_scrolling",
    "would_finish_watching",
    "would_share",
    "would_subscribe",
)

# Timeline segments the Creative Director must judge
TIMELINE_SEGMENTS = (
    "first_3_seconds",
    "first_6_seconds",
    "first_15_seconds",
    "middle_pacing",
    "ending",
)

# Soft craft signals inside each timeline pass
CRAFT_SIGNALS = (
    "viewer_emotion",
    "curiosity",
    "payoff",
    "visual_movement",
    "narration_energy",
)

# Mission scorecard — Creative Excellence (separate from ops/engineering)
CREATIVE_SCORE_DIMENSIONS = (
    "engineering_quality",  # present for contrast only — not the creative grade
    "creative_quality",
    "viewer_retention",
    "educational_value",
    "entertainment",
    "shareability",
    "emotional_impact",
    "curiosity",
)

# Expected retention gain ranking (higher = prefer as THE one recommendation)
RETENTION_IMPACT_RANK = (
    ("first_3_seconds", 100, "Winning the scroll-stop is the largest retention gain on Shorts."),
    ("first_6_seconds", 92, "Confirm the open with a visual argument before doubt returns."),
    ("first_15_seconds", 80, "Lock the promise before mid-video attrition."),
    ("middle_pacing", 72, "Pattern interrupt at the mid-drop saves completion."),
    ("ending", 60, "Payoff + share seed converts retention into growth."),
    ("visual_movement", 78, "Motion density keeps eyes from leaving."),
    ("narration_energy", 70, "Human contour on hook/punchline lifts finish rate."),
    ("curiosity", 85, "Open loops force the brain to stay for the close."),
    ("payoff", 68, "Unpaid curiosity collapses shares and rewatches."),
    ("viewer_emotion", 75, "Emotion is the share / subscribe conversion fuel."),
)
