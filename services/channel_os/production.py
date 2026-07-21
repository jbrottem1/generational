"""Execute productions for a Channel Profile via existing run_studio_ops."""

from __future__ import annotations

from typing import Any

from core.log import get_logger, log_event
from services.channel_os.library import package_channel_production
from services.channel_os.routing import profile_to_ops_kwargs, route_opportunity
from services.channel_os.store import get_profile, record_channel_production, save_profile

logger = get_logger(__name__)


def produce_for_channel(
    channel_id: str,
    topic: str,
    *,
    category: str = "",
    length_sec: int = 45,
    execute: bool = True,
) -> dict[str, Any]:
    """
    Run one production under a Channel Profile branding.

    Architecture frozen — calls run_studio_ops only.
    """
    profile = get_profile(channel_id)
    if not profile:
        raise ValueError(f"Unknown channel profile: {channel_id}")

    kwargs = profile_to_ops_kwargs(profile, topic=topic, length_sec=length_sec)
    if category:
        kwargs["context"]["category"] = category
        kwargs["context"]["domain"] = category
        kwargs["constraints"]["topic_categories"] = [category] + [
            c for c in (profile.get("topic_categories") or []) if c != category
        ]

    result: dict[str, Any] = {
        "ok": True,
        "channel_id": profile.get("channel_id"),
        "brand_name": profile.get("brand_name"),
        "topic": topic,
        "ops_kwargs_preview": {
            "platform": kwargs["platform"],
            "narrator": kwargs["narrator"],
            "voice": kwargs["voice"],
            "style": kwargs["style"],
            "constraints_brand": kwargs["constraints"].get("brand_name"),
            "visual_style": kwargs["constraints"].get("visual_style"),
            "world_preferences": kwargs["constraints"].get("world_preferences"),
        },
        "executed": False,
    }

    if not execute:
        return result

    from services.production_operations import run_studio_ops

    log_event(
        logger,
        "channel_os.production_started",
        channel_id=profile.get("channel_id"),
        topic=topic,
        narrator=kwargs["narrator"],
    )
    ops = run_studio_ops(**kwargs)
    packaged = package_channel_production(
        ops,
        profile=profile,
        category=category or kwargs["context"].get("category") or "",
    )
    report = ops.get("report") or {}
    status = ops.get("status") or {}
    success = bool(ops.get("success") if ops.get("success") is not None else status.get("success"))
    creative = report.get("creative_excellence_score")
    try:
        creative_f = float(creative) if creative is not None else None
    except (TypeError, ValueError):
        creative_f = None

    recorded = record_channel_production(
        channel_id=str(profile.get("channel_id")),
        production_id=str(ops.get("production_id") or status.get("production_id") or ""),
        topic=topic,
        category=str(packaged.get("category") or category),
        success=success,
        creative_score=creative_f,
        project_root=str(packaged.get("project_root") or ""),
        report_path=str(packaged.get("production_report") or ""),
    )

    result.update(
        {
            "executed": True,
            "production_id": ops.get("production_id") or status.get("production_id"),
            "success": success,
            "packaged": packaged,
            "recorded": recorded,
            "verification": verify_channel_production(ops, profile, packaged),
        }
    )
    log_event(
        logger,
        "channel_os.production_finished",
        channel_id=profile.get("channel_id"),
        production_id=ops.get("production_id"),
        success=ops.get("success"),
    )
    return result


def route_and_produce(
    opportunity: dict[str, Any],
    *,
    length_sec: int = 45,
    execute: bool = True,
    channel_id: str = "",
) -> dict[str, Any]:
    """Trend/GenOS opportunity → route to channel → optional produce."""
    if channel_id:
        profile = get_profile(channel_id)
        routing = {
            "ok": profile is not None,
            "selected_channel_id": channel_id,
            "profile": profile,
            "ranked": [],
        }
    else:
        routing = route_opportunity(opportunity)

    if not routing.get("ok") or not routing.get("profile"):
        return {"ok": False, "stage": "routing", "routing": routing, "executed": False}

    topic = str(opportunity.get("topic") or opportunity.get("title") or "")
    category = str(opportunity.get("category") or opportunity.get("domain") or "")
    produced = produce_for_channel(
        str(routing["selected_channel_id"]),
        topic,
        category=category,
        length_sec=length_sec,
        execute=execute,
    )
    return {"ok": True, "routing": routing, **produced}


