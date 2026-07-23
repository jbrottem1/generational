"""Select the strongest available visual source per scene."""

from __future__ import annotations

from typing import Any

from services.visual_source_intelligence.catalog import catalog_options_for_scene
from services.visual_source_intelligence.intent import build_scene_intent
from services.visual_source_intelligence.models import (
    MOTION_CYCLE,
    REJECT_REASONS,
    SOURCE_LABELS,
    TIER_TO_ASSET_TYPE,
)


def _score_option(opt: dict[str, Any], *, intent: dict[str, Any], reject_flags: list[str]) -> float:
    """Higher is better. Prefer lower fallback rank, availability, relevance, motion, explainer fit."""
    if not opt.get("available"):
        return -1.0
    rank = int(opt.get("rank") or 5)
    # Ladder: tier 1 ~ 100 base, tier 5 ~ 20
    base = max(0, 120 - rank * 20)
    score = (
        base
        + float(opt.get("relevance") or 0) * 25
        + float(opt.get("motion_score") or 0) * 18
        + float(opt.get("explains_narration") or 0) * 22
    )
    if intent.get("prefers_diagram"):
        if opt.get("source_key") in {"animated_diagram", "motion_graphics", "diagram"}:
            score += 40  # ideal visual for legend/rate/compare beats beats generic AI video
        elif opt.get("source_key") in {"ai_video", "ai_still_motion"}:
            score -= 12
    if intent.get("prefers_motion") and opt.get("source_key") in {"stock_video", "ai_video"}:
        score += 14
    if intent.get("purpose") == "hook" and opt.get("source_key") in {"stock_video", "ai_video"}:
        score += 16
    if "obvious_placeholder" in reject_flags and opt.get("source_key") in {"cinematic_fallback", "placeholder"}:
        score -= 80
    if "feels_like_slideshow" in reject_flags and opt.get("source_key") == "static_image":
        score -= 25
    return score


def reject_flags_for_option(opt: dict[str, Any], *, camera_seen: set[str], motion_label: str) -> list[str]:
    flags: list[str] = []
    key = str(opt.get("source_key") or "")
    if key in {"cinematic_fallback", "placeholder"} or str(opt.get("path") or "").startswith(("mock://", "runtime://")):
        flags.append("obvious_placeholder")
    if key == "static_image" and float(opt.get("motion_score") or 0) < 0.2:
        flags.append("feels_like_slideshow")
        flags.append("lacks_cinematic_interest")
    if motion_label and motion_label in camera_seen:
        flags.append("repeated_identical_camera")
    if float(opt.get("explains_narration") or 0) < 0.35 and float(opt.get("relevance") or 0) < 0.35:
        flags.append("fails_to_explain_narration")
    if float(opt.get("relevance") or 0) < 0.2:
        flags.append("low_relevance")
    # Only keep known reasons
    return [f for f in flags if f in REJECT_REASONS]


