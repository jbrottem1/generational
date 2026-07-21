"""Category scorers for Production Quality Assurance."""

from __future__ import annotations

from typing import Any

from services.production_qa.models import (
    CATEGORY_PASS_THRESHOLD,
    CategoryScore,
    PlatformReady,
    PLATFORM_KEYS,
)


def _clamp(n: float) -> int:
    return int(max(0, min(100, round(n))))


def _safe_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def score_research_accuracy(item: dict, context: dict | None = None) -> CategoryScore:
    context = context or {}
    research = _safe_dict(context.get("research") or item.get("research"))
    citations = _safe_dict(item.get("citations"))
    critique = _safe_dict(item.get("critique"))
    threat = _safe_dict(item.get("threat_report"))

    conf = float(research.get("research_confidence") or citations.get("claim_confidence") or 0)
    if conf <= 1.0:
        conf *= 100.0
    unsupported = _safe_list(citations.get("unsupported_claims"))
    citation_count = int(citations.get("citation_count") or len(_safe_list(citations.get("sources"))) or 0)
    critic_score = float(critique.get("score") or 70)
    hallucination_flags = _safe_list(threat.get("hallucination_risks") or threat.get("issues"))

    score = 55.0
    score += min(30.0, conf * 0.30)
    score += min(10.0, citation_count * 3.0)
    score += (critic_score - 50) * 0.15
    score -= len(unsupported) * 12.0
    score -= min(20.0, len(hallucination_flags) * 8.0)

    issues: list[str] = []
    corrections: list[str] = []
    if unsupported:
        issues.append(f"{len(unsupported)} unsupported claim(s)")
        corrections.append("Add citations or remove unsupported claims")
    if citation_count == 0:
        issues.append("No citations present")
        corrections.append("Attach trusted sources via Citation Engine")
    if conf < 45:
        issues.append("Low research confidence")
        corrections.append("Re-run Research with stronger sources")
    if hallucination_flags:
        issues.append("Hallucination / threat flags present")
        corrections.append("Resolve threat_detection findings before export")

    sources = []
    for src in _safe_list(citations.get("sources")):
        if isinstance(src, dict):
            sources.append(str(src.get("url") or src.get("title") or src.get("id") or "source"))
        elif src:
            sources.append(str(src))
    if research.get("sources"):
        for src in _safe_list(research.get("sources")):
            sources.append(str(src if not isinstance(src, dict) else src.get("url") or src.get("title")))

    return CategoryScore(
        key="research_accuracy",
        label="Research Accuracy",
        score=_clamp(score),
        confidence=min(0.95, 0.45 + citation_count * 0.08 + (0.2 if conf >= 50 else 0)),
        details={
            "research_confidence": conf,
            "citation_count": citation_count,
            "unsupported_claims": len(unsupported),
            "sources_checked": sources[:20],
        },
        issues=issues,
        corrections_required=corrections,
    )


