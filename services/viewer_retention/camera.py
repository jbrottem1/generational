"""Module 3 — Cinematic Camera Engine: narration-matched motion (never random)."""

from __future__ import annotations

from services.viewer_retention.models import (
    CINEMATIC_MOTIONS_V2,
    MOTION_TO_LEGACY,
    CameraDirective,
)

_RULES: list[tuple[tuple[str, ...], str, str]] = [
    (("notice", "look at", "this detail", "zoom"), "macro_push", "Detail cue → macro push"),
    (("tiny", "micro", "cell", "chip", "atom"), "macro_push", "Scale cue → macro"),
    (("orbit", "tilt", "spin", "rotate", "axis"), "orbit", "Rotation cue → orbit"),
    (("across", "landscape", "horizon", "wide"), "drone_simulation", "Wide geography → drone"),
    (("reveal", "hidden", "behind", "secret"), "reveal", "Reveal language → reveal move"),
    (("follow", "along", "track", "path"), "tracking", "Path language → tracking"),
    (("factory", "assembly", "machine arm"), "parallax", "Industrial depth → parallax"),
    (("suddenly", "shock", "impact", "crash"), "crash_zoom", "Impact beat → crash zoom"),
    (("focus", "sharp", "blur", "depth"), "rack_focus", "Focus language → rack focus"),
    (("cut to", "meanwhile", "switch"), "whip_pan", "Hard shift → whip pan"),
    (("rise", "climb", "ascend", "tower"), "tilt", "Vertical rise → tilt"),
    (("walk", "move through", "into the"), "dolly", "Traversal → dolly"),
    (("history", "archive", "old", "then"), "ken_burns", "Archival still → Ken Burns"),
    (("field", "documentary", "on the ground"), "handheld_documentary", "Doc tone → handheld"),
]


def choose_cinematic_motion(narration: str, *, scene_index: int = 0) -> tuple[str, str]:
    text = (narration or "").lower()
    for keywords, motion, reason in _RULES:
        if any(k in text for k in keywords):
            return motion, reason
    # Deterministic fallback by beat position — never random
    fallbacks = (
        ("slow_push", "Default educational push-in"),
        ("parallax", "Depth variation mid-beat"),
        ("orbit", "Curiosity orbit"),
        ("ken_burns", "Still-photo Ken Burns"),
        ("reveal", "Payoff reveal"),
    )
    motion, reason = fallbacks[scene_index % len(fallbacks)]
    return motion, reason


def build_camera_plan(candidate: dict, pacing: list | None = None) -> list[CameraDirective]:
    vp = candidate.get("visual_package") or {}
    scenes = list(vp.get("scenes") or [])
    if not scenes:
        ep = candidate.get("evidence_package") or {}
        scenes = list(ep.get("scenes") or [])

    cine = candidate.get("cinematography_plan") or {}
    cine_scenes = {str(s.get("scene_id") or ""): s for s in (cine.get("scenes") or [])}

    plan: list[CameraDirective] = []
    if not scenes:
        motion, reason = choose_cinematic_motion("Stay with this idea.", scene_index=0)
        plan.append(
            CameraDirective(
                scene_id="hook",
                motion=motion,
                legacy_movement=MOTION_TO_LEGACY.get(motion, "slow_push_in"),
                intensity=0.7,
                reason=reason,
                narration_cue="hook",
            )
        )
        return plan

    for i, scene in enumerate(scenes):
        sid = str(scene.get("scene_id") or scene.get("id") or f"s{i+1}")
        narration = str(scene.get("narration") or scene.get("voiceover") or "")
        # Prefer existing cinematography if already narration-matched
        existing = cine_scenes.get(sid) or {}
        if existing.get("movement") and existing.get("reason"):
            legacy = str(existing["movement"])
            # Reverse-map to V2 label when possible
            motion = next(
                (m for m, leg in MOTION_TO_LEGACY.items() if leg == legacy),
                "slow_push" if "push" in legacy else legacy,
            )
            if motion not in CINEMATIC_MOTIONS_V2:
                motion = "slow_push"
            reason = f"Aligned with cinematography: {existing.get('reason')}"
        else:
            motion, reason = choose_cinematic_motion(narration, scene_index=i)

        intensity = 0.55 + min(0.4, (i % 4) * 0.08)
        if pacing and i < len(pacing):
            p = pacing[i]
            label = getattr(p, "pacing_label", None) or (p.get("pacing_label") if isinstance(p, dict) else "")
            if label in ("cut_2s", "montage", "crash_zoom"):
                intensity = min(1.0, intensity + 0.15)
            if label == "dramatic_pause":
                intensity = max(0.35, intensity - 0.2)

        plan.append(
            CameraDirective(
                scene_id=sid,
                motion=motion,
                legacy_movement=MOTION_TO_LEGACY.get(motion, "slow_push_in"),
                intensity=round(intensity, 2),
                reason=reason,
                narration_cue=narration[:80],
            )
        )
    return plan


def apply_camera_to_cinematography(candidate: dict, camera_plan: list[CameraDirective]) -> dict:
    """Additively enrich cinematography_plan scenes with V2 motion metadata."""
    plan = dict(candidate.get("cinematography_plan") or {})
    scenes = list(plan.get("scenes") or [])
    by_id = {d.scene_id: d for d in camera_plan}
    enriched = []
    for scene in scenes:
        row = dict(scene)
        sid = str(row.get("scene_id") or "")
        directive = by_id.get(sid)
        if directive:
            row["v2_motion"] = directive.motion
            row["v2_intensity"] = directive.intensity
            row["v2_reason"] = directive.reason
            # Prefer V2 legacy mapping when movement was generic
            if not row.get("movement") or row.get("movement") == "static_hold":
                row["movement"] = directive.legacy_movement
                row["reason"] = directive.reason
        enriched.append(row)
    if not enriched and camera_plan:
        enriched = [
            {
                "scene_id": d.scene_id,
                "movement": d.legacy_movement,
                "v2_motion": d.motion,
                "v2_intensity": d.intensity,
                "reason": d.reason,
                "attention_score": 80,
            }
            for d in camera_plan
        ]
    plan["scenes"] = enriched
    plan["v2_camera_count"] = len(camera_plan)
    candidate["cinematography_plan"] = plan
    return plan
