"""Category 5 — Stress tests (resource + queue)."""

from __future__ import annotations

import os
import time
from typing import Any

from services.production_acceptance.catalog import limits_for
from services.production_acceptance.models import TestResult


def _resource_snapshot() -> dict[str, Any]:
    snap: dict[str, Any] = {"pid": os.getpid()}
    try:
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF)
        snap["max_rss_kb"] = int(getattr(usage, "ru_maxrss", 0) or 0)
        snap["user_time_sec"] = round(float(usage.ru_utime), 3)
        snap["system_time_sec"] = round(float(usage.ru_stime), 3)
    except Exception:  # noqa: BLE001
        snap["max_rss_kb"] = None
    try:
        import shutil

        disk = shutil.disk_usage(".")
        snap["disk_free_gb"] = round(disk.free / (1024**3), 2)
        snap["disk_total_gb"] = round(disk.total / (1024**3), 2)
    except Exception:  # noqa: BLE001
        pass
    # GPU optional
    snap["gpu"] = "not_probed"
    try:
        import subprocess

        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if out.returncode == 0 and out.stdout.strip():
            snap["gpu"] = out.stdout.strip().splitlines()[0]
    except Exception:  # noqa: BLE001
        snap["gpu"] = "unavailable"
    return snap


def run_stress_tests(mode: str = "smoke") -> list[TestResult]:
    from services.production_operations import enqueue_production, queue_summary, run_studio_ops

    limits = limits_for(mode)
    results: list[TestResult] = []
    counts = tuple(limits["stress_counts"])

    for n in counts:
        t0 = time.time()
        before = _resource_snapshot()
        ok_count = 0
        elapsed_sum = 0
        try:
            for i in range(int(n)):
                out = run_studio_ops(
                    topic=f"Stress sample {n}-{i} photosynthesis tip",
                    platform="youtube_shorts",
                    length_sec=30,
                    style="science",
                )
                if out.get("succeeded"):
                    ok_count += 1
                elapsed_sum += int(out.get("elapsed_ms") or 0)
            after = _resource_snapshot()
            ok = ok_count == n
            results.append(
                TestResult(
                    category="stress",
                    name=f"generate_{n}_videos",
                    passed=ok,
                    duration_ms=int((time.time() - t0) * 1000),
                    message=f"ok={ok_count}/{n}",
                    metrics={
                        "count": n,
                        "succeeded": ok_count,
                        "avg_render_time_ms": int(elapsed_sum / max(n, 1)),
                        "render_time_ms": int(elapsed_sum / max(n, 1)),
                        "resources_before": before,
                        "resources_after": after,
                        "rss_delta_kb": (
                            (after.get("max_rss_kb") or 0) - (before.get("max_rss_kb") or 0)
                            if after.get("max_rss_kb") and before.get("max_rss_kb")
                            else None
                        ),
                    },
                )
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                TestResult(
                    category="stress",
                    name=f"generate_{n}_videos",
                    passed=False,
                    duration_ms=int((time.time() - t0) * 1000),
                    errors=[str(exc)],
                    message=str(exc),
                )
            )

    # Queue burst
    queued = int(limits["queued_jobs"])
    t0 = time.time()
    try:
        # For smoke, run_immediately False for most then drain a few; for higher counts enqueue metadata
        job_ids = []
        for i in range(queued):
            # run_immediately only for first few to keep suite bounded
            immediate = i < min(3, queued)
            out = enqueue_production(
                topic=f"Queued acceptance job {i}",
                platform="youtube_shorts",
                length_sec=20,
                priority=(queued - i),
                run_immediately=immediate,
            )
            job_ids.append(out.get("job_id"))
        summary = queue_summary()
        ok = len(job_ids) == queued
        results.append(
            TestResult(
                category="stress",
                name=f"queue_{queued}_jobs",
                passed=ok,
                duration_ms=int((time.time() - t0) * 1000),
                message=f"enqueued={len(job_ids)} summary={summary.get('pending')}/{summary.get('succeeded')}",
                metrics={
                    "queued": queued,
                    "job_ids": job_ids[:10],
                    "queue_summary": summary,
                    "render_time_ms": int((time.time() - t0) * 1000),
                },
            )
        )
    except Exception as exc:  # noqa: BLE001
        results.append(
            TestResult(
                category="stress",
                name=f"queue_{queued}_jobs",
                passed=False,
                duration_ms=int((time.time() - t0) * 1000),
                errors=[str(exc)],
                message=str(exc),
            )
        )

    # Recovery probe under stress: missing engine continues
    t0 = time.time()
    from services.production_operations.resilience import run_engine_with_retries

    rec = run_engine_with_retries("does_not_exist_stress", {}, max_retries=1)
    results.append(
        TestResult(
            category="stress",
            name="recovery_under_stress",
            passed=rec.get("status") == "skipped" and rec.get("fallback") is True,
            duration_ms=int((time.time() - t0) * 1000),
            message=str(rec.get("error") or "fallback_ok"),
            metrics=rec,
        )
    )
    return results
