"""Module 3 — Transition Engine: context-selected cinematic transitions."""

from __future__ import annotations

from services.studio_render.models import TRANSITIONS_V3

_RULES: list[tuple[tuple[str, ...], str, str]] = [
    (("suddenly", "shock", "impact", "crash"), "whip_pan", "Impact beat → whip pan"),
    (("meanwhile", "elsewhere", "across"), "directional_wipe", "Location shift → wipe"),
    (("zoom", "closer", "detail", "macro"), "zoom_transition", "Scale change → zoom transition"),
    (("reveal", "hidden", "behind"), "object_reveal", "Reveal language → object reveal"),
    (("focus", "blur", "sharp"), "focus_pull", "Focus language → focus pull"),
    (("depth", "layers", "parallax"), "parallax_transition", "Depth cue → parallax"),
    (("history", "years ago", "then", "past"), "fade_through_black", "Temporal jump → fade black"),
    (("same", "identical", "match"), "match_cut", "Continuity → match cut"),
    (("morph", "becomes", "transforms"), "morph", "Transformation → morph"),
    (("fast", "rapid", "accelerate"), "speed_ramp", "Pace surge → speed ramp"),
    (("light", "flash", "bright"), "light_flash", "Light cue → flash"),
    (("dream", "soft", "dissolve"), "cinematic_dissolve", "Soft tone → cinematic dissolve"),
]


def choose_transition(narration: str, *, index: int = 0, next_narration: str = "") -> tuple[str, str]:
    text = f"{narration} {next_narration}".lower()
    for keys, transition, reason in _RULES:
        if any(k in text for k in keys):
            return transition, reason
    # Deterministic non-generic fallbacks — never plain hard cut as default
    cycle = (
        ("cross_dissolve", "Default educational cross dissolve"),
        ("cinematic_dissolve", "Documentary dissolve"),
        ("depth_transition", "Depth transition for variety"),
        ("motion_blur", "Motion-blur bridge"),
    )
    return cycle[index % len(cycle)]


def build_transitions(candidate: dict) -> list[dict]:
    scenes = list((candidate.get("visual_package") or {}).get("scenes") or [])
    if not scenes:
        scenes = list((candidate.get("evidence_package") or {}).get("scenes") or [])
    if len(scenes) < 2:
        scenes = scenes or [{"scene_id": "s1", "narration": ""}]
        scenes = scenes + [{"scene_id": "s2", "narration": "payoff"}]

    out: list[dict] = []
    for i in range(len(scenes) - 1):
        a = scenes[i]
        b = scenes[i + 1]
        tr, reason = choose_transition(
            str(a.get("narration") or ""),
            index=i,
            next_narration=str(b.get("narration") or ""),
        )
        assert tr in TRANSITIONS_V3
        out.append(
            {
                "from_scene": str(a.get("scene_id") or f"s{i+1}"),
                "to_scene": str(b.get("scene_id") or f"s{i+2}"),
                "type": tr,
                "duration_sec": 0.45 if tr in ("whip_pan", "light_flash", "speed_ramp") else 0.7,
                "reason": reason,
            }
        )
    return out
