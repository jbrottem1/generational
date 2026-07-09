"""Batch / campaign / series animation planning helpers.

Supports parallel planning across large campaigns, multi-video productions,
and series episodes without changing the per-item package contract.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from services.animation.config import AnimationConfig, get_animation_config
from services.animation.package import build_animation_package, plan_items


def batch_plan(
    items: "list[dict]",
    context: "dict | None" = None,
    config: "AnimationConfig | None" = None,
    max_workers: int = 8,
) -> dict:
    """Plan many items and return an aggregate batch result."""
    resolved = config or get_animation_config()
    # Force parallel for batch entrypoint regardless of config flag.
    workers = max(1, min(max_workers, len(items) or 1))

    def _one(item: dict) -> dict:
        package = build_animation_package(item, context, resolved)
        item["animation_package"] = package
        return package

    if len(items) <= 1:
        packages = [_one(item) for item in items]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            packages = list(pool.map(_one, items))

    readiness = [p.get("production_readiness", {}) for p in packages]
    return {
        "batch_id": f"anim_batch_{len(items)}",
        "items": len(items),
        "packages": packages,
        "ready": sum(1 for r in readiness if r.get("status") == "ready"),
        "needs_review": sum(1 for r in readiness if r.get("status") == "needs_review"),
        "incomplete": sum(1 for r in readiness if r.get("status") == "incomplete"),
        "total_duration_sec": round(
            sum(float((p.get("timeline") or {}).get("total_duration_sec", 0) or 0) for p in packages),
            3,
        ),
    }


def plan_series(
    episodes: "list[dict]",
    series_id: str,
    context: "dict | None" = None,
    config: "AnimationConfig | None" = None,
) -> dict:
    """Plan a series: stamps series_id / episode_index then batch-plans."""
    for index, episode in enumerate(episodes, start=1):
        episode["series_id"] = series_id
        episode["episode_index"] = index
    result = batch_plan(episodes, context, config)
    result["series_id"] = series_id
    result["episodes"] = len(episodes)
    return result


def prepare_render_batch(packages: "list[dict]") -> dict:
    """Collapse animation packages into a render-prep manifest (no pixels)."""
    jobs = []
    for package in packages:
        export = package.get("export_metadata") or {}
        jobs.append({
            "project_id": package.get("project_id", ""),
            "duration_sec": (package.get("timeline") or {}).get("total_duration_sec", 0),
            "fps": export.get("fps"),
            "aspect_ratio": export.get("aspect_ratio"),
            "shot_count": len((package.get("camera_plan") or {}).get("shots") or []),
            "provider_instructions": len(package.get("provider_instructions") or []),
            "readiness": (package.get("production_readiness") or {}).get("status", ""),
        })
    return {
        "job_count": len(jobs),
        "jobs": jobs,
        "ready_jobs": sum(1 for job in jobs if job["readiness"] == "ready"),
    }


# Re-export plan_items for callers that want the engine-equivalent path.
__all__ = ["batch_plan", "plan_items", "plan_series", "prepare_render_batch"]