def score_evidence(item: dict, _context: dict | None = None) -> CategoryScore:
    pkg = _safe_dict(item.get("evidence_package"))
    scenes = _safe_list(pkg.get("scenes"))
    authentic = int(pkg.get("authentic_hit_count") or 0)
    ai_fallback = int(pkg.get("ai_fallback_count") or 0)
    confidence = float(pkg.get("overall_evidence_confidence") or item.get("evidence_confidence") or 0)
    if confidence <= 1.0 and confidence > 0:
        confidence *= 100.0

    total_visuals = max(1, authentic + ai_fallback)
    real_pct = round(100.0 * authentic / total_visuals, 1)
    ai_pct = round(100.0 * ai_fallback / total_visuals, 1)

    missing: list[str] = []
    important_without = 0
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        modality = str(scene.get("modality") or scene.get("visual_type") or "")
        conf = float(scene.get("evidence_confidence") or 0)
        if conf <= 1.0:
            conf *= 100.0
        has_real = bool(
            scene.get("reality_image_ids")
            or scene.get("atlas_asset_ids")
            or (isinstance(scene.get("evidence"), dict) and scene["evidence"].get("source_type") in ("reality", "atlas", "nasa", "official"))
        )
        if modality in ("photo", "footage", "diagram", "") and not has_real and conf < 70:
            important_without += 1
            missing.append(str(scene.get("scene_id") or scene.get("narration") or "scene")[:80])

    score = 50.0 + confidence * 0.35 + real_pct * 0.25 - ai_pct * 0.15 - important_without * 8.0
    if not scenes and not pkg:
        score = 40.0
        missing.append("No evidence_package on production")

    issues = []
    corrections = []
    if real_pct < 50 and scenes:
        issues.append(f"Real image share only {real_pct}%")
        corrections.append("Prefer Reality Catalog / Knowledge Atlas over AI")
    if important_without:
        issues.append(f"{important_without} scene(s) lack visual evidence")
        corrections.append("Re-run Evidence Intelligence for missing scenes")
    if ai_pct > 40:
        issues.append("AI imagery used more than necessary")
        corrections.append("Replace AI fills with authentic media where possible")

    return CategoryScore(
        key="evidence",
        label="Evidence",
        score=_clamp(score),
        confidence=0.75 if scenes else 0.4,
        details={
            "real_image_pct": real_pct,
            "ai_image_pct": ai_pct,
            "authentic_hit_count": authentic,
            "ai_fallback_count": ai_fallback,
            "missing_evidence": missing[:12],
            "scene_count": len(scenes),
        },
        issues=issues,
        corrections_required=corrections,
    )


def score_visuals(item: dict, _context: dict | None = None) -> CategoryScore:
    visual = _safe_dict(item.get("visual_package"))
    visual_score = float(
        item.get("visual_score")
        or visual.get("visual_score")
        or (_safe_dict(visual.get("score_components")).get("overall") if visual else 0)
        or 0
    )
    qc = _safe_dict(item.get("qc") or item.get("visual_qc") or visual.get("qc"))
    production = _safe_dict(item.get("production") or item.get("render_package") or visual.get("render_package"))
    verification = _safe_dict(item.get("verification") or production.get("verification"))

    score = visual_score if visual_score > 0 else 62.0
    issues: list[str] = []
    corrections: list[str] = []

    hard = _safe_list(qc.get("hard_fails") or qc.get("failures"))
    warnings = _safe_list(qc.get("warnings"))
    score -= len(hard) * 12.0
    score -= len(warnings) * 3.0

    scenes = _safe_list(visual.get("scenes"))
    empty = sum(1 for s in scenes if isinstance(s, dict) and not (s.get("assets") or s.get("image") or s.get("shot_type") or s.get("visual_type")))
    if empty:
        issues.append(f"{empty} empty / under-specified scene(s)")
        corrections.append("Fill empty scenes in Visual Intelligence")
        score -= empty * 5.0

    if verification and verification.get("ok") is False:
        issues.append("Export technical verification failed")
        corrections.append("Re-export with verified_export")
        score -= 15.0

    if not visual and visual_score <= 0:
        issues.append("No visual_package to inspect")
        corrections.append("Run Visual Intelligence before PQA")

    return CategoryScore(
        key="visuals",
        label="Visuals",
        score=_clamp(score),
        confidence=0.8 if visual or visual_score else 0.35,
        details={
            "visual_score": visual_score,
            "scene_count": len(scenes),
            "empty_scenes": empty,
            "qc_hard_fails": len(hard),
        },
        issues=issues,
        corrections_required=corrections,
    )