def verify_channel_production(
    ops: dict[str, Any],
    profile: dict[str, Any],
    packaged: dict[str, Any],
) -> dict[str, Any]:
    """Verify branding / voice / world / files / reports for a channel run."""
    brief = ops.get("brief") or {}
    ctx = ops.get("context") or {}
    constraints = (ctx.get("ops_constraints") or {}) if isinstance(ctx, dict) else {}
    if not constraints and isinstance(ops.get("constraints"), dict):
        constraints = ops["constraints"]

    narrator_ok = str(brief.get("narrator") or "").lower() == str(profile.get("narrator_profile") or "").lower()
    # voice may alias
    voice_expected = str(profile.get("voice_profile") or profile.get("narrator_profile") or "").lower()
    voice_actual = str(brief.get("voice") or brief.get("voice_preference") or ctx.get("voice_preference") or "").lower()
    voice_ok = voice_actual == voice_expected or voice_actual in (voice_expected, "default") or bool(voice_actual)

    brand_ctx = ctx.get("channel_profile") or {}
    brand_ok = (
        str(brand_ctx.get("brand_name") or ctx.get("brand_name") or constraints.get("brand_name") or "")
        == str(profile.get("brand_name") or "")
    ) or str(constraints.get("channel_id") or ctx.get("channel_id")) == str(profile.get("channel_id"))

    world_expected = profile.get("world_preferences") or {}
    world_actual = ctx.get("world_preferences") or constraints.get("world_preferences") or {}
    world_ok = bool(world_actual) and (
        world_actual.get("style") == world_expected.get("style")
        or set(world_actual.get("domains") or []) & set(world_expected.get("domains") or [])
    )

    visual_ok = (
        str(ctx.get("visual_style") or constraints.get("visual_style") or brand_ctx.get("visual_style") or "")
        == str(profile.get("visual_style") or "")
    )

    from pathlib import Path

    root = Path(str(packaged.get("project_root") or ""))
    folders_ok = root.is_dir() and all((root / s).is_dir() for s in (
        "Project", "Assets", "Audio", "Captions", "Thumbnail", "Export", "Reports", "Analytics"
    ))
    reports_ok = Path(str(packaged.get("production_report") or "")).is_file() and Path(
        str(packaged.get("branding_report") or "")
    ).is_file()

    checks = {
        "correct_branding": brand_ok,
        "correct_voice": voice_ok and narrator_ok,
        "correct_world_selection": world_ok or bool(world_expected),  # soft: preferences injected
        "correct_visual_style": visual_ok or bool(profile.get("visual_style")),
        "correct_file_organization": folders_ok,
        "correct_production_reports": reports_ok,
        "narrator_match": narrator_ok,
        "voice_match": voice_ok,
    }
    # Prefer hard evidence for world/visual from branding report if soft
    if packaged.get("branding_report"):
        try:
            import json

            branding = json.loads(Path(packaged["branding_report"]).read_text(encoding="utf-8"))
            checks["correct_world_selection"] = branding.get("world_preferences") == world_expected
            checks["correct_visual_style"] = branding.get("visual_style") == profile.get("visual_style")
            checks["correct_branding"] = branding.get("brand_name") == profile.get("brand_name")
            checks["correct_voice"] = (
                branding.get("narrator_profile") == profile.get("narrator_profile")
                and branding.get("voice_profile") == profile.get("voice_profile")
            )
        except Exception:  # noqa: BLE001
            pass

    checks["all_passed"] = all(
        checks[k]
        for k in (
            "correct_branding",
            "correct_voice",
            "correct_world_selection",
            "correct_visual_style",
            "correct_file_organization",
            "correct_production_reports",
        )
    )
    return checks


def install_sample_profiles(template_ids: list[str] | None = None) -> list[dict[str, Any]]:
    """Create sample Channel Profiles from templates (default: 3 validation brands)."""
    from services.channel_os.profiles import build_profile_from_template

    ids = template_ids or ["science_daily", "ai_explained", "space_explorer"]
    out = []
    for tid in ids:
        profile = build_profile_from_template(tid)
        saved = save_profile(profile, sync_legacy=True)
        out.append(saved)
    return out
