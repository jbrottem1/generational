"""Creative review before export — identify weak scenes; do not rebuild."""

from __future__ import annotations

from typing import Any


def _scenes_from(candidate: dict[str, Any], package: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if package and package.get("scene_decisions"):
        return list(package.get("scene_decisions") or [])
    vp = candidate.get("visual_package") if isinstance(candidate.get("visual_package"), dict) else {}
    scenes = list(vp.get("scenes") or candidate.get("scenes") or [])
    return [s for s in scenes if isinstance(s, dict)]


def creative_review(
    candidate: dict[str, Any] | None = None,
    *,
    package: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Answer mission questions honestly from VSI decisions + attached paths.
    Does not rebuild weak scenes.
    """
    candidate = candidate or {}
    decisions = list((package or {}).get("scene_decisions") or [])
    scenes = _scenes_from(candidate, package)
    n = max(len(decisions), len(scenes), 1)

    explain_yes = 0
    editor_keep = 0
    tiers: list[int] = []
    weak_idx = 0
    weak_score = 999.0
    for i, dec in enumerate(decisions or scenes):
        if isinstance(dec, dict) and "selected" in dec:
            sel = dec.get("selected") or {}
            tier = int(dec.get("tier") or 5)
            score = float(sel.get("selection_score") or dec.get("selection_score") or (100 - tier * 15))
            explains = float(sel.get("explains_narration") or 0.5)
            motion = float(sel.get("motion_score") or 0.3)
            path = sel.get("path") or (dec.get("scene") or {}).get("approved_asset_path")
        else:
            tier = int(tier_guess(dec))
            score = 100 - tier * 15
            explains = 0.55
            motion = 0.4 if str(dec.get("asset_type") or "") in {"ai_video", "stock_footage"} else 0.2
            path = dec.get("approved_asset_path") or dec.get("image")
        tiers.append(tier)
        if explains >= 0.45 and tier <= 4:
            explain_yes += 1
        # Human editor keep: motion + explain + not last-resort static without path diversity
        if tier <= 3 or (tier == 4 and motion >= 0.55) or (path and tier <= 4):
            if explains >= 0.4:
                editor_keep += 1
        if score < weak_score:
            weak_score = score
            weak_idx = i

    explain_ratio = explain_yes / n
    keep_ratio = editor_keep / n
    opening_tier = tiers[0] if tiers else 5
    opening_compelling = opening_tier <= 2 or (
        decisions
        and int((decisions[0] or {}).get("tier") or 5) <= 3
        and str((decisions[0].get("intent") or {}).get("purpose") or "") == "hook"
    )
    # Publishing justified only if most scenes explain + few static last-resorts
    # and enough decisions carry a real on-disk path (intent alone is not publishable footage)
    static_last = sum(1 for t in tiers if t >= 5)
    real_paths = 0
    for d in decisions or scenes:
        if not isinstance(d, dict):
            continue
        path = (d.get("selected") or {}).get("path") if "selected" in d else (
            d.get("approved_asset_path") or d.get("image") or d.get("path")
        )
        if path and not str(path).startswith(("mock://", "runtime://")):
            real_paths += 1
    path_ratio = real_paths / n
    publish_ok = (
        explain_ratio >= 0.75
        and keep_ratio >= 0.65
        and static_last <= max(1, n // 4)
        and opening_compelling
        and path_ratio >= 0.5
    )

    weakest = None
    if decisions:
        d = decisions[weak_idx]
        weakest = {
            "scene_index": weak_idx,
            "scene_number": (d.get("scene") or {}).get("scene_number") or weak_idx + 1,
            "tier": d.get("tier"),
            "source": (d.get("selected") or {}).get("source_key"),
            "reason": d.get("fallback_reason") or "Lowest selection score among scene decisions",
            "viewer_understanding": (d.get("intent") or {}).get("viewer_understanding"),
        }
    elif scenes:
        s = scenes[weak_idx]
        weakest = {
            "scene_index": weak_idx,
            "scene_number": s.get("scene_number") or weak_idx + 1,
            "tier": tier_guess(s),
            "source": s.get("vsi_source") or s.get("asset_type"),
            "reason": s.get("vsi_fallback_reason") or "Weakest available scene row",
            "viewer_understanding": s.get("viewer_understanding"),
        }

    answers = {
        "every_scene_explains_narration": "YES" if explain_ratio >= 0.85 else ("MOSTLY" if explain_ratio >= 0.6 else "NO"),
        "human_editor_would_keep_shots": "YES" if keep_ratio >= 0.75 else ("MOSTLY" if keep_ratio >= 0.5 else "NO"),
        "opening_visually_compelling": "YES" if opening_compelling else "NO",
        "visual_quality_justifies_publishing": "YES" if publish_ok else "NO",
        "weakest_scene": weakest,
    }

    md_lines = [
        "# Visual Source Intelligence — Creative Review",
        "",
        f"- Every scene visually explains narration: **{answers['every_scene_explains_narration']}** ({explain_yes}/{n})",
        f"- Human editor would keep these shots: **{answers['human_editor_would_keep_shots']}** ({editor_keep}/{n})",
        f"- Opening visually compelling: **{answers['opening_visually_compelling']}**",
        f"- Visual quality justifies publishing: **{answers['visual_quality_justifies_publishing']}**",
    ]
    if weakest:
        md_lines += [
            "",
            "## Weakest scene (not auto-rebuilt)",
            "",
            f"- Scene: `{weakest.get('scene_number')}`",
            f"- Source / tier: `{weakest.get('source')}` / `{weakest.get('tier')}`",
            f"- Why: {weakest.get('reason')}",
        ]
    md_lines += ["", "_Do not automatically rebuild from this review._", ""]

    return {
        "answers": answers,
        "metrics": {
            "scene_count": n,
            "explain_ratio": round(explain_ratio, 3),
            "editor_keep_ratio": round(keep_ratio, 3),
            "static_last_resort_count": static_last,
            "real_path_ratio": round(path_ratio, 3),
            "mean_tier": round(sum(tiers) / max(1, len(tiers)), 2) if tiers else None,
            "opening_tier": opening_tier,
        },
        "publish_justified": publish_ok,
        "markdown": "\n".join(md_lines),
    }


def tier_guess(scene: dict[str, Any]) -> int:
    if scene.get("vsi_tier"):
        return int(scene["vsi_tier"])
    at = str(scene.get("asset_type") or scene.get("vsi_source") or "")
    mapping = {
        "stock_footage": 1,
        "stock_video": 1,
        "ai_video": 2,
        "animated_diagram": 3,
        "ai_image": 4,
        "atlas_image": 5,
    }
    return int(mapping.get(at, 5))
