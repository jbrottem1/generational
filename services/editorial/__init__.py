"""Editorial standards for the Generational Motivational Media Studio.

Data and helpers consumed by scripts, psychology, quality, citation, channels,
and visual planning — not a parallel pipeline. Extend existing engines; do not
duplicate them.
"""

from __future__ import annotations

from services.editorial.philosophy import (
    EDITORIAL_PHILOSOPHY,
    EMOTIONAL_OUTCOME,
    MISSION_STATEMENT,
    REJECT_CRITERIA,
    WRITING_STANDARD,
)
from services.editorial.pillars import (
    CONTENT_PILLARS,
    DEFAULT_MOTIVATION_PILLARS,
    MOTIVATION_NICHE,
    is_motivational_niche,
    pillar_keywords,
)
from services.editorial.progression import (
    MOTIVATIONAL_PROGRESSION,
    PROGRESSION_LABELS,
    score_viewer_progression,
)
from services.editorial.story import (
    REQUIRED_STORY_BEATS,
    STORY_BEAT_LABELS,
    beats_complete,
    empty_story_beats,
    score_story_structure,
)

__all__ = [
    "CONTENT_PILLARS",
    "DEFAULT_MOTIVATION_PILLARS",
    "EDITORIAL_PHILOSOPHY",
    "EMOTIONAL_OUTCOME",
    "MISSION_STATEMENT",
    "MOTIVATION_NICHE",
    "MOTIVATIONAL_PROGRESSION",
    "PROGRESSION_LABELS",
    "REJECT_CRITERIA",
    "REQUIRED_STORY_BEATS",
    "STORY_BEAT_LABELS",
    "WRITING_STANDARD",
    "beats_complete",
    "empty_story_beats",
    "is_motivational_niche",
    "pillar_keywords",
    "score_story_structure",
    "score_viewer_progression",
]