def choose_source(
    scene: dict[str, Any],
    *,
    candidate: dict[str, Any] | None = None,
    topic: str = "",
    used_paths: set[str] | None = None,
    camera_seen: set[str] | None = None,
    scene_index: int = 0,
) -> dict[str, Any]:
    """Pick highest-quality available option; record fallback ladder position + why."""
    intent = build_scene_intent(scene, topic=topic)
    options = catalog_options_for_scene(
        scene, candidate=candidate, topic=topic, used_paths=used_paths
    )
    camera_seen = camera_seen or set()
    motion_label = MOTION_CYCLE[scene_index % len(MOTION_CYCLE)]

    ranked: list[dict[str, Any]] = []
    for opt in options:
        flags = reject_flags_for_option(opt, camera_seen=camera_seen, motion_label=motion_label)
        score = _score_option(opt, intent=intent, reject_flags=flags)
        ranked.append({**opt, "reject_flags": flags, "selection_score": round(score, 2)})
    ranked.sort(key=lambda r: (-float(r["selection_score"]), int(r["rank"])))

    available = [r for r in ranked if r.get("available") and float(r["selection_score"]) >= 0]
    # Walk mission ladder: among available, prefer best score (already sorted)
    selected = available[0] if available else (ranked[0] if ranked else None)
    if selected is None:
        selected = {
            "source_key": "ai_still_motion",
            "rank": 4,
            "available": True,
            "reason": "No catalog options — defaulting to AI still with motion",
            "selection_score": 0,
            "reject_flags": [],
            "path": None,
            "meta": {},
        }

    tier = int(selected.get("rank") or 4)
    asset_type = TIER_TO_ASSET_TYPE.get(tier, "ai_image")
    # Prefer keeping stock/ai_video asset types precise
    if selected.get("source_key") in {"stock_video", "licensed_stock_video", "library_video", "stock_footage"}:
        asset_type = "stock_footage"
    elif selected.get("source_key") in {"ai_video", "ai_generated_video"}:
        asset_type = "ai_video"
    elif selected.get("source_key") == "animated_diagram":
        asset_type = "ai_image"

    fallback_used = tier > 1 or selected.get("source_key") not in {
        "stock_video",
        "licensed_stock_video",
        "library_video",
        "stock_footage",
    }

    return {
        "intent": intent,
        "selected": selected,
        "alternatives": ranked[:6],
        "asset_type": asset_type,
        "tier": tier,
        "tier_label": SOURCE_LABELS.get(tier, "unknown"),
        "fallback_used": fallback_used,
        "fallback_reason": selected.get("reason")
        or ("Best available on mission ladder" if not fallback_used else "Higher ladder tiers unavailable"),
        "camera_motion": motion_label,
        "media_type": (selected.get("meta") or {}).get("media_type")
        or (
            "motion_graphics"
            if selected.get("source_key") == "animated_diagram"
            else ("video" if asset_type in {"stock_footage", "ai_video"} else "image")
        ),
    }


def apply_choice_to_scene(scene: dict[str, Any], choice: dict[str, Any]) -> dict[str, Any]:
    """Mutate a scene copy with VSI decisions — soft fields for renderer/VAD."""
    out = dict(scene)
    selected = choice.get("selected") or {}
    intent = choice.get("intent") or {}
    out["asset_type"] = choice.get("asset_type") or out.get("asset_type") or "ai_image"
    out["vsi_source"] = selected.get("source_key")
    out["vsi_tier"] = choice.get("tier")
    out["vsi_tier_label"] = choice.get("tier_label")
    out["vsi_fallback_used"] = choice.get("fallback_used")
    out["vsi_fallback_reason"] = choice.get("fallback_reason")
    out["viewer_understanding"] = intent.get("viewer_understanding")
    out["ideal_visual"] = intent.get("ideal_visual")
    out["media_type"] = choice.get("media_type") or out.get("media_type")
    # Diversify camera — avoid identical Ken Burns across beats
    out["camera_motion"] = choice.get("camera_motion") or out.get("camera_motion")
    out["required_motion"] = choice.get("camera_motion")
    meta = selected.get("meta") or {}
    if meta.get("prompt") and out["asset_type"] == "ai_video":
        out["ai_video_prompt"] = meta.get("prompt") or out.get("ai_video_prompt")
    if meta.get("prompt") and out["asset_type"] == "ai_image":
        # Prefer ideal visual explaining narration
        out["ai_image_prompt"] = (
            f"{intent.get('ideal_visual') or ''} {meta.get('prompt') or out.get('ai_image_prompt') or ''}".strip()
        )
    if selected.get("source_key") == "animated_diagram":
        out["overlay_style"] = "annotated diagram callouts, data labels"
        out["annotation_plan"] = meta.get("overlay_plan") or "keyword callouts synced to narration"
        out["motion_plan"] = "diagram build-on / reveal aligned to narration clauses"
    path = selected.get("path")
    if path:
        out["approved_asset_path"] = path
        out["image"] = out.get("image") or path
        if str(path).lower().endswith((".mp4", ".mov", ".webm", ".m4v")):
            out["video_path"] = path
            out["asset_kind"] = "video"
        else:
            out["asset_kind"] = "image"
    # Meaningful motion requirement for stills
    if choice.get("tier") == 4:
        out["ken_burns"] = False  # prefer directed motion label over default slideshow pan
        out["motion_required"] = True
        out["cinematic_motion"] = choice.get("camera_motion")
    return out
