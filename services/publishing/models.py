"""Data contracts for the Publishing & Distribution Engine (Agent 7).

Field tuples are the testable contract (same convention as the Render and
Optimization engines). Everything the engine emits is a plain JSON-safe
dict so the workflow context, ContentPackage slots, queue files, and the
UI can carry it without conversion.
"""

from __future__ import annotations

PUBLISHING_ENGINE_VERSION = "1.0.0"

# Version of the platform-ready package the Publishing Engine writes into
# the ContentPackage `publishing_package` slot. Additive-only from 1.0 on.
PUBLISH_PACKAGE_VERSION = "1.0"


class JobStatus:
    """Lifecycle of one publishing job."""

    QUEUED = "queued"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"

    ALL = (QUEUED, SCHEDULED, PUBLISHING, PUBLISHED, FAILED, CANCELLED)
    TERMINAL = (PUBLISHED, FAILED, CANCELLED)


# One platform-ready publish package (one item × one platform).
PLATFORM_PUBLISH_PACKAGE_FIELDS = (
    "package_version",
    "project_id",
    "video",              # {file_uri, duration_sec, resolution, aspect_ratio, mock}
    "thumbnail",
    "title",
    "description",
    "hashtags",
    "keywords",
    "captions",
    "language",
    "country",
    "platform",
    "provider",
    "account",            # placeholder PublishingAccount reference
    "publish_time",       # ISO-8601 UTC
    "timezone",           # e.g. "UTC-05:00"
    "visibility",         # public | unlisted | private
    "playlist",           # placeholder — real playlist routing is future work
    "category",           # placeholder — real category mapping is future work
    "status",
    "diagnostics",
    "generated_at",
)

# One queued publishing job (persisted in the publishing queue).
PUBLISHING_JOB_FIELDS = (
    "job_id",
    "project_id",
    "brand_id",
    "channel_id",
    "platform",
    "provider",
    "package",            # the platform publish package this job delivers
    "status",             # JobStatus value
    "attempts",
    "max_retries",
    "scheduled_time",     # ISO-8601 UTC
    "timezone",
    "next_retry_at",
    "last_error",
    "history",            # attempt records (see PUBLISH_ATTEMPT_FIELDS)
    "analytics_ref",      # future Analytics Engine correlation id
    "created_at",
    "updated_at",
)

# One publish attempt record (job history + PublishingHistory log).
PUBLISH_ATTEMPT_FIELDS = (
    "attempt",
    "provider",
    "platform",
    "status",
    "scheduled_time",
    "started_at",
    "published_at",
    "duration_ms",
    "post_id",
    "post_url",
    "warnings",
    "error",
    "analytics_ref",
)

# The standardized PublishingResult the engine returns to the orchestrator.
PUBLISHING_RESULT_FIELDS = (
    "engine_version",
    "status",             # SUCCESS | WARNING | FAILED | SKIPPED
    "items",
    "jobs_created",
    "published",
    "scheduled",
    "failed",
    "cancelled",
    "platforms",
    "queue_size",
    "publish_mode",
    "warnings",
    "errors",
    "results",            # per-job summaries
    "generated_at",
)

# One scheduler decision inside the `publish_schedule` context key.
PUBLISH_SCHEDULE_ENTRY_FIELDS = (
    "project_id",
    "platform",
    "country",
    "language",
    "mode",               # immediate | scheduled
    "publish_time",
    "timezone",
    "local_time",
    "window",             # the optimal window this slot came from ({} if none)
)

# Retry defaults — providers override per platform via `retry_policy()`.
DEFAULT_RETRY_POLICY = {
    "max_retries": 3,
    "base_delay_sec": 30,
    "backoff_multiplier": 2.0,
    "max_delay_sec": 3600,
}
