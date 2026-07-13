"""Analytics service — Agent 9's performance-data collection layer.

Public surface:
    from services.analytics import get_analytics_store, collect_analytics
    from services.analytics import build_analytics_package, attach_experiment
    from services.analytics import performance_score, ANALYTICS_RECORD_FIELDS
"""

from services.analytics.collector import (
    attach_experiment,
    build_analytics_package,
    build_attribution,
    build_record,
    collect_analytics,
    collect_item_records,
    fingerprint,
)
from services.analytics.models import (
    ANALYTICS_ENGINE_VERSION,
    ANALYTICS_METRIC_FIELDS,
    ANALYTICS_PACKAGE_FIELDS,
    ANALYTICS_RECORD_FIELDS,
    ANALYTICS_RECORD_VERSION,
    ANALYTICS_SUMMARY_FIELDS,
    LEARNING_ENGINE_VERSION,
    MetricsStatus,
    empty_metrics,
    engagement_rate,
    performance_score,
)
from services.analytics.store import AnalyticsStore, get_analytics_store

__all__ = [
    "ANALYTICS_ENGINE_VERSION",
    "ANALYTICS_METRIC_FIELDS",
    "ANALYTICS_PACKAGE_FIELDS",
    "ANALYTICS_RECORD_FIELDS",
    "ANALYTICS_RECORD_VERSION",
    "ANALYTICS_SUMMARY_FIELDS",
    "LEARNING_ENGINE_VERSION",
    "AnalyticsStore",
    "MetricsStatus",
    "attach_experiment",
    "build_analytics_package",
    "build_attribution",
    "build_record",
    "collect_analytics",
    "collect_item_records",
    "empty_metrics",
    "engagement_rate",
    "fingerprint",
    "get_analytics_store",
    "performance_score",
]