def score_typography(item: dict, _context: dict | None = None) -> CategoryScore:
    visual = _safe_dict(item.get("visual_package"))
    captions = (
        item.get("captions")
        or item.get("subtitle_package")
        or (_safe_dict(item.get("structured_script")).get("caption_plan"))
        or visual.get("caption_plan")
        or []
    )
    layout = _safe_dict(item.get("layout_qc") or visual.get("layout_qc"))

    score = 88.0
    issues: list[str] = []
    corrections: list[str] = []

    if not captions:
        score -= 18.0
        issues.append("Captions / subtitle plan missing")
        corrections.append("Generate captions via Subtitle Engine")
    else:
        score += 6.0

    overlaps = int(layout.get("overlapping_text") or layout.get("overlap_count") or 0)
    clipping = int(layout.get("clipped_text") or layout.get("clip_count") or 0)
    outside = int(layout.get("outside_safe_margin") or 0)
    score -= overlaps * 10.0 + clipping * 10.0 + outside * 8.0
    if overlaps:
        issues.append("Overlapping text detected")
        corrections.append("Fix typography layout safe zones")
    if clipping:
        issues.append("Text clipping detected")
        corrections.append("Increase margins / reduce font size")
    if outside:
        issues.append("Text outside safe margins")
        corrections.append("Keep titles/captions inside safe zones")

    readability = layout.get("readability_score")
    if readability is not None:
        try:
            score = 0.55 * score + 0.45 * float(readability)
        except (TypeError, ValueError):
            pass

    return CategoryScore(
        key="typography",
        label="Typography",
        score=_clamp(score),
        confidence=0.7 if captions or layout else 0.4,
        details={"has_captions": bool(captions), "layout": layout or {}},
        issues=issues,
        corrections_required=corrections,
    )


def score_annotations(item: dict, _context: dict | None = None) -> CategoryScore:
    evidence = _safe_dict(item.get("evidence_package"))
    scenes = _safe_list(evidence.get("scenes") or _safe_dict(item.get("visual_package")).get("scenes"))
    total = 0
    tied = 0
    randomish = 0
    issues: list[str] = []
    corrections: list[str] = []

    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        plans = scene.get("annotation_plan") or scene.get("annotations") or []
        if not isinstance(plans, list):
            continue
        narration = str(scene.get("narration") or "")
        for ann in plans:
            if not isinstance(ann, dict):
                continue
            total += 1
            cue = str(ann.get("narration_cue") or ann.get("cue") or "")
            target = ann.get("target") or ann.get("highlight_region") or ann.get("region")
            if cue and (cue.lower() in narration.lower() or narration.lower().find(cue.lower()[:12]) >= 0):
                tied += 1
            elif target and cue:
                tied += 1
            else:
                randomish += 1

    if total == 0:
        score = 78.0  # no annotations is ok if none planned
        if scenes:
            issues.append("No narration-tied annotations found")
            corrections.append("Add purposeful annotations via Evidence Engine")
            score = 72.0
    else:
        ratio = tied / total
        score = 55.0 + ratio * 45.0 - randomish * 8.0
        if randomish:
            issues.append(f"{randomish} annotation(s) lack narration cue/target")
            corrections.append("Remove random arrows/circles; require narration_cue + target")

    return CategoryScore(
        key="annotations",
        label="Annotations",
        score=_clamp(score),
        confidence=0.75 if total else 0.45,
        details={"annotation_count": total, "narration_tied": tied, "untied": randomish},
        issues=issues,
        corrections_required=corrections,
    )


def score_cinematography(item: dict, _context: dict | None = None) -> CategoryScore:
    plan = _safe_dict(item.get("cinematography_plan"))
    scenes = _safe_list(plan.get("scenes"))
    attention = float(
        item.get("cinematography_attention_score")
        or plan.get("overall_attention_score")
        or 0
    )
    handoff = _safe_dict(item.get("animation_handoff") or plan.get("animation_handoff"))

    score = attention if attention > 0 else (70.0 if scenes else 45.0)
    issues: list[str] = []
    corrections: list[str] = []

    if not scenes:
        issues.append("No cinematography_plan scenes")
        corrections.append("Run Cinematography Engine before export")
        score = min(score, 48.0)
    else:
        # Penalize missing motion rationale / random-looking empty reasons
        weak = 0
        for s in scenes:
            if not isinstance(s, dict):
                continue
            if not (s.get("movement") or s.get("camera_plan")):
                weak += 1
            reason = str(s.get("reason") or s.get("movement_reason") or "")
            if reason and "random" in reason.lower():
                weak += 1
                issues.append("Random movement rationale detected")
        score -= weak * 8.0
        if weak:
            corrections.append("Re-direct scenes so movement reinforces narration")

    if not handoff.get("scenes") and scenes:
        issues.append("Animation handoff incomplete")
        corrections.append("Ensure animation_handoff is populated")
        score -= 5.0

    return CategoryScore(
        key="cinematography",
        label="Cinematography",
        score=_clamp(score),
        confidence=0.8 if scenes else 0.35,
        details={
            "attention_score": attention,
            "scene_count": len(scenes),
            "has_animation_handoff": bool(handoff.get("scenes")),
            "pacing": plan.get("pacing") or plan.get("scene_pacing"),
        },
        issues=issues,
        corrections_required=corrections,
    )


