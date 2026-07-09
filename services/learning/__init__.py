"""Learning service — Agent 9's continuous-improvement layer.

Public surface:
    from services.learning import run_learning, mine_patterns
    from services.learning import build_recommendations, guidance_for_engine
    from services.learning import ExperimentManager, get_experiment_manager
    from services.learning import HistoricalMemory, get_memory, MEMORY_CATEGORY
    from services.learning import build_performance_report, render_report_text
"""

from services.learning.experiments import (
    EXPERIMENT_FIELDS,
    EXPERIMENT_KINDS,
    ExperimentManager,
    ExperimentStatus,
    compare_variants,
    get_experiment_manager,
)
from services.learning.loop import (
    build_learning_metadata,
    collect_learning_items,
    grow_memory,
    run_learning,
)
from services.learning.memory import (
    MEMORY_CATEGORY,
    MEMORY_ENTRY_FIELDS,
    HistoricalMemory,
    get_memory,
)
from services.learning.models import (
    DIMENSION_TARGETS,
    INSIGHT_FIELDS,
    LEARNING_ENGINE_VERSION,
    LEARNING_METADATA_FIELDS,
    LEARNING_REPORT_FIELDS,
    PATTERN_DIMENSIONS,
    PERFORMANCE_REPORT_FIELDS,
    RECOMMENDATION_FIELDS,
    REPORT_PERIODS,
    TARGET_ENGINES,
)
from services.learning.patterns import (
    best_performers,
    mine_patterns,
    platform_breakdown,
    worst_performers,
)
from services.learning.recommendations import (
    build_recommendations,
    guidance_for_engine,
    psychology_guidance,
    recommendations_by_engine,
    recommendations_from_records,
    script_guidance,
    seo_guidance,
    visual_guidance,
    voice_guidance,
)
from services.learning.reports import build_performance_report, render_report_text

__all__ = [
    "DIMENSION_TARGETS",
    "EXPERIMENT_FIELDS",
    "EXPERIMENT_KINDS",
    "ExperimentManager",
    "ExperimentStatus",
    "HistoricalMemory",
    "INSIGHT_FIELDS",
    "LEARNING_ENGINE_VERSION",
    "LEARNING_METADATA_FIELDS",
    "LEARNING_REPORT_FIELDS",
    "MEMORY_CATEGORY",
    "MEMORY_ENTRY_FIELDS",
    "PATTERN_DIMENSIONS",
    "PERFORMANCE_REPORT_FIELDS",
    "RECOMMENDATION_FIELDS",
    "REPORT_PERIODS",
    "TARGET_ENGINES",
    "best_performers",
    "build_learning_metadata",
    "build_performance_report",
    "build_recommendations",
    "collect_learning_items",
    "compare_variants",
    "get_experiment_manager",
    "get_memory",
    "grow_memory",
    "guidance_for_engine",
    "mine_patterns",
    "platform_breakdown",
    "psychology_guidance",
    "recommendations_by_engine",
    "recommendations_from_records",
    "render_report_text",
    "run_learning",
    "script_guidance",
    "seo_guidance",
    "visual_guidance",
    "voice_guidance",
    "worst_performers",
]
