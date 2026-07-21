"""Category 6 — Quality score acceptance."""

from __future__ import annotations

import time

from services.production_acceptance.models import TestResult

QUALITY_KEYS = (
    "hook_score",
    "narration_score",
    "visual_score",
    "audio_score",
    "caption_score",
    "educational_accuracy",
    "retention_prediction",
    "ctr_prediction",
    "completion_prediction",
    "shareability",
    "overall_quality_score",
)


def run_quality_tests(mode: str = "smoke") -> list[TestResult]:
    from services.production_operations import run_studio_ops

    t0 = time.time()
    results: list[TestResult] = []
    try:
        out = run_studio_ops(
            topic="Quality acceptance — curiosity gap in human attention",
            platform="youtube_shorts",
            length_sec=45,
            style="psychology",
            narrator="professor",
            quality_target=90,
        )
        report = out.get("report") or {}
        missing = [k for k in QUALITY_KEYS if k not in report]
        # Soft floors for acceptance (prove scores exist + sane ranges)
        floors = {
            "hook_score": 1,
            "narration_score": 1,
            "visual_score": 1,
            "audio_score": 1,
            "caption_score": 1,
            "educational_accuracy": 1,
            "retention_prediction": 1,
            "ctr_prediction": 0.1,
            "completion_prediction": 1,
            "shareability": 1,
            "overall_quality_score": 50,
        }
        bad = []
        for k, floor in floors.items():
            val = report.get(k)
            try:
                if val is None or float(val) < floor:
                    bad.append(k)
            except (TypeError, ValueError):
                bad.append(k)

        # Named dimension aliases for mission wording
        aliases_ok = {
            "hook_quality": report.get("hook_score") is not None,
            "visual_pacing": report.get("visual_score") is not None,
            "scene_quality": report.get("visual_score") is not None,
            "animation_quality": report.get("visual_score") is not None,
            "seo_quality": bool((out.get("context") or {}).get("seo_package") or report.get("platform_readiness") is not None),
        }
        ok = not missing and not bad and all(aliases_ok.values()) and bool(out.get("succeeded"))
        results.append(
            TestResult(
                category="quality",
                name="quality_dimensions_present",
                passed=ok,
                duration_ms=int((time.time() - t0) * 1000),
                message=f"missing={missing} below_floor={bad}",
                metrics={
                    **{k: report.get(k) for k in QUALITY_KEYS},
                    "overall_quality": report.get("overall_quality_score"),
                    "render_time_ms": out.get("elapsed_ms"),
                    "aliases": aliases_ok,
                    "recommendation": report.get("final_recommendation"),
                },
                warnings=[f"below_floor:{k}" for k in bad],
            )
        )
    except Exception as exc:  # noqa: BLE001
        results.append(
            TestResult(
                category="quality",
                name="quality_dimensions_present",
                passed=False,
                duration_ms=int((time.time() - t0) * 1000),
                errors=[str(exc)],
                message=str(exc),
            )
        )
    return results