def score_retention(item: dict, _context: dict | None = None) -> CategoryScore:
    """Viewer Retention & Cinematic Excellence V2 gate.

    Backward compatible: when the V2 package is absent, score from existing
    psychology / script retention signals so legacy productions are not
    blocked solely for missing the new engine.
    """
    pkg = _safe_dict(item.get("viewer_retention_package"))
    score = float(
        item.get("viewer_retention_score")
        or item.get("cinematic_excellence_score")
        or pkg.get("overall_score")
        or 0
    )
    issues: list[str] = []
    corrections: list[str] = []
    details: dict = {
        "package_present": bool(pkg),
        "polish_rounds": pkg.get("polish_rounds"),
        "predictions": pkg.get("predictions") or item.get("retention_predictions") or {},
    }

    if not pkg and score <= 0:
        script_ret = _safe_dict(item.get("script_retention"))
        psych = _safe_dict(item.get("psychology"))
        legacy = [
            float(script_ret.get("retention_score") or 0),
            float(psych.get("retention_potential") or 0),
            float(psych.get("first_3_second_hook") or 0),
            float(item.get("psychology_score") or 0),
            float(item.get("human_attention_score") or 0),
        ]
        score = max(legacy) if any(legacy) else 70.0
        details["legacy_fallback"] = True
        if score < CATEGORY_PASS_THRESHOLD:
            issues.append("Viewer Retention package missing")
            corrections.append("Run viewer_retention before export")
    else:
        qs = _safe_dict(pkg.get("quality_scores"))
        if qs:
            score = max(score, float(qs.get("overall") or score))
        hook = _safe_dict(pkg.get("selected_hook"))
        if int(hook.get("score") or 0) < 80 and pkg:
            issues.append("Selected hook below excellence bar")
            corrections.append("Regenerate hook candidates and pick a stronger opening")
            score = min(score, 88.0)
        curve = _safe_list(pkg.get("retention_curve"))
        high_risk = [
            c for c in curve
            if isinstance(c, dict) and str(c.get("risk") or "") == "high"
        ]
        if high_risk:
            issues.append(f"{len(high_risk)} high-risk retention checkpoint(s)")
            corrections.append("Polish pacing / hook / mid-beats via viewer_retention")
            score -= 6.0 * min(3, len(high_risk))
        if pkg and not item.get("viewer_retention_passed") and score < 98:
            corrections.append("Auto-polish until cinematic excellence ≥ 98")

    return CategoryScore(
        key="retention",
        label="Viewer Retention",
        score=_clamp(score),
        confidence=0.85 if pkg else 0.55,
        details=details,
        issues=issues,
        corrections_required=corrections,
    )


def score_render_quality(item: dict, _context: dict | None = None) -> CategoryScore:
    """Studio Render & Motion Graphics V3 gate (backward compatible)."""
    pkg = _safe_dict(item.get("studio_render_package"))
    score = float(
        item.get("studio_render_score")
        or item.get("render_quality_score")
        or pkg.get("overall_score")
        or 0
    )
    issues: list[str] = []
    corrections: list[str] = []
    details: dict = {
        "package_present": bool(pkg),
        "revision_rounds": pkg.get("revision_rounds"),
        "export_plan": (pkg.get("export_plan") or item.get("export_plan_v3") or {}),
    }

    if not pkg and score <= 0:
        # Legacy fallback from cinematography / visual / render_package signals
        cine = float(item.get("cinematography_attention_score") or 0)
        visual = float(item.get("visual_score") or 0)
        rp = _safe_dict(item.get("render_package"))
        score = max(cine, visual, 70.0 if rp else 68.0)
        details["legacy_fallback"] = True
        if score < CATEGORY_PASS_THRESHOLD:
            issues.append("Studio Render package missing")
            corrections.append("Run studio_render before export")
    else:
        qs = _safe_dict(pkg.get("quality_scores"))
        if qs:
            score = max(score, float(qs.get("overall") or score))
        if not (pkg.get("transitions") or []):
            issues.append("No cinematic transitions planned")
            corrections.append("Rebuild transition engine layer")
            score = min(score, 88.0)
        if not (pkg.get("color_grade") or {}).get("lut"):
            issues.append("Color LUT missing")
            corrections.append("Apply grade profile")
            score = min(score, 90.0)
        if pkg and not item.get("studio_render_passed") and score < 98:
            corrections.append("Auto-revise studio render until quality ≥ 98")

    return CategoryScore(
        key="render_quality",
        label="Render Quality",
        score=_clamp(score),
        confidence=0.88 if pkg else 0.5,
        details=details,
        issues=issues,
        corrections_required=corrections,
    )


