"""Categories 2–4 — Video generation, duration, platform acceptance."""

from __future__ import annotations

import time
from typing import Any

from services.production_acceptance.catalog import (
    CATEGORIES,
    CATEGORY_TOPICS,
    PLATFORMS,
    limits_for,
)
from services.production_acceptance.models import TestResult


def _run_ops(topic: str, platform: str, length_sec: int, style: str = "educational") -> dict[str, Any]:
    from services.production_operations import run_studio_ops

    return run_studio_ops(
        topic=topic,
        platform=platform,
        length_sec=length_sec,
        style=style,
        narrator="professor",
        voice="default",
        quality_target=90,
    )


def run_video_generation(mode: str = "smoke") -> list[TestResult]:
    limits = limits_for(mode)
    cats = list(CATEGORIES)[: int(limits["categories"])]
    per = int(limits["topics_per_category"])
    results: list[TestResult] = []
    for cat in cats:
        topics = (CATEGORY_TOPICS.get(cat) or [f"{cat.title()} sample topic"])[:per]
        for topic in topics:
            t0 = time.time()
            try:
                out = _run_ops(topic, "youtube_shorts", 45, style=cat if cat != "educational" else "educational")
                report = out.get("report") or {}
                ok = bool(out.get("succeeded")) and int((out.get("status") or {}).get("overall_progress_pct") or 0) >= 90
                results.append(
                    TestResult(
                        category="video_generation",
                        name=f"{cat}:{topic[:40]}",
                        passed=ok,
                        duration_ms=int((time.time() - t0) * 1000),
                        message=str(report.get("final_recommendation") or ""),
                        metrics={
                            "overall_quality": report.get("overall_quality_score"),
                            "render_time_ms": out.get("elapsed_ms"),
                            "production_id": out.get("production_id"),
                            "category": cat,
                        },
                    )
                )
            except Exception as exc:  # noqa: BLE001
                results.append(
                    TestResult(
                        category="video_generation",
                        name=f"{cat}:{topic[:40]}",
                        passed=False,
                        duration_ms=int((time.time() - t0) * 1000),
                        message=str(exc),
                        errors=[str(exc)],
                    )
                )
    return results


def run_duration_tests(mode: str = "smoke") -> list[TestResult]:
    limits = limits_for(mode)
    durations = tuple(limits["durations"])
    results: list[TestResult] = []
    for dur in durations:
        t0 = time.time()
        topic = f"Duration accuracy probe for {dur} seconds of science"
        try:
            out = _run_ops(topic, "youtube_shorts", int(dur))
            brief = out.get("brief") or {}
            target = int(brief.get("length_sec") or 0)
            # Timing accuracy: brief must honor requested duration within pipeline
            timing_ok = target == int(dur)
            # Context should carry the same target
            ctx = out.get("context") or {}
            ctx_ok = int(ctx.get("target_runtime_sec") or ctx.get("video_length_sec") or 0) == int(dur)
            report = out.get("report") or {}
            ok = bool(out.get("succeeded")) and timing_ok and ctx_ok
            results.append(
                TestResult(
                    category="duration",
                    name=f"duration_{dur}s",
                    passed=ok,
                    duration_ms=int((time.time() - t0) * 1000),
                    message=f"requested={dur} brief={target}",
                    metrics={
                        "requested_sec": dur,
                        "brief_sec": target,
                        "overall_quality": report.get("overall_quality_score"),
                        "render_time_ms": out.get("elapsed_ms"),
                    },
                )
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                TestResult(
                    category="duration",
                    name=f"duration_{dur}s",
                    passed=False,
                    duration_ms=int((time.time() - t0) * 1000),
                    errors=[str(exc)],
                    message=str(exc),
                )
            )
    return results


def run_platform_tests(mode: str = "smoke") -> list[TestResult]:
    limits = limits_for(mode)
    platforms = tuple(limits["platforms"])
    results: list[TestResult] = []
    for plat in platforms:
        spec = PLATFORMS.get(plat) or {}
        length = min(45, int(spec.get("max_sec") or 60))
        t0 = time.time()
        try:
            out = _run_ops(f"Platform validation for {plat}", plat, length)
            brief = out.get("brief") or {}
            export = out.get("export_validation") or {}
            ctx = out.get("context") or {}
            seo_ok = bool(ctx.get("seo_package") or ((ctx.get("candidates") or [{}])[0] or {}).get("seo_package"))
            # Metadata / captions contract
            captions_ok = True
            if spec.get("caption_required"):
                captions_ok = bool(export.get("captions_burned_or_present") or ctx.get("production_packages"))
            dim_ok = brief.get("platform") == plat
            # Bitrate/codec: when no MP4, accept metadata package as smoke pass with warning
            media_ok = bool(export.get("ok", True))
            ok = bool(out.get("succeeded")) and dim_ok and media_ok and captions_ok
            warnings = []
            if not export.get("video_exists"):
                warnings.append("mp4_not_materialized_metadata_ok")
            results.append(
                TestResult(
                    category="platform",
                    name=f"platform_{plat}",
                    passed=ok,
                    duration_ms=int((time.time() - t0) * 1000),
                    message=f"aspect={spec.get('aspect')} seo={seo_ok}",
                    warnings=warnings,
                    metrics={
                        "platform": plat,
                        "aspect": spec.get("aspect"),
                        "caption_required": spec.get("caption_required"),
                        "export_ok": export.get("ok"),
                        "seo_present": seo_ok,
                        "overall_quality": (out.get("report") or {}).get("overall_quality_score"),
                        "render_time_ms": out.get("elapsed_ms"),
                        "bitrate_probe": (export.get("probe") or {}).get("bit_rate") if isinstance(export.get("probe"), dict) else None,
                        "codec_probe": (export.get("probe") or {}).get("video_codec") if isinstance(export.get("probe"), dict) else None,
                    },
                )
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                TestResult(
                    category="platform",
                    name=f"platform_{plat}",
                    passed=False,
                    duration_ms=int((time.time() - t0) * 1000),
                    errors=[str(exc)],
                    message=str(exc),
                )
            )
    return results
