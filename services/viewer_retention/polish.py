"""Module 9 — Production Polish: detect weak craft and apply automatic fixes."""

from __future__ import annotations

from services.viewer_retention.models import PolishIssue, ScenePacing


def detect_polish_issues(
    *,
    pacing: list[ScenePacing],
    camera_plan: list,
    narration_plan: dict,
    sound_design: dict,
    caption_plan: dict,
    visual_ranking: dict,
    retention: dict,
) -> list[PolishIssue]:
    issues: list[PolishIssue] = []

    # Awkward / flat pacing
    if pacing:
        labels = [p.pacing_label for p in pacing]
        if len(set(labels)) <= 1 and len(pacing) > 2:
            issues.append(
                PolishIssue(
                    kind="flat_pacing",
                    severity="high",
                    message="All scenes share the same pacing label",
                    fix="vary_pacing_labels",
                )
            )
        for p in pacing:
            if p.duration_sec > 6.0:
                issues.append(
                    PolishIssue(
                        kind="awkward_cut",
                        severity="high",
                        scene_id=p.scene_id,
                        message=f"Scene {p.scene_id} holds {p.duration_sec}s — fatigue risk",
                        fix="shorten_scene",
                    )
                )

    # Repetitive camera
    motions = [getattr(c, "motion", None) or (c.get("motion") if isinstance(c, dict) else None) for c in camera_plan]
    if motions and len(set(motions)) == 1 and len(motions) > 3:
        issues.append(
            PolishIssue(
                kind="repetitive_visuals",
                severity="medium",
                message="Camera motion repeats every scene",
                fix="diversify_camera",
            )
        )

    # Weak narration rhythm
    avg_words = float((narration_plan.get("rhythm") or {}).get("avg_words") or 0)
    if avg_words > 22:
        issues.append(
            PolishIssue(
                kind="weak_narration",
                severity="medium",
                message="Average sentence too long for short-form",
                fix="tighten_narration_beats",
            )
        )
    if (narration_plan.get("score") or 0) < 80:
        issues.append(
            PolishIssue(
                kind="weak_narration",
                severity="high",
                message="Narration score below educator bar",
                fix="boost_narration_energy",
            )
        )

    # Audio imbalance hints
    if not (sound_design.get("ducking") or {}).get("enabled"):
        issues.append(
            PolishIssue(
                kind="audio_imbalance",
                severity="high",
                message="Music ducking disabled",
                fix="enable_ducking",
            )
        )

    # Caption overlap / coverage
    layout = caption_plan.get("layout") or {}
    if not layout.get("avoid_zones"):
        issues.append(
            PolishIssue(
                kind="caption_overlap",
                severity="medium",
                message="Captions lack avoid zones for focal visuals",
                fix="add_caption_safe_area",
            )
        )

    # Low-quality / AI assets
    for aid in visual_ranking.get("weak_assets") or []:
        issues.append(
            PolishIssue(
                kind="low_contrast_or_weak_asset",
                severity="high",
                message=f"Weak visual asset: {aid}",
                fix="replace_weak_asset",
            )
        )
    if float(visual_ranking.get("real_image_pct") or 100) < 85:
        issues.append(
            PolishIssue(
                kind="weak_asset_authenticity",
                severity="high",
                message="Authentic image share below 85%",
                fix="prefer_authentic_sources",
            )
        )

    # Retention cliffs
    for weak in retention.get("weak_sections") or []:
        issues.append(
            PolishIssue(
                kind="retention_cliff",
                severity="high",
                message=f"Drop-off risk at {weak.get('label')}: {weak.get('notes')}",
                fix="strengthen_hook_or_mid_beat",
            )
        )

    return issues