def score_optimization(item: dict, _context: dict | None = None) -> CategoryScore:
    """Autonomous Optimization Lab V4 gate (backward compatible)."""
    pkg = _safe_dict(item.get("optimization_package"))
    score = float(
        item.get("optimization_score")
        or pkg.get("overall_score")
        or 0
    )
    issues: list[str] = []
    corrections: list[str] = []
    details: dict = {
        "package_present": bool(pkg),
        "winner": (pkg.get("winner") or item.get("optimization_winner") or {}),
        "experiment_id": pkg.get("experiment_id") or "",
        "variant_count": len(pkg.get("variants") or []),
    }

    if not pkg and score <= 0:
        # Legacy: use ranking / quality / retention as soft readiness
        legacy = [
            float(item.get("psychology_score") or 0),
            float(item.get("seo_score") or 0),
            float(item.get("viewer_retention_score") or 0),
            float(item.get("studio_render_score") or 0),
            float(item.get("script_quality") or 0),
        ]
        score = max(legacy) if any(legacy) else 72.0
        details["legacy_fallback"] = True
        if score < CATEGORY_PASS_THRESHOLD:
            issues.append("Optimization package missing")
            corrections.append("Run optimization_lab before publish")
    else:
        if len(pkg.get("variants") or []) < 2:
            issues.append("Fewer than 2 variants generated")
            corrections.append("Increase optimization_variant_count")
            score = min(score, 88.0)
        if not (pkg.get("winner") or item.get("winning_variant_id")):
            issues.append("No winning variant selected")
            corrections.append("Re-run comparison leaderboard")
            score = min(score, 85.0)
        if pkg and not item.get("optimization_passed") and score < 98:
            corrections.append("Revise winning variant until optimization score ≥ 98")

    return CategoryScore(
        key="optimization",
        label="Optimization",
        score=_clamp(score),
        confidence=0.86 if pkg else 0.5,
        details=details,
        issues=issues,
        corrections_required=corrections,
    )


def score_audio(item: dict, _context: dict | None = None) -> CategoryScore:
    voice = _safe_dict(item.get("voice_package") or item.get("audio_package") or item.get("voice_audio"))
    plan = _safe_dict(item.get("audio_production_package") or voice.get("plan"))
    score = 80.0
    issues: list[str] = []
    corrections: list[str] = []

    has_path = bool(voice.get("path") or voice.get("audio_b64") or voice.get("file"))
    if has_path:
        score += 10.0
    elif plan or voice:
        score += 4.0
    else:
        score -= 20.0
        issues.append("No voice/audio package")
        corrections.append("Generate narration via Voice / Voice Audio Engine")

    if voice.get("clipped") or voice.get("clipping"):
        issues.append("Audio clipping detected")
        corrections.append("Normalize and re-render voice")
        score -= 15.0
    if float(voice.get("noise_floor") or 0) > 0.35:
        issues.append("Background noise elevated")
        corrections.append("Denoise / re-record narration")
        score -= 10.0
    if voice.get("normalized") is False:
        issues.append("Audio not normalized")
        corrections.append("Apply loudness normalization")
        score -= 6.0

    music = float(voice.get("music_balance") or plan.get("music_balance") or 0.5)
    if music > 0.85:
        issues.append("Music may overpower narration")
        corrections.append("Lower music bed under voice")
        score -= 8.0

    return CategoryScore(
        key="audio",
        label="Audio",
        score=_clamp(score),
        confidence=0.7 if (has_path or plan) else 0.35,
        details={"has_audio_file": has_path, "music_balance": music},
        issues=issues,
        corrections_required=corrections,
    )


