"""Production Operations orchestrator — Agent 0 command center entry.

One brief → 16 monitored stages → export validation → report → history.
Never terminates on stage failure (retry / repair / fallback / continue).
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any

from core.log import get_logger, log_event
from services.production_operations.brief import StudioBrief, brief_to_context, build_studio_brief
from services.production_operations.history import store_production
from services.production_operations.report import build_production_report, write_production_report
from services.production_operations.resilience import run_stage_engines
from services.production_operations.services_steps import apply_music_direction, export_and_validate
from services.production_operations.stages import OPERATIONS_STAGES
from services.production_operations.status import (
    build_live_dashboard,
    new_ops_status,
    update_stage,
    write_ops_status,
)
from services.production_pipeline.bridges import bridge_before_stage, validation_score

logger = get_logger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _map_bridge_key(ops_key: str) -> str:
    """Reuse production_pipeline bridges where stage keys align."""
    mapping = {
        "research": "research",
        "psychology": "psychology",
        "studio_director": "studio_director",
        "script_generator": "script_generator",
        "scene_builder": "scene_builder",
        "media_collection": "media_generation",
        "animation": "media_generation",
        "voice_generation": "voice_generation",
        "music_sound": "voice_generation",
        "captions": "video_assembly",
        "rendering": "video_assembly",
        "viewer_retention": "video_assembly",
        "optimization_lab": "export",
        "quality_assurance": "quality_control",
        "seo_package": "quality_control",
        "export": "export",
    }
    return mapping.get(ops_key, "research")


def run_studio_ops(
    *,
    topic: str = "",
    platform: str = "youtube_shorts",
    length_sec: int = 60,
    style: str = "educational",
    narrator: str = "professor",
    voice: str = "default",
    quality_target: float = 98.0,
    constraints: dict | None = None,
    command: str = "",
    production_id: str = "",
    resume: bool = False,
    context: dict | None = None,
) -> dict[str, Any]:
    """Execute a full studio production with live monitoring."""
    import engines  # noqa: F401

    brief_obj: StudioBrief = build_studio_brief(
        topic=topic,
        platform=platform,
        length_sec=length_sec,
        style=style,
        narrator=narrator,
        voice=voice,
        quality_target=quality_target,
        constraints=constraints,
        command=command,
    )
    brief = brief_obj.to_dict()
    pid = production_id or f"ops_{uuid.uuid4().hex[:10]}"
    ctx: dict[str, Any] = {**brief_to_context(brief_obj), **(context or {})}
    ctx["production_id"] = pid
    ctx["project_id"] = pid
    ctx.setdefault("command", brief_obj.to_command())

    status = new_ops_status(pid, brief)
    if resume:
        # Stage-skip resume is not implemented; flag is a full re-run marker until C3 lands
        status["notes"] = [
            "resumed",
            "resume_mode=full_rerun — completed stages are not skipped yet",
        ]
    write_ops_status(pid, status)
    build_live_dashboard(status)

    log_event(
        logger,
        "ops.production_started",
        production_id=pid,
        topic=brief_obj.topic,
        platform=brief_obj.platform,
        length_sec=brief_obj.length_sec,
    )

    t0 = time.time()
    quality_scores: dict[str, float] = {}

    for stage in OPERATIONS_STAGES:
        stage_key = stage["key"]
        ctx = bridge_before_stage(_map_bridge_key(stage_key), ctx)
        agents = list(stage.get("engines") or []) or [stage.get("service_step") or stage_key]
        status = update_stage(
            status,
            stage_key,
            phase="start",
            current_agent=agents[0],
        )
        write_ops_status(pid, status)
        build_live_dashboard(status)

        started = time.time()
        log_event(logger, "ops.stage_started", production_id=pid, stage=stage_key)

        service = stage.get("service_step")
        if service == "apply_music_direction":
            result = apply_music_direction(ctx)
        elif service == "export_and_validate":
            result = export_and_validate(ctx, production_id=pid, topic=brief_obj.topic)
        else:
            result = run_stage_engines(stage, ctx)

        elapsed = int((time.time() - started) * 1000)
        if not result.get("duration_ms"):
            result["duration_ms"] = elapsed

        q = float(result.get("quality_score") or validation_score(ctx, _map_bridge_key(stage_key)))
        quality_scores[stage_key] = q
        files = list(result.get("output_files") or [])
        if files:
            status["current_files"] = list(dict.fromkeys((status.get("current_files") or []) + files))

        failure_reason = ""
        if result.get("errors"):
            failure_reason = "; ".join(str(e) for e in (result.get("errors") or [])[:3])
        elif any("unavailable" in str(w).lower() for w in (result.get("warnings") or [])):
            failure_reason = next(
                (str(w) for w in (result.get("warnings") or []) if "unavailable" in str(w).lower()),
                "",
            )
        status = update_stage(
            status,
            stage_key,
            phase="finish",
            duration_ms=int(result.get("duration_ms") or elapsed),
            warnings=list(result.get("warnings") or []),
            errors=list(result.get("errors") or []),
            retries=int(result.get("retries") or 0),
            quality_score=q,
            output_files=files,
            current_agent=agents[0],
            stage_status=str(result.get("status") or "succeeded"),
            engine_results=list(result.get("engine_results") or []),
            artifacts=files,
            failure_reason=failure_reason,
            outputs_produced=list(result.get("outputs_produced") or files),
            dependency_health={
                "engine_count": len(result.get("engine_results") or []),
                "skipped": sum(
                    1 for r in (result.get("engine_results") or []) if r.get("status") == "skipped"
                ),
                "failed_continued": sum(
                    1
                    for r in (result.get("engine_results") or [])
                    if r.get("status") == "failed_continued"
                ),
            },
        )
        status["quality_scores"] = quality_scores
        write_ops_status(pid, status)
        build_live_dashboard(status)

        log_event(
            logger,
            "ops.stage_finished",
            production_id=pid,
            stage=stage_key,
            status=result.get("status"),
            duration_ms=result.get("duration_ms"),
            retries=result.get("retries"),
            quality_score=q,
        )

        # Golden / brief hook enforcement — soft overwrite when mission supplies hook_required
        if stage_key == "script_generator":
            try:
                cons = dict(brief_obj.constraints or {})
                required_hook = str(cons.get("hook_required") or ctx.get("hook") or "").strip()
                if required_hook and (
                    cons.get("golden_production") or cons.get("enforce_hook") or ctx.get("golden_production")
                ):

                    def _swap_open(text: str) -> str:
                        body = str(text or "").strip()
                        if not body:
                            return required_hook
                        if body.startswith(required_hook):
                            return body
                        # Drop first sentence / clause so voice TTS hears the mission hook first
                        for sep in (". ", "? ", "! ", " — ", " —", " - "):
                            if sep in body:
                                rest = body.split(sep, 1)[1].strip()
                                if rest:
                                    return f"{required_hook} {rest}"
                        return f"{required_hook} {body}"

                    cands = list(ctx.get("candidates") or [])
                    if cands and isinstance(cands[0], dict):
                        top = dict(cands[0])
                        top["hook"] = required_hook
                        top["primary_hook"] = required_hook
                        if top.get("script"):
                            top["script"] = _swap_open(str(top.get("script") or ""))
                        if top.get("narration"):
                            top["narration"] = _swap_open(str(top.get("narration") or ""))
                        sections = list(top.get("sections") or [])
                        if sections and isinstance(sections[0], dict):
                            sec0 = dict(sections[0])
                            sec0["narration"] = required_hook
                            sections[0] = sec0
                            top["sections"] = sections
                        # Root-level scene plan (common ops shape)
                        breakdown = list(top.get("scene_breakdown") or [])
                        if breakdown and isinstance(breakdown[0], dict):
                            first = dict(breakdown[0])
                            first["narration"] = required_hook
                            first["purpose"] = first.get("purpose") or "hook"
                            breakdown[0] = first
                            top["scene_breakdown"] = breakdown
                        if not top.get("script") and top.get("narration"):
                            top["script"] = top["narration"]
                        elif top.get("script") and isinstance(top.get("script"), str):
                            top["script"] = _swap_open(str(top.get("script") or ""))

                        ss = dict(top.get("structured_script") or {})
                        if ss:
                            ss["hook"] = required_hook
                            ss["primary_hook"] = required_hook
                            if ss.get("full_script"):
                                ss["full_script"] = _swap_open(str(ss.get("full_script") or ""))
                            if ss.get("narration"):
                                ss["narration"] = _swap_open(str(ss.get("narration") or ""))
                            ss_break = list(ss.get("scene_breakdown") or [])
                            if ss_break and isinstance(ss_break[0], dict):
                                f0 = dict(ss_break[0])
                                f0["narration"] = required_hook
                                f0["purpose"] = f0.get("purpose") or "hook"
                                ss_break[0] = f0
                                ss["scene_breakdown"] = ss_break
                            ss_sec = list(ss.get("sections") or [])
                            if ss_sec and isinstance(ss_sec[0], dict):
                                s0 = dict(ss_sec[0])
                                s0["narration"] = required_hook
                                ss_sec[0] = s0
                                ss["sections"] = ss_sec
                            top["structured_script"] = ss

                        sp = dict(top.get("script_package") or {})
                        if sp:
                            sp["hook"] = required_hook
                            if isinstance(sp.get("structured_script"), dict):
                                ssp = dict(sp["structured_script"])
                                ssp["hook"] = required_hook
                                ssp["primary_hook"] = required_hook
                                if ssp.get("full_script"):
                                    ssp["full_script"] = _swap_open(str(ssp.get("full_script") or ""))
                                if ssp.get("narration"):
                                    ssp["narration"] = _swap_open(str(ssp.get("narration") or ""))
                                sp["structured_script"] = ssp
                            if isinstance(sp.get("best_variant"), dict):
                                bv = dict(sp["best_variant"])
                                bv["hook"] = required_hook
                                if bv.get("full_script"):
                                    bv["full_script"] = _swap_open(str(bv.get("full_script") or ""))
                                sp["best_variant"] = bv
                            top["script_package"] = sp
                        cands[0] = top
                        ctx["candidates"] = cands
                        ctx["hook"] = required_hook
                        ctx["hook_enforcement"] = {"applied": True, "hook": required_hook}

                # Full script override for mission briefs (soft) — factual narration package
                override = cons.get("script_override") or ctx.get("script_override")
                if isinstance(override, dict) and (
                    cons.get("golden_production") or cons.get("enforce_script") or ctx.get("golden_production")
                ):
                    cands = list(ctx.get("candidates") or [])
                    if cands and isinstance(cands[0], dict):
                        top = dict(cands[0])
                        narr = str(override.get("narration") or override.get("full_script") or "").strip()
                        hook_o = str(override.get("hook") or required_hook or "").strip()
                        if hook_o:
                            top["hook"] = hook_o
                            top["primary_hook"] = hook_o
                        if narr:
                            top["narration"] = narr
                            top["script"] = narr
                        if isinstance(override.get("scene_breakdown"), list):
                            top["scene_breakdown"] = list(override["scene_breakdown"])
                        if isinstance(override.get("sections"), list):
                            top["sections"] = list(override["sections"])
                        ss = dict(top.get("structured_script") or {})
                        ss.update({k: v for k, v in override.items() if v is not None})
                        if narr:
                            ss["narration"] = narr
                            ss["full_script"] = narr
                        if hook_o:
                            ss["hook"] = hook_o
                            ss["primary_hook"] = hook_o
                        top["structured_script"] = ss
                        sp = dict(top.get("script_package") or {})
                        if sp:
                            if narr:
                                sp["narration"] = narr
                            if hook_o:
                                sp["hook"] = hook_o
                            if isinstance(sp.get("best_variant"), dict):
                                bv = dict(sp["best_variant"])
                                if narr:
                                    bv["full_script"] = narr
                                if hook_o:
                                    bv["hook"] = hook_o
                                sp["best_variant"] = bv
                            top["script_package"] = sp
                        cands[0] = top
                        ctx["candidates"] = cands
                        ctx["script_override"] = {"applied": True, "chars": len(narr)}
            except Exception:  # noqa: BLE001
                ctx["hook_enforcement"] = {"error": "unavailable"}

        # Persistent World Builder — soft place after scenes (never blocks ops)
        if stage_key == "scene_builder":
            try:
                from services.world_builder import place_candidate_in_world

                cands = list(ctx.get("candidates") or [])
                if cands and isinstance(cands[0], dict):
                    cons = dict(brief_obj.constraints or {})
                    cands[0] = place_candidate_in_world(
                        cands[0],
                        topic=brief_obj.topic,
                        niche=str(cons.get("category") or cands[0].get("category") or ""),
                        world_type=str(cons.get("world_type") or ctx.get("world_type") or ""),
                        world_id=str(cons.get("world_id") or ctx.get("world_id") or ""),
                        production_id=pid,
                        platform=brief_obj.platform,
                        audience=str(cons.get("audience") or ctx.get("audience") or ""),
                        request={
                            "location_type": str(cons.get("world_type") or ""),
                            "required_objects": list(cons.get("world_objects") or []),
                            "continuity_requirements": list(cons.get("world_continuity") or []),
                        },
                    )
                    ctx["candidates"] = cands
                    ctx["world_package"] = cands[0].get("world_package")
                    ctx["world_id"] = cands[0].get("world_id")
            except Exception:  # noqa: BLE001
                ctx["world_placement"] = {"error": "unavailable"}

            # Visual Source Intelligence — choose strongest source before media fulfilment
            try:
                from services.visual_source_intelligence import (
                    attach_visual_source_package,
                    build_visual_source_package,
                )

                cands = list(ctx.get("candidates") or [])
                if cands and isinstance(cands[0], dict):
                    top = dict(cands[0])
                    vsi = build_visual_source_package(
                        top,
                        topic=brief_obj.topic,
                        production_id=pid,
                        write=True,
                    )
                    cands[0] = attach_visual_source_package(top, vsi)
                    ctx["candidates"] = cands
                    ctx["visual_source_intelligence"] = {
                        "path": vsi.get("path"),
                        "fallback_summary": vsi.get("fallback_summary"),
                        "publish_justified": (vsi.get("creative_review") or {}).get("publish_justified"),
                        "scene_count": vsi.get("scene_count"),
                    }
            except Exception:  # noqa: BLE001
                ctx["visual_source_intelligence"] = {"error": "unavailable"}

        # Visual Asset Director — soft gate after media, before cinematic/render (never blocks ops)
        if stage_key == "media_collection":
            try:
                from services.visual_asset_director import (
                    attach_visual_package_to_candidate,
                    build_visual_package,
                )

                cands = list(ctx.get("candidates") or [])
                if cands and isinstance(cands[0], dict):
                    top = dict(cands[0])
                    vad = build_visual_package(
                        top,
                        topic=brief_obj.topic,
                        niche=str(getattr(brief_obj, "category", "") or top.get("category") or ""),
                        platform=str(
                            getattr(brief_obj, "platform", None) or top.get("platform") or "youtube_shorts"
                        ),
                        world_package=top.get("world_package"),
                        production_id=pid,
                        write=True,
                    )
                    cands[0] = attach_visual_package_to_candidate(top, vad)
                    ctx["candidates"] = cands
                    ctx["visual_asset_direction"] = {
                        "path": vad.get("path"),
                        "approved_count": len(vad.get("approved_assets") or []),
                        "rejected_count": len(vad.get("rejected_assets") or []),
                        "mean_overall": (vad.get("visual_scores") or {}).get(
                            "mean_overall_professional_quality"
                        ),
                        "validation": vad.get("validation"),
                    }
            except Exception:  # noqa: BLE001
                ctx["visual_asset_direction"] = {"error": "unavailable"}

        # Virtual Film Director soft-ensure — before Animation package rebuild
        if stage_key == "animation":
            try:
                from services.virtual_film_director import direct_candidate as vfd_direct

                cands = list(ctx.get("candidates") or [])
                if cands and isinstance(cands[0], dict) and not cands[0].get("directed_by_vfd"):
                    cands[0] = vfd_direct(
                        cands[0],
                        topic=str(cands[0].get("topic") or ctx.get("topic") or ""),
                        production_id=str(ctx.get("production_id") or ""),
                        write=True,
                    )
                    ctx["candidates"] = cands
                if cands and isinstance(cands[0], dict):
                    ctx["virtual_film_director"] = cands[0].get("virtual_film_director") or {
                        "path": (cands[0].get("VIRTUAL_FILM_DIRECTOR_PACKAGE") or {}).get("path"),
                    }
            except Exception:  # noqa: BLE001
                ctx["virtual_film_director"] = {"error": "unavailable"}

        # Character & World Studio — after VFD, before Animation Engine package
        if stage_key == "animation":
            try:
                from services.character_world_studio import studio_place_candidate

                cands = list(ctx.get("candidates") or [])
                if cands and isinstance(cands[0], dict) and not cands[0].get("CHARACTER_WORLD_STUDIO_PACKAGE"):
                    cands[0] = studio_place_candidate(
                        cands[0],
                        topic=str(cands[0].get("topic") or ctx.get("topic") or brief_obj.topic),
                        production_id=str(ctx.get("production_id") or pid),
                        write=True,
                    )
                    ctx["candidates"] = cands
                if cands and isinstance(cands[0], dict):
                    ctx["character_world_studio"] = cands[0].get("character_world_studio") or {
                        "path": (cands[0].get("CHARACTER_WORLD_STUDIO_PACKAGE") or {}).get("path"),
                    }
            except Exception:  # noqa: BLE001
                ctx["character_world_studio"] = {"error": "unavailable"}

        # Cinematic Animation Engine V2 — ensure package after cinematography/animation stage
        if stage_key == "animation":
            try:
                from services.animation_engine import attach_animation_package, build_animation_package

                cands = list(ctx.get("candidates") or [])
                if cands and isinstance(cands[0], dict):
                    top = dict(cands[0])
                    existing = top.get("ANIMATION_PACKAGE")
                    if not isinstance(existing, dict) or not existing.get("scene_decisions"):
                        pkg = build_animation_package(
                            top,
                            topic=brief_obj.topic,
                            production_id=pid,
                            write=True,
                        )
                        top = attach_animation_package(top, pkg)
                        cands[0] = top
                        ctx["candidates"] = cands
                    else:
                        pkg = existing
                    ctx["animation_engine"] = {
                        "path": pkg.get("path") or (top.get("animation_engine") or {}).get("path"),
                        "animation_excellence_score": (pkg.get("animation_excellence") or {}).get(
                            "animation_excellence_score"
                        ),
                        "quality_gate": (pkg.get("quality_gate") or {}).get("decision"),
                        "scene_count": pkg.get("scene_count"),
                    }
            except Exception:  # noqa: BLE001
                ctx["animation_engine"] = {"error": "unavailable"}

        # Visual Source Intelligence creative review — before export (never rebuilds)
        if stage_key == "rendering":
            try:
                from services.visual_source_intelligence import creative_review

                cands = list(ctx.get("candidates") or [])
                top = cands[0] if cands and isinstance(cands[0], dict) else {}
                prior = top.get("VISUAL_SOURCE_INTELLIGENCE") or {}
                review = creative_review(top, package=prior if isinstance(prior, dict) else None)
                ctx["visual_source_creative_review"] = review
                if cands and isinstance(cands[0], dict):
                    vsi_meta = dict(cands[0].get("visual_source_intelligence") or {})
                    vsi_meta["creative_review"] = review
                    cands[0]["visual_source_intelligence"] = vsi_meta
                    ctx["candidates"] = cands
            except Exception:  # noqa: BLE001
                ctx["visual_source_creative_review"] = {"error": "unavailable"}

            # Animation quality gate snapshot (advisory — does not auto-rebuild)
            try:
                from services.animation_engine.score import quality_gate

                cands = list(ctx.get("candidates") or [])
                top = cands[0] if cands and isinstance(cands[0], dict) else {}
                pkg = top.get("ANIMATION_PACKAGE") if isinstance(top.get("ANIMATION_PACKAGE"), dict) else {}
                decisions = list(pkg.get("scene_decisions") or [])
                if decisions:
                    gate = quality_gate(decisions)
                    ctx["animation_quality_gate"] = gate
                    if cands and isinstance(cands[0], dict):
                        meta = dict(cands[0].get("animation_engine") or {})
                        meta["post_render_gate"] = gate
                        cands[0]["animation_engine"] = meta
                        ctx["candidates"] = cands
            except Exception:  # noqa: BLE001
                ctx["animation_quality_gate"] = {"error": "unavailable"}

        # NEVER break — continue even if degraded

    total_ms = int((time.time() - t0) * 1000)
    status["elapsed_ms"] = total_ms
    status["finished_at"] = _now()
    status["overall_progress_pct"] = 100
    # Roll-up validation
    qs = list(quality_scores.values())
    status["validation_score"] = round(sum(qs) / len(qs), 1) if qs else 0

    # Deliverable truth: production success requires a materialized MP4 unless soft-export opted in
    export_val = ctx.get("export_validation") if isinstance(ctx.get("export_validation"), dict) else {}
    video_exists = bool(export_val.get("video_exists"))
    allow_missing = bool(
        ctx.get("allow_missing_mp4")
        or (ctx.get("ops_constraints") or {}).get("allow_missing_mp4")
        or str((ctx.get("ops_constraints") or {}).get("export_mode") or "").lower()
        in ("smoke", "plan", "metadata", "dry_run")
    )
    status["video_exists"] = video_exists
    status["deliverable_ok"] = video_exists or allow_missing
    if status["deliverable_ok"]:
        status["overall_status"] = "succeeded"
        status["success"] = True
    else:
        status["overall_status"] = "degraded_no_export"
        status["success"] = False
        notes = list(status.get("notes") or [])
        notes.append("success_requires_mp4 — pipeline continued but deliverable missing")
        status["notes"] = notes

    report = build_production_report(ctx, status, brief)
    report_path = write_production_report(pid, report)
    # Creative Excellence — attention craft (separate from engineering QA)
    try:
        from services.creative_excellence import review_production_creative_excellence

        top = next((c for c in (ctx.get("candidates") or []) if isinstance(c, dict)), {})
        creative = review_production_creative_excellence(
            top or {"topic": brief_obj.topic, "platform": brief_obj.platform},
            production_report=report,
            production_id=pid,
            topic=brief_obj.topic,
        )
        ctx["creative_excellence"] = {
            "creative_excellence_score": (creative.get("scorecard") or {}).get("creative_excellence_score"),
            "single_recommendation": creative.get("single_recommendation"),
            "markdown_path": creative.get("markdown_path"),
        }
        report["creative_excellence_score"] = ctx["creative_excellence"]["creative_excellence_score"]
        report["creative_recommendation"] = (creative.get("single_recommendation") or {}).get("recommendation")
        write_production_report(pid, report)
    except Exception:  # noqa: BLE001 — never block ops on creative review
        ctx["creative_excellence"] = {"error": "unavailable"}

    # Audience Intelligence — post-production lesson (advisory only; never blocks ops)
    try:
        from services.audience_intelligence import review_production_audience

        top = next((c for c in (ctx.get("candidates") or []) if isinstance(c, dict)), {})
        ai_review = review_production_audience(
            topic=brief_obj.topic,
            niche=str(getattr(brief_obj, "category", "") or top.get("category") or ""),
            platform=str(getattr(brief_obj, "platform", None) or top.get("platform") or "youtube_shorts"),
            production_id=pid,
            candidate=top or {"topic": brief_obj.topic},
            production_report=report,
            creative_excellence=(
                None
                if (ctx.get("creative_excellence") or {}).get("error")
                else {
                    "scorecard": {
                        "creative_excellence_score": (ctx.get("creative_excellence") or {}).get(
                            "creative_excellence_score"
                        )
                    },
                    "single_recommendation": (ctx.get("creative_excellence") or {}).get(
                        "single_recommendation"
                    ),
                    "creative_excellence_score": (ctx.get("creative_excellence") or {}).get(
                        "creative_excellence_score"
                    ),
                }
            ),
        )
        ctx["audience_intelligence_review"] = {
            "lesson_id": (ai_review.get("lesson_recorded") or {}).get("lesson_id"),
            "highest_impact_improvement": (ai_review.get("highest_impact_improvement") or {}).get(
                "statement"
            ),
            "markdown_path": ai_review.get("markdown_path"),
            "path": ai_review.get("path"),
        }
        report["audience_intelligence_lesson"] = (ai_review.get("lesson_recorded") or {}).get(
            "statement"
        )
        report["audience_intelligence_review_path"] = ai_review.get("path")
        write_production_report(pid, report)
    except Exception:  # noqa: BLE001 — never block ops on AI review
        ctx["audience_intelligence_review"] = {"error": "unavailable"}

    history_row = store_production(
        production_id=pid,
        brief=brief,
        report=report,
        status=status,
        context=ctx,
    )
    write_ops_status(pid, status)
    dash = build_live_dashboard(status)

    log_event(
        logger,
        "ops.production_finished",
        production_id=pid,
        elapsed_ms=total_ms,
        recommendation=report.get("final_recommendation"),
        overall=report.get("overall_quality_score"),
    )

    return {
        "production_id": pid,
        "succeeded": bool(status.get("success")),
        "success": bool(status.get("success")),
        "elapsed_ms": total_ms,
        "brief": brief,
        "status": status,
        "dashboard": dash,
        "report": report,
        "report_path": str(report_path),
        "history": history_row,
        "context": ctx,
        "recommendation": report.get("final_recommendation"),
        "export_validation": ctx.get("export_validation"),
        "video_exists": bool(status.get("video_exists")),
        "deliverable_ok": bool(status.get("deliverable_ok")),
    }
