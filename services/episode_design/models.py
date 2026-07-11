"""Data contracts for the Episode Design Engine (Agent 25).

NOTE: Mission brief named this Agent 24; registry assigns Agent 25 because
Agent 24 is already Executive Intelligence (key: autonomous_executive).

Field tuples are the testable contract (additive-only from 1.0 on).
Everything emitted is plain JSON-safe dict.
"""

from __future__ import annotations

EPISODE_DESIGN_ENGINE_VERSION = "1.0.0"
EPISODE_DESIGN_PACKAGE_VERSION = "1.0"


class EpisodeDesignStatus:
    """Lifecycle of one EpisodeDesignPackage."""

    READY = "ready"
    NEEDS_REVIEW = "needs_review"
    DEGRADED = "degraded"
    INCOMPLETE = "incomplete"

    ALL = (READY, NEEDS_REVIEW, DEGRADED, INCOMPLETE)


# ──────────────────────────────────────────────────────────
# Canonical Lesson Blueprint timing beats (seconds).
# Total = 49s — matches the Generational educational format.
# ──────────────────────────────────────────────────────────
BLUEPRINT_BEATS = (
    {
        "beat": "curiosity_hook",
        "label": "Curiosity Hook",
        "start_sec": 0,
        "duration_sec": 2,
        "purpose": "Capture attention immediately — one arresting visual or question",
        "viewer_question": "What is happening? Why should I care?",
        "reveal": False,
        "pause_point": False,
    },
    {
        "beat": "interesting_question",
        "label": "Interesting Question",
        "start_sec": 2,
        "duration_sec": 5,
        "purpose": "State the surprising/counterintuitive question the episode answers",
        "viewer_question": "Is that really true? I have to find out.",
        "reveal": False,
        "pause_point": False,
    },
    {
        "beat": "demonstration",
        "label": "Demonstration",
        "start_sec": 7,
        "duration_sec": 10,
        "purpose": "Show the concept in action — visual proof before explanation",
        "viewer_question": "How does that work? What am I seeing?",
        "reveal": False,
        "pause_point": False,
    },
    {
        "beat": "explanation",
        "label": "Explanation",
        "start_sec": 17,
        "duration_sec": 15,
        "purpose": "Clear, layered teaching — build from simple to complex",
        "viewer_question": "Why does this happen? How does each layer connect?",
        "reveal": True,
        "pause_point": True,
    },
    {
        "beat": "real_world_application",
        "label": "Real-World Application",
        "start_sec": 32,
        "duration_sec": 10,
        "purpose": "Connect the concept to something in the viewer's own life",
        "viewer_question": "Where have I seen this? How does it affect me?",
        "reveal": False,
        "pause_point": False,
    },
    {
        "beat": "powerful_takeaway",
        "label": "Powerful Takeaway",
        "start_sec": 42,
        "duration_sec": 5,
        "purpose": "One memorable, shareable insight — the emotional peak",
        "viewer_question": "What do I now know that most people don't?",
        "reveal": True,
        "pause_point": True,
    },
    {
        "beat": "bridge_to_next",
        "label": "Bridge to Next Lesson",
        "start_sec": 47,
        "duration_sec": 2,
        "purpose": "Tease the next episode — leave a curiosity gap open",
        "viewer_question": "What comes next? What else don't I know?",
        "reveal": False,
        "pause_point": False,
    },
)

# ──────────────────────────────────────────────────────────
# Retention Review scoring dimensions
# ──────────────────────────────────────────────────────────
RETENTION_SCORE_FIELDS = (
    "curiosity_score",           # Does the hook create genuine urgency to watch on?
    "teaching_clarity_score",    # Is the explanation layered, clear, jargon-free?
    "visual_opportunity_score",  # Are there rich visual/demo moments?
    "emotional_engagement_score",# Does it make the viewer feel something?
    "educational_payoff_score",  # Does it deliver genuine learning value?
    "ending_strength_score",     # Does the ending land + tease the next episode?
    "overall_flow_score",        # Does the pacing feel natural start-to-finish?
    "overall_score",             # Weighted composite (0-100)
)

# ──────────────────────────────────────────────────────────
# Series Design fields
# ──────────────────────────────────────────────────────────
SERIES_DESIGN_FIELDS = (
    "series_type",               # mini_series | season | standalone | anthology
    "series_title",
    "episode_count",
    "episode_sequence",          # list of episode position + topic + connector
    "progression_arc",           # how complexity/stakes build across episodes
    "callbacks",                 # recurring references that reward viewers
    "recurring_elements",        # jokes, experiments, catchphrases, visual motifs
    "visual_continuity",         # shared color palette, typography, style rules
    "educational_continuity",    # how knowledge builds across the series
    "numbering_scheme",          # "Part 1/3" | "#1" | season/episode numbering
    "series_diagnostics",
)

# ──────────────────────────────────────────────────────────
# Playbook fields (per-pattern entry in JSON store)
# ──────────────────────────────────────────────────────────
PLAYBOOK_FIELDS = (
    "pattern_id",
    "pattern_name",
    "description",
    "niche",
    "strengths",                 # what this pattern does well
    "weaknesses",                # known failure modes
    "successes",                 # documented wins (project_ids, metrics)
    "improvement_notes",
    "times_used",
    "average_retention_score",
    "last_updated",
)

# ──────────────────────────────────────────────────────────
# EpisodeDesignPackage — full per-item output contract
# ──────────────────────────────────────────────────────────
EPISODE_DESIGN_PACKAGE_FIELDS = (
    "episode_design_package_version",
    "engine_version",
    "project_id",
    "lesson_blueprint",          # LessonBlueprint dict (beats with content guidance)
    "retention_review",          # RetentionReview dict (scores + revision list)
    "series_design",             # SeriesDesign dict (may be None for standalones)
    "design_questions",          # the six strategic questions answered
    "revision_notes",            # flat list of specific actionable revisions
    "upstream_slots_read",       # which upstream slots were consumed
    "validation",                # status, confidence, blockers
    "episode_design_diagnostics",
    "generated_at",
)

EPISODE_DESIGN_SUMMARY_FIELDS = (
    "engine_version",
    "status",                    # designed | no_items | degraded
    "items",
    "packages",
    "ready",
    "needs_review",
    "degraded",
    "incomplete",
    "average_retention_score",
    "niches",
    "generated_at",
)

# ──────────────────────────────────────────────────────────
# The six strategic design questions every episode answers
# ──────────────────────────────────────────────────────────
STRATEGIC_DESIGN_QUESTIONS = (
    "why_care",              # Why should the viewer care about this topic right now?
    "whats_surprising",      # What is the most surprising / counterintuitive element?
    "what_first",            # What is the optimal first frame / opening line?
    "biggest_reveal",        # When and how should the biggest reveal land?
    "where_pause",           # Where should pacing slow to let ideas sink in?
    "how_end",               # How should the episode end to make them watch another?
)