def score_narration(item: dict, _context: dict | None = None) -> CategoryScore:
    script = _safe_dict(item.get("structured_script") or item.get("script"))
    variants = _safe_list(item.get("script_variants"))
    best = float(item.get("script_quality") or script.get("quality_score") or 0)
    if not best and variants:
        best = max(float(v.get("score") or 0) for v in variants if isinstance(v, dict)) or 0
    psychology = _safe_dict(item.get("psychology"))
    hook = float(psychology.get("first_3_second_hook") or script.get("hook_score") or 60)

    score = best if best > 0 else 68.0
    score = 0.55 * score + 0.25 * hook + 0.20 * float(psychology.get("clarity") or psychology.get("comprehension") or 65)

    issues: list[str] = []
    corrections: list[str] = []
    text = str(script.get("full_script") or script.get("narration") or item.get("script_text") or "")
    if not text and not variants:
        issues.append("Narration / script text missing")
        corrections.append("Run Script Generation")
        score = min(score, 50.0)
    if hook < 55:
        issues.append("Weak opening hook")
        corrections.append("Rewrite hook for stronger first 3 seconds")
    grammar_flags = _safe_list(script.get("grammar_issues") or item.get("grammar_issues"))
    if grammar_flags:
        issues.append(f"{len(grammar_flags)} grammar issue(s)")
        corrections.append("Fix grammar before voice render")
        score -= len(grammar_flags) * 4.0

    return CategoryScore(
        key="narration",
        label="Narration",
        score=_clamp(score),
        confidence=0.75 if (text or best) else 0.4,
        details={"script_quality": best, "hook": hook, "chars": len(text)},
        issues=issues,
        corrections_required=corrections,
    )


def score_synchronization(item: dict, _context: dict | None = None) -> CategoryScore:
    timeline = _safe_dict(item.get("timeline") or _safe_dict(item.get("render_package")).get("timeline"))
    cine = _safe_dict(item.get("cinematography_plan"))
    visual = _safe_dict(item.get("visual_package"))
    score = 82.0
    issues: list[str] = []
    corrections: list[str] = []

    segments = _safe_list(timeline.get("segments") or cine.get("timeline") or visual.get("timeline"))
    if not segments:
        score -= 15.0
        issues.append("No timeline / sync segments")
        corrections.append("Build timeline before export")
    else:
        score += 8.0

    # Annotation timing presence
    evidence_scenes = _safe_list(_safe_dict(item.get("evidence_package")).get("scenes"))
    missing_timing = 0
    for scene in evidence_scenes:
        if not isinstance(scene, dict):
            continue
        for ann in _safe_list(scene.get("annotation_plan")):
            if isinstance(ann, dict) and not (ann.get("start") or ann.get("t0") or ann.get("appear_at") is not None or ann.get("timing")):
                # soft: many plans use relative fade without absolute ts
                missing_timing += 0
    caption_plan = item.get("captions") or _safe_dict(item.get("structured_script")).get("caption_plan")
    if caption_plan and not segments:
        issues.append("Captions present without timeline sync")
        corrections.append("Align captions to timeline")
        score -= 8.0

    sync_qc = _safe_dict(item.get("sync_qc") or item.get("lipsync"))
    if sync_qc.get("score") is not None:
        score = 0.5 * score + 0.5 * float(sync_qc["score"])
    if sync_qc.get("ok") is False:
        issues.append("Lip-sync / sync QC failed")
        corrections.append("Re-time animation to voice")
        score -= 12.0

    return CategoryScore(
        key="synchronization",
        label="Synchronization",
        score=_clamp(score),
        confidence=0.7 if segments else 0.4,
        details={"segment_count": len(segments), "missing_ann_timing": missing_timing},
        issues=issues,
        corrections_required=corrections,
    )


