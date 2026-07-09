"""Publishing & Distribution Engine (Agent 7).

Prepares completed content (RenderPackage + optimization PublishingPackage)
for the supported publishing providers: platform-fitted metadata, a durable
job queue with retries, timezone-aware scheduling, mock publish execution,
and full attempt history for the future Analytics Engine. Real platform
APIs plug in behind `providers/publishing/` adapters — nothing in the
package, queue, or scheduling contracts changes when they arrive.

This package supersedes the former `engines/publishing.py` planned stub
(same key) and graduates the `scheduler` contract stub from
`engines/future_stubs.py` (same key, same input contract).
"""

from engines.publishing.engine import PublishingEngine, publish_content
from engines.publishing.scheduler_engine import (
    SchedulerEngine,
    collect_publish_items,
    pair_with_optimization,
)

__all__ = [
    "PublishingEngine",
    "SchedulerEngine",
    "collect_publish_items",
    "pair_with_optimization",
    "publish_content",
]