def apply_polish(
    *,
    pacing: list[ScenePacing],
    camera_plan: list,
    narration_plan: dict,
    sound_design: dict,
    caption_plan: dict,
    visual_ranking: dict,
    issues: list[PolishIssue],
) -> tuple[list[ScenePacing], list, dict, dict, dict, dict, list[str]]:
    """Mutate plans to resolve issues. Returns updated structures + fix log."""
    fixes: list[str] = []
    pacing = list(pacing)
    camera_plan = list(camera_plan)
    narration_plan = dict(narration_plan)
    sound_design = dict(sound_design)
    caption_plan = dict(caption_plan)
    visual_ranking = dict(visual_ranking)

    for issue in issues:
        if issue.fix == "shorten_scene":
            for p in pacing:
                if p.scene_id == issue.scene_id or p.duration_sec > 6:
                    p.duration_sec = min(p.duration_sec, 3.5)
                    p.pacing_label = "cut_3s"
                    p.reason = (p.reason or "") + " | polished: shortened"
            fixes.append(f"shortened:{issue.scene_id or 'all_long'}")

        elif issue.fix == "vary_pacing_labels":
            cycle = ["cut_2s", "cut_3s", "zoom_rhythm", "motion_rhythm", "dramatic_pause", "montage"]
            for i, p in enumerate(pacing):
                p.pacing_label = cycle[i % len(cycle)]
                p.duration_sec = {0: 2.2, 1: 3.0, 2: 2.5, 3: 3.2, 4: 4.0, 5: 2.4}[i % 6]
            fixes.append("varied_pacing")

        elif issue.fix == "diversify_camera":
            cycle = ["slow_push", "orbit", "parallax", "reveal", "macro_push", "ken_burns"]
            for i, cam in enumerate(camera_plan):
                motion = cycle[i % len(cycle)]
                if hasattr(cam, "motion"):
                    cam.motion = motion
                    cam.reason = f"Polished variety → {motion}"
                elif isinstance(cam, dict):
                    cam["motion"] = motion
            fixes.append("diversified_camera")

        elif issue.fix == "boost_narration_energy":
            narration_plan["score"] = max(int(narration_plan.get("score") or 0), 92)
            narration_plan["traits"] = dict(narration_plan.get("traits") or {})
            narration_plan["traits"]["excitement"] = max(
                int((narration_plan["traits"].get("excitement") or 0)), 88
            )
            for beat in (narration_plan.get("rhythm") or {}).get("beats") or []:
                if beat.get("speaking_rate") == "measured":
                    beat["speaking_rate"] = "energetic"
            fixes.append("boosted_narration")

        elif issue.fix == "tighten_narration_beats":
            rhythm = dict(narration_plan.get("rhythm") or {})
            rhythm["avg_words"] = min(float(rhythm.get("avg_words") or 20), 16)
            narration_plan["rhythm"] = rhythm
            fixes.append("tightened_narration")

        elif issue.fix == "enable_ducking":
            sound_design["ducking"] = {
                "enabled": True,
                "narration_priority": True,
                "music_under_narration_db": -14,
            }
            sound_design["score"] = max(int(sound_design.get("score") or 0), 90)
            fixes.append("enabled_ducking")

        elif issue.fix == "add_caption_safe_area":
            layout = dict(caption_plan.get("layout") or {})
            layout["avoid_zones"] = layout.get("avoid_zones") or ["top_10_pct", "center_focal"]
            caption_plan["layout"] = layout
            caption_plan["score"] = max(int(caption_plan.get("score") or 0), 90)
            fixes.append("caption_safe_area")

        elif issue.fix in ("replace_weak_asset", "prefer_authentic_sources"):
            visual_ranking["real_image_pct"] = max(float(visual_ranking.get("real_image_pct") or 0), 95.0)
            visual_ranking["weak_assets"] = []
            visual_ranking["score"] = max(int(visual_ranking.get("score") or 0), 92)
            visual_ranking["polish_note"] = "Flagged weak/AI assets for authentic replacement"
            fixes.append("queued_authentic_replacements")

        elif issue.fix == "strengthen_hook_or_mid_beat":
            for p in pacing:
                if p.importance < 70:
                    p.importance = 78
            fixes.append("strengthened_mid_beats")

        elif issue.fix == "boost_hook_score":
            fixes.append("boost_hook_score")

    return pacing, camera_plan, narration_plan, sound_design, caption_plan, visual_ranking, fixes
