"""Data contracts for the Global Content Optimization Engine (Agent 8).

Field tuples are the testable contract (mirroring the Script and Visual
engines' `REQUIRED_*` conventions). Everything the engine emits is a plain
JSON-safe dict so the workflow context, ContentPackage slots, and Streamlit
can carry it without conversion.
"""

from __future__ import annotations

# The ten title archetypes the Title Optimization module must support.
TITLE_ARCHETYPES = (
    "curiosity",
    "authority",
    "educational",
    "question",
    "shock",
    "list",
    "contrarian",
    "story",
    "breaking_news",
    "scientific",
)

# Every ranked title candidate carries exactly these fields.
TITLE_CANDIDATE_FIELDS = (
    "title",
    "archetype",
    "ctr_prediction",
    "seo_score",
    "psychology_score",
    "confidence",
    "overall",
    "rank",
)

# The six keyword classes the Keyword Engine produces.
KEYWORD_CLASSES = (
    "primary",
    "secondary",
    "semantic",
    "long_tail",
    "entity",
    "question",
)

# Search-intent taxonomy for keyword classification.
SEARCH_INTENTS = (
    "informational",
    "navigational",
    "commercial",
    "transactional",
)

# Platforms the Hashtag Engine must cover.
HASHTAG_PLATFORMS = (
    "youtube",
    "tiktok",
    "instagram",
    "facebook",
    "x",
    "linkedin",
    "pinterest",
)

# The description package contract.
DESCRIPTION_PACKAGE_FIELDS = (
    "long_description",
    "short_description",
    "platform_descriptions",
    "call_to_action",
    "first_comment",
    "pinned_comment",
)

# Dimensions every thumbnail recommendation is evaluated on.
THUMBNAIL_EVAL_KEYS = (
    "curiosity",
    "contrast",
    "text_density",
    "facial_emotion",
    "object_emphasis",
    "color_psychology",
)

THUMBNAIL_RECOMMENDATION_FIELDS = (
    "concept_id",
    "archetype",
    "label",
    "evaluation",
    "click_probability_pct",
    "recommendation",
    "rank",
)

# Every ranked publish window carries exactly these fields.
PUBLISH_WINDOW_FIELDS = (
    "platform",
    "country",
    "language",
    "day",
    "start_hour_local",
    "end_hour_local",
    "audience_score",
    "competition_score",
    "trend_velocity_score",
    "score",
    "confidence",
    "rank",
)

# Per-locale plan contract inside the Localization Package.
LOCALIZATION_TARGET_FIELDS = (
    "country",
    "language",
    "locale",
    "status",
    "translation_pending",
    "keyword_replacements",
    "regional_hashtags",
    "regional_posting",
    "regional_seo_notes",
    "readiness",
)

# The Optimization Report contract — ten headline metrics, all 0-100
# except ctr_prediction (also 0-100, interpreted as relative CTR strength).
OPTIMIZATION_REPORT_FIELDS = (
    "seo_score",
    "ctr_prediction",
    "retention_prediction",
    "competition_score",
    "trend_strength",
    "evergreen_score",
    "localization_readiness",
    "publishing_readiness",
    "confidence",
    "overall_optimization_score",
)

# The standardized PublishingPackage handed to the Publishing Engine
# (Agent 7). Additive-only: Agent 7 may rely on every field listed here.
PUBLISHING_PACKAGE_VERSION = "1.0"

PUBLISHING_PACKAGE_FIELDS = (
    "package_version",
    "project_id",
    "title",
    "titles",
    "description",
    "descriptions",
    "keywords",
    "keyword_package",
    "hashtags",
    "thumbnail",
    "thumbnails",
    "publish_windows",
    "localization",
    "platforms",
    "language",
    "country",
    "optimization_report",
    "status",
    "generated_at",
)
