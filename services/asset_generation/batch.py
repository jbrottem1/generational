"""Batch generation — many requests, one coordinated result.

`batch_generate()` runs a list of GENERATION_REQUEST_FIELDS dicts through
the same generate_asset lifecycle (safety → cache → selection → retries →
fallback → QC). Concurrency is configurable; default is sequential for
determinism in Demo Mode, with optional ThreadPoolExecutor when
`batch_concurrency > 1`.

Never raises: per-request failures become failed assets inside the batch
result. The batch status is `completed` / `partial` / `failed` / `empty`.
"""

from __future__ import annotations

import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from services.asset_generation.config import AssetGenerationConfig, get_asset_generation_config
from services.asset_generation.generator import generate_asset
from services.asset_generation.models import AssetStatus, JobStatus
from services.asset_generation.registry import AssetRegistry, get_asset_registry
from services.asset_generation.usage import summarize_jobs


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def batch_generate(
    requests: "list[dict]",
    item: "dict | None" = None,
    config: "AssetGenerationConfig | None" = None,
    registry: "AssetRegistry | None" = None,
) -> dict:
    """Generate many assets. Returns one BATCH_RESULT_FIELDS dict."""
    config = config or get_asset_generation_config()
    registry = registry or get_asset_registry()
    item = item or {}
    batch_id = f"batch_{uuid.uuid4().hex[:10]}"
    started = time.time()

    if not requests:
        return {
            "batch_id": batch_id,
            "status": "empty",
            "requested": 0,
            "succeeded": 0,
            "failed": 0,
            "cache_hits": 0,
            "assets": [],
            "jobs": [],
            "usage": summarize_jobs([]),
            "duration_ms": 0,
            "created_at": _now_iso(),
        }

    concurrency = max(1, int(getattr(config, "batch_concurrency", 1) or 1))
    if concurrency == 1 or len(requests) == 1:
        pairs = [generate_asset(request, item, config, registry) for request in requests]
    else:
        pairs = _parallel(requests, item, config, registry, concurrency)

    assets = [pair[0] for pair in pairs]
    jobs = [pair[1] for pair in pairs]
    succeeded = sum(
        1 for asset in assets
        if asset.get("status") not in (AssetStatus.FAILED, AssetStatus.BLOCKED)
    )
    failed = len(assets) - succeeded
    cache_hits = sum(1 for job in jobs if job.get("status") == JobStatus.CACHE_HIT)

    if succeeded == len(assets):
        status = "completed"
    elif succeeded == 0:
        status = "failed"
    else:
        status = "partial"

    return {
        "batch_id": batch_id,
        "status": status,
        "requested": len(requests),
        "succeeded": succeeded,
        "failed": failed,
        "cache_hits": cache_hits,
        "assets": assets,
        "jobs": jobs,
        "usage": summarize_jobs(jobs),
        "duration_ms": int((time.time() - started) * 1000),
        "created_at": _now_iso(),
    }


def _parallel(requests, item, config, registry, concurrency: int) -> list:
    """Run generate_asset across a thread pool; preserve request order."""
    results: "dict[int, tuple]" = {}
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {
            pool.submit(generate_asset, request, item, config, registry): index
            for index, request in enumerate(requests)
        }
        for future in as_completed(futures):
            index = futures[future]
            try:
                results[index] = future.result()
            except Exception as exc:  # noqa: BLE001 - never crash the batch
                results[index] = (
                    {
                        "asset_id": str(requests[index].get("asset_id", "")),
                        "status": AssetStatus.FAILED,
                        "error": str(exc)[:200],
                    },
                    {
                        "job_id": f"genjob_err_{index}",
                        "asset_id": str(requests[index].get("asset_id", "")),
                        "status": JobStatus.FAILED,
                        "error": str(exc)[:200],
                        "attempts": 0,
                        "providers_tried": [],
                        "cache_hit": False,
                        "cost_estimate": 0.0,
                        "latency_ms": 0,
                        "created_at": _now_iso(),
                    },
                )
    return [results[index] for index in range(len(requests))]