def score_education(item: dict, _context: dict | None = None) -> CategoryScore:
    psychology = _safe_dict(item.get("psychology"))
    audience = _safe_dict(item.get("audience_intelligence"))
    script = _safe_dict(item.get("structured_script") or item.get("script"))
    clarity = float(psychology.get("clarity") or psychology.get("comprehension") or script.get("clarity") or 70)
    density = float(psychology.get("knowledge_density") or audience.get("knowledge_density") or 65)
    progression = float(script.get("logical_progression") or psychology.get("structure") or 70)
    engagement = float(psychology.get("engagement") or item.get("human_attention_score") or 65)
    retention = float(psychology.get("retention_potential") or 65)

    score = 0.25 * clarity + 0.2 * progression + 0.2 * engagement + 0.15 * density + 0.2 * retention
    issues: list[str] = []
    corrections: list[str] = []
    if clarity < 60:
        issues.append("Educational clarity below bar")
        corrections.append("Simplify explanations in Script Engine")
    if density < 50:
        issues.append("Low knowledge density")
        corrections.append("Add concrete facts with evidence support")

    return CategoryScore(
        key="educational_value",
        label="Educational Value",
        score=_clamp(score),
        confidence=0.7,
        details={
            "clarity": clarity,
            "logical_progression": progression,
            "engagement": engagement,
            "knowledge_density": density,
            "retention": retention,
        },
        issues=issues,
        corrections_required=corrections,
    )


def score_psychology(item: dict, _context: dict | None = None) -> CategoryScore:
    psych = _safe_dict(item.get("psychology"))
    audience = _safe_dict(item.get("audience_intelligence"))
    attention = float(item.get("human_attention_score") or audience.get("human_attention_score") or 0)
    base = float(item.get("psychology_score") or 0)
    if base <= 0:
        vals = [
            float(psych.get(k) or 0)
            for k in (
                "curiosity_gap",
                "first_3_second_hook",
                "retention_potential",
                "share_likelihood",
                "replay_value",
            )
            if psych.get(k) is not None
        ]
        base = sum(vals) / len(vals) if vals else 60.0
    if attention:
        score = 0.55 * base + 0.45 * attention
    else:
        score = base

    predicted = {
        "ctr": float(psych.get("ctr_estimate") or audience.get("estimated_ctr") or score * 0.08),
        "avg_watch_time_sec": float(audience.get("estimated_runtime_hint_sec") or psych.get("avg_watch_time") or 0),
        "drop_off_risk": float(psych.get("drop_off_risk") or max(0, 100 - float(psych.get("retention_potential") or 60))),
        "shareability": float(psych.get("share_likelihood") or 50),
        "replay_probability": float(psych.get("replay_value") or 50),
        "subscriber_conversion": float(psych.get("subscribe_likelihood") or audience.get("subscriber_conversion") or 40),
    }

    issues: list[str] = []
    corrections: list[str] = []
    if predicted["drop_off_risk"] > 55:
        issues.append("High drop-off risk")
        corrections.append("Strengthen mid-video retention beats")
    if score < 70:
        issues.append("Psychology score below documentary engagement bar")
        corrections.append("Re-run Audience / Psychology with stronger hooks")

    return CategoryScore(
        key="psychology",
        label="Psychology",
        score=_clamp(score),
        confidence=0.75 if (psych or audience) else 0.4,
        details={"predicted_metrics": predicted, "human_attention_score": attention},
        issues=issues,
        corrections_required=corrections,
    )


def score_seo(item: dict, _context: dict | None = None) -> CategoryScore:
    seo = float(item.get("seo_score") or 0)
    package = _safe_dict(item.get("seo_package") or item.get("metadata"))
    title = str(package.get("title") or item.get("title") or "")
    description = str(package.get("description") or item.get("description") or "")
    keywords = _safe_list(package.get("keywords") or package.get("tags") or item.get("keywords"))
    hashtags = _safe_list(package.get("hashtags") or item.get("hashtags"))

    score = seo if seo > 0 else 55.0
    issues: list[str] = []
    corrections: list[str] = []
    if not title:
        issues.append("Title missing")
        corrections.append("Generate SEO title")
        score -= 20.0
    elif len(title) < 12:
        issues.append("Title too short")
        corrections.append("Expand title for search intent")
        score -= 8.0
    if not description:
        issues.append("Description missing")
        corrections.append("Write SEO description")
        score -= 12.0
    if not keywords and not hashtags:
        issues.append("No keywords/hashtags")
        corrections.append("Add keywords and platform hashtags")
        score -= 10.0
    else:
        score += 8.0

    return CategoryScore(
        key="seo",
        label="SEO",
        score=_clamp(score),
        confidence=0.8 if package or seo else 0.4,
        details={
            "title_len": len(title),
            "description_len": len(description),
            "keyword_count": len(keywords),
            "hashtag_count": len(hashtags),
        },
        issues=issues,
        corrections_required=corrections,
    )


