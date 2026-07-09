"""Global Content Optimization services (Agent 8).

The business logic behind the `seo_optimization` engine: title
optimization, keyword/hashtag/description generation, thumbnail
evaluation, localization preparation, posting strategy, optimization
scoring, and PublishingPackage assembly. The engine module
(`engines/seo_optimization.py`) stays thin and delegates here.
"""

from services.seo.descriptions import build_description_package
from services.seo.hashtags import build_hashtag_package, flat_hashtags
from services.seo.keywords import build_keyword_package, classify_intent, collect_keyword_signals, flatten_keywords
from services.seo.localization import (
    LOCALIZATION_TARGETS,
    HeuristicLocalizationAdapter,
    LocalizationAdapter,
    build_localization_package,
)
from services.seo.package import build_publishing_package, optimize_content
from services.seo.report import build_optimization_report
from services.seo.thumbnails import evaluate_concept, rank_thumbnail_concepts
from services.seo.titles import generate_title_candidates
from services.seo.windows import recommend_publish_windows

__all__ = [
    "LOCALIZATION_TARGETS",
    "HeuristicLocalizationAdapter",
    "LocalizationAdapter",
    "build_description_package",
    "build_hashtag_package",
    "build_keyword_package",
    "build_localization_package",
    "build_optimization_report",
    "build_publishing_package",
    "classify_intent",
    "collect_keyword_signals",
    "evaluate_concept",
    "flat_hashtags",
    "flatten_keywords",
    "generate_title_candidates",
    "optimize_content",
    "rank_thumbnail_concepts",
    "recommend_publish_windows",
]
