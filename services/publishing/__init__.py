"""Publishing & Distribution services (Agent 7).

Thin engine, fat service layer (same split as services/seo/): the
PublishingEngine delegates everything to the PublishingManager, which
coordinates the queue, scheduler, retry manager, provider adapters,
account registry, and history log.
"""

from services.publishing.accounts import (
    PUBLISHING_ACCOUNT_FIELDS,
    AccountRegistry,
    CredentialProvider,
    build_publishing_account,
    get_account_registry,
)
from services.publishing.extensions import (
    PrePublishGate,
    PublishListener,
    RegionalScheduleRule,
    RollbackHandler,
    register_pre_publish_gate,
    register_publish_listener,
    register_rollback_handler,
    unregister_pre_publish_gate,
    unregister_publish_listener,
)
from services.publishing.manager import PublishingManager
from services.publishing.models import (
    DEFAULT_RETRY_POLICY,
    JobStatus,
    PLATFORM_PUBLISH_PACKAGE_FIELDS,
    PUBLISH_ATTEMPT_FIELDS,
    PUBLISH_PACKAGE_VERSION,
    PUBLISH_SCHEDULE_ENTRY_FIELDS,
    PUBLISHING_ENGINE_VERSION,
    PUBLISHING_JOB_FIELDS,
    PUBLISHING_RESULT_FIELDS,
)
from services.publishing.package import build_platform_publish_package
from services.publishing.queue import PublishingHistory, PublishingQueue, build_publishing_job
from services.publishing.retry import RetryManager
from services.publishing.scheduler import PUBLISH_MODES, PublishingScheduler, next_window_occurrence

# Register production integrity gate (blocks live publish of mock MP4s).
try:
    from services.media_production.bootstrap import bootstrap_media_production

    bootstrap_media_production()
except Exception:  # noqa: BLE001 — publishing must load even if media module fails
    pass

__all__ = [
    "AccountRegistry",
    "CredentialProvider",
    "DEFAULT_RETRY_POLICY",
    "JobStatus",
    "PLATFORM_PUBLISH_PACKAGE_FIELDS",
    "PUBLISHING_ACCOUNT_FIELDS",
    "PUBLISHING_ENGINE_VERSION",
    "PUBLISHING_JOB_FIELDS",
    "PUBLISHING_RESULT_FIELDS",
    "PUBLISH_ATTEMPT_FIELDS",
    "PUBLISH_MODES",
    "PUBLISH_PACKAGE_VERSION",
    "PUBLISH_SCHEDULE_ENTRY_FIELDS",
    "PrePublishGate",
    "PublishListener",
    "PublishingHistory",
    "PublishingManager",
    "PublishingQueue",
    "PublishingScheduler",
    "RegionalScheduleRule",
    "RetryManager",
    "RollbackHandler",
    "build_platform_publish_package",
    "build_publishing_account",
    "build_publishing_job",
    "get_account_registry",
    "next_window_occurrence",
    "register_pre_publish_gate",
    "register_publish_listener",
    "register_rollback_handler",
    "unregister_pre_publish_gate",
    "unregister_publish_listener",
]