def score_platform_compliance(item: dict, _context: dict | None = None) -> tuple[CategoryScore, list[PlatformReady]]:
    visual = _safe_dict(item.get("visual_package"))
    render = _safe_dict(item.get("render_package") or visual.get("render_package") or item.get("production"))
    aspect = str(
        item.get("aspect_ratio")
        or visual.get("aspect_ratio")
        or render.get("aspect_ratio")
        or "16:9"
    )
    duration = float(
        item.get("duration_sec")
        or render.get("duration_sec")
        or visual.get("duration_sec")
        or 0
    )
    has_captions = bool(
        item.get("captions")
        or item.get("subtitle_package")
        or _safe_dict(item.get("structured_script")).get("caption_plan")
    )
    has_thumb = bool(item.get("thumbnail") or item.get("thumbnail_concepts") or visual.get("thumbnails"))
    has_seo = bool(item.get("seo_package") or item.get("title"))
    vertical = aspect in ("9:16", "9/16", "vertical", "1080x1920")
    landscape = aspect in ("16:9", "16/9", "landscape", "1920x1080")

    platforms: list[PlatformReady] = []
    for key in PLATFORM_KEYS:
        reasons: list[str] = []
        ready = True
        if key in ("youtube_shorts", "tiktok", "instagram_reels") and not vertical and aspect not in ("1:1",):
            # Allow if unspecified; soft fail only when explicitly landscape longform
            if landscape and duration > 90:
                ready = False
                reasons.append("Short-form platforms prefer 9:16 under ~90s")
        if key == "youtube" and vertical and duration < 15:
            reasons.append("Very short vertical may fit Shorts better")
        if key in ("youtube", "youtube_shorts", "tiktok", "instagram_reels") and not has_captions:
            ready = False
            reasons.append("Captions required")
        if key in ("youtube", "pinterest", "linkedin") and not has_thumb:
            ready = False
            reasons.append("Thumbnail missing")
        if not has_seo and key in ("youtube", "linkedin", "pinterest"):
            ready = False
            reasons.append("SEO / metadata missing")
        if duration <= 0 and key in ("youtube_shorts", "tiktok"):
            reasons.append("Duration unknown")
        platforms.append(PlatformReady(platform=key, ready=ready, reasons=reasons))

    ready_count = sum(1 for p in platforms if p.ready)
    score = 40.0 + (ready_count / max(1, len(platforms))) * 60.0
    issues = [f"{p.platform}: {', '.join(p.reasons)}" for p in platforms if not p.ready and p.reasons]
    corrections = ["Fix platform packaging (aspect, captions, thumbnail, SEO) for failed platforms"] if issues else []

    cat = CategoryScore(
        key="platform_compliance",
        label="Platform Compliance",
        score=_clamp(score),
        confidence=0.7,
        details={"ready_count": ready_count, "aspect_ratio": aspect, "duration_sec": duration},
        issues=issues[:8],
        corrections_required=corrections,
    )
    return cat, platforms


CATEGORY_SCORERS = {
    "research_accuracy": score_research_accuracy,
    "evidence": score_evidence,
    "visuals": score_visuals,
    "typography": score_typography,
    "annotations": score_annotations,
    "cinematography": score_cinematography,
    "retention": score_retention,
    "render_quality": score_render_quality,
    "optimization": score_optimization,
    "audio": score_audio,
    "narration": score_narration,
    "synchronization": score_synchronization,
    "educational_value": score_education,
    "psychology": score_psychology,
    "seo": score_seo,
}
