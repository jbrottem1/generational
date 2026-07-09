"""Generation job queue interfaces — async-ready submission for asset work.

Wraps the platform `core.jobs.JobQueue` with asset-generation-specific
job types. Execution is synchronous today (Streamlit model); callers only
depend on submit/run semantics so a background worker can later drain the
queue without API changes.

Job types:
- `asset_generate` — one GENERATION_REQUEST_FIELDS dict → one asset
- `asset_batch` — list of requests → BATCH_RESULT_FIELDS dict
- `asset_package` — one ContentPackage-style item → AssetPackage
"""

from __future__ import annotations

from core.jobs import JobQueue, get_queue
from core.log import get_logger, log_event

logger = get_logger(__name__)

JOB_TYPE_GENERATE = "asset_generate"
JOB_TYPE_BATCH = "asset_batch"
JOB_TYPE_PACKAGE = "asset_package"

ASSET_JOB_TYPES = (JOB_TYPE_GENERATE, JOB_TYPE_BATCH, JOB_TYPE_PACKAGE)

_handlers_registered = False


def _handle_generate(payload: dict) -> dict:
    from services.asset_generation.generator import generate_asset

    request = payload.get("request") or {}
    item = payload.get("item") or {}
    asset, job = generate_asset(request, item)
    return {"asset": asset, "job": job}


def _handle_batch(payload: dict) -> dict:
    from services.asset_generation.batch import batch_generate

    requests = payload.get("requests") or []
    item = payload.get("item") or {}
    return batch_generate(requests, item)


def _handle_package(payload: dict) -> dict:
    from services.asset_generation.package import build_asset_package

    item = payload.get("item") or {}
    return build_asset_package(item)


def ensure_asset_job_handlers(queue: "JobQueue | None" = None) -> JobQueue:
    """Register asset-generation handlers on the platform job queue (idempotent)."""
    global _handlers_registered
    queue = queue or get_queue()
    if not _handlers_registered or not queue.has_handler(JOB_TYPE_GENERATE):
        queue.register_handler(JOB_TYPE_GENERATE, _handle_generate)
        queue.register_handler(JOB_TYPE_BATCH, _handle_batch)
        queue.register_handler(JOB_TYPE_PACKAGE, _handle_package)
        _handlers_registered = True
        log_event(logger, "asset_generation.job_handlers_registered", types=len(ASSET_JOB_TYPES))
    return queue


def submit_generate(request: dict, item: "dict | None" = None, queue: "JobQueue | None" = None):
    """Enqueue one generation request. Returns the Job object."""
    queue = ensure_asset_job_handlers(queue)
    return queue.submit(JOB_TYPE_GENERATE, {"request": request, "item": item or {}})


def submit_batch(requests: list, item: "dict | None" = None, queue: "JobQueue | None" = None):
    """Enqueue a batch of generation requests. Returns the Job object."""
    queue = ensure_asset_job_handlers(queue)
    return queue.submit(JOB_TYPE_BATCH, {"requests": list(requests), "item": item or {}})


def submit_package(item: dict, queue: "JobQueue | None" = None):
    """Enqueue full AssetPackage assembly for one content item."""
    queue = ensure_asset_job_handlers(queue)
    return queue.submit(JOB_TYPE_PACKAGE, {"item": item})


def run_generate(request: dict, item: "dict | None" = None, queue: "JobQueue | None" = None) -> dict:
    """Submit + run one generation job synchronously. Returns {asset, job}."""
    queue = ensure_asset_job_handlers(queue)
    job = submit_generate(request, item, queue)
    finished = queue.run(job.id)
    return finished.result if finished.status == "succeeded" else {
        "asset": {},
        "job": {"status": "failed", "error": finished.error},
    }
