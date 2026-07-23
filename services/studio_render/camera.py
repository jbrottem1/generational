"""Module 9 — Camera Choreography: multi-stage cinematic moves."""

from __future__ import annotations

from services.cinematography.animation_adapter import get_animation_handoff

COMPOUND_MOVES = (
    "orbit_plus_zoom",
    "push_plus_rack_focus",
    "pan_plus_tilt",
    "reveal_plus_dolly",
    "macro_transition",
    "object_tracking",
    "dynamic_framing",
    "subject_locking",
)


def _compound_for(narration: str, base: str, index: int) -> tuple[str, list[str], str]:
    text = (narration or "").lower()
    if any(w in text for w in ("orbit", "tilt", "spin", "rotate")):
        return "orbit_plus_zoom", ["orbit", "slow_push"], "Orbit + zoom for rotational subject"
    if any(w in text for w in ("notice", "focus", "tiny", "macro", "detail")):
        return "push_plus_rack_focus", ["slow_push", "rack_focus"], "Push + rack focus on detail"
    if any(w in text for w in ("reveal", "hidden", "behind")):
        return "reveal_plus_dolly", ["reveal", "dolly"], "Reveal + dolly"
    if any(w in text for w in ("follow", "track", "along")):
        return "object_tracking", ["tracking"], "Object tracking with subject lock"
    if any(w in text for w in ("wide", "landscape", "establishing")):
        return "pan_plus_tilt", ["horizontal_pan", "vertical_pan"], "Pan + tilt establishing"
    if "macro" in base or "push" in base:
        return "macro_transition", [base, "rack_focus"], "Macro transition with smoothing"
    cycle = (
        ("dynamic_framing", [base or "slow_push"], "Dynamic framing with motion smoothing"),
        ("subject_locking", [base or "tracking"], "Subject lock + smoothed follow"),
        ("orbit_plus_zoom", ["orbit", "slow_push"], "Compound orbit/zoom variety"),
    )
    return cycle[index % len(cycle)]


def build_camera_choreography(candidate: dict) -> list[dict]:
    handoff = get_animation_handoff(candidate) if candidate.get("animation_handoff") or candidate.get("cinematography_plan") else {}
    if not isinstance(handoff, dict):
        handoff = {}
    handoff_scenes = {
        str(s.get("scene_id") or ""): s
        for s in (handoff.get("scenes") or [])
        if isinstance(s, dict)
    }

    vp = candidate.get("visual_package") if isinstance(candidate.get("visual_package"), dict) else {}
    ep = candidate.get("evidence_package") if isinstance(candidate.get("evidence_package"), dict) else {}
    scenes = [s for s in list(vp.get("scenes") or []) if isinstance(s, dict)]
    if not scenes:
        scenes = [s for s in list(ep.get("scenes") or []) if isinstance(s, dict)]
    vr = candidate.get("viewer_retention_package") if isinstance(candidate.get("viewer_retention_package"), dict) else {}
    vr_cam = vr.get("camera_plan") or []
    vr_by_id = {str(c.get("scene_id")): c for c in vr_cam if isinstance(c, dict)}

    choreo: list[dict] = []
    for i, scene in enumerate(scenes or [{"scene_id": "s1", "narration": ""}]):
        sid = str(scene.get("scene_id") or f"s{i+1}")
        narration = str(scene.get("narration") or "")
        base = ""
        if sid in handoff_scenes:
            cam = handoff_scenes[sid].get("camera")
            if isinstance(cam, dict):
                base = str(cam.get("movement") or cam.get("move") or "")
            elif isinstance(cam, str):
                base = cam
            if not base:
                base = str(handoff_scenes[sid].get("movement") or "")
        if not base and sid in vr_by_id:
            base = str(vr_by_id[sid].get("motion") or vr_by_id[sid].get("legacy_movement") or "")
        compound, stages, reason = _compound_for(narration, base, i)
        choreo.append(
            {
                "scene_id": sid,
                "compound_move": compound,
                "stages": stages,
                "smoothing": 0.88,
                "subject_lock": compound in ("object_tracking", "subject_locking"),
                "mechanical": False,
                "cinematic": True,
                "reason": reason,
            }
        )
    return choreo
