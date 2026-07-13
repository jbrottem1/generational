"""Master production pipeline runner — Studio → Workflow Executor → Orchestrator.

No stage bypasses the orchestrator. This module is a thin façade that selects
short-form / long-form production types and returns a normalized result.
"""

from __future__ import annotations

from typing import Any

from core.log import get_logger
from services.master_pipeline.contracts import contract_audit, normalize_pipeline_context
from services.master_pipeline.qc import run_production_qc
from services.master_pipeline.registry import master_pipeline_map, registry_summary

logger = get_logger(__name__)

SHORT_FORM_DURATIONS = {
    15: "youtube_short",
    30: "youtube_short",
    60: "youtube_short",
    90: "youtube_short",
}

SHORT_FORM_PLATFORMS = {
    "youtube_shorts": "youtube_short",
    "tiktok": "youtube_short",
    "instagram_reels": "youtube_short",
    "facebook": "youtube_short",
}

LONG_FORM_DURATIONS = {
    300: "longform",      # 5 min
    600: "longform",      # 10 min
    1200: "longform",     # 20 min
    1800: "longform",     # 30 min
    3600: "longform",     # 60 min
}

LONG_FORM_PLATFORMS = {
    "youtube_long": "longform",
    "documentary": "documentary",
    "podcast": "podcast",
    "course": "course",
    "animated_series": "animated_episode",
}


def resolve_production_type(
    *,
    platform: str = "youtube_shorts",
    duration_sec: int = 60,
    production_type: str = "",
) -> str:
    if production_type:
        return production_type
    if platform in LONG_FORM_PLATFORMS:
        return LONG_FORM_PLATFORMS[platform]
    # Duration wins over short-form platform default when clearly long-form.
    if duration_sec >= 300:
        for boundary, ptype in sorted(LONG_FORM_DURATIONS.items()):
            if duration_sec <= boundary:
                return ptype
        return "longform"
    if platform in SHORT_FORM_PLATFORMS:
        return SHORT_FORM_PLATFORMS[platform]
    if duration_sec in SHORT_FORM_DURATIONS:
        return SHORT_FORM_DURATIONS[duration_sec]
    return "youtube_short"


def run_master_production(
    prompt: str,
    *,
    platform: str = "youtube_shorts",
    duration_sec: int = 60,
    production_type: str = "",
    publish_mode: str = "dry_run",
    project_name: str = "",
    settings: dict | None = None,
) -> dict[str, Any]:
    """Execute one full production through Workflow Executor → Orchestrator."""
    from services.studio.production import run_studio_production
    from services.studio import build_default_settings

    ptype = resolve_production_type(
        platform=platform,
        duration_sec=duration_sec,
        production_type=production_type,
    )
    studio_settings = build_default_settings()
    studio_settings.update(settings or {})
    studio_settings["platform"] = platform
    studio_settings["video_length_sec"] = int(duration_sec)
    studio_settings["publish_mode"] = publish_mode
    studio_settings["production_type"] = ptype

    logger.info(
        "master_pipeline.start | platform=%s duration=%s type=%s publish_mode=%s",
        platform,
        duration_sec,
        ptype,
        publish_mode,
    )

    result = run_studio_production(
        prompt,
        studio_settings,
        project_name=project_name or None,
    )

    # Normalize packages on the result dict
    contextish = {
        "unified_packages": result.get("unified_packages") or result.get("packages") or [],
        "production_packages": result.get("production_packages") or [],
        "publishing_packages": result.get("publishing_packages") or [],
        "stage_reports": result.get("stage_reports") or result.get("pipeline_steps") or [],
    }
    normalized = normalize_pipeline_context(contextish)
    packages = normalized.get("unified_packages") or []
    audits = [contract_audit(p if isinstance(p, dict) else {}) for p in packages[:5]]
    qc = run_production_qc(result, normalized)

    report_paths: dict = {}
    try:
        from services.media_production.reports import write_full_report_bundle

        render_packages = [
            (p.get("render_package") if isinstance(p, dict) else {}) or {}
            for p in packages
            if isinstance(p, dict)
        ]
        report_paths = write_full_report_bundle(
            {**result, "qc": qc},
            render_packages=render_packages[:5],
            metrics={
                "tokens_used": result.get("token_usage") or result.get("tokens_used"),
                "notes": [f"production_type={ptype}", f"publish_mode={publish_mode}"],
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("master_pipeline.reports_failed | error=%s", exc)

    output = {
        **result,
        "master_pipeline": {
            "platform": platform,
            "duration_sec": duration_sec,
            "production_type": ptype,
            "publish_mode": publish_mode,
            "stages": master_pipeline_map(),
            "contract_audits": audits,
            "qc": qc,
            "reports": report_paths,
            "registry": {
                "engines_ready": registry_summary().get("engines_ready"),
                "engine_count": registry_summary().get("engine_count"),
            },
        },
        "unified_packages": packages,
        "qc": qc,
        "reports": report_paths,
    }
    logger.info(
        "master_pipeline.complete | ok=%s qc_score=%s packages=%s",
        qc.get("passed"),
        qc.get("score"),
        len(packages),
    )
    return output
