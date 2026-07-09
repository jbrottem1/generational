"""Transitions, visual effects, particles, lighting, motion graphics, audio sync."""

from __future__ import annotations

from services.animation.config import AnimationConfig
from services.animation.models import EffectType, TransitionType

_TRANSITION_MAP = (
    ("match cut", TransitionType.MATCH_CUT),
    ("match", TransitionType.MATCH_CUT),
    ("dissolve", TransitionType.DISSOLVE),
    ("fade", TransitionType.FADE),
    ("whip", TransitionType.WHIP),
    ("blur", TransitionType.BLUR),
    ("zoom", TransitionType.ZOOM),
    ("object", TransitionType.OBJECT),
    ("cut", TransitionType.CUT),
)

_EFFECT_HINTS = (
    ("smoke", EffectType.SMOKE),
    ("fire", EffectType.FIRE),
    ("flame", EffectType.FIRE),
    ("rain", EffectType.RAIN),
    ("snow", EffectType.SNOW),
    ("fog", EffectType.FOG),
    ("mist", EffectType.FOG),
    ("dust", EffectType.DUST),
    ("magic", EffectType.MAGIC),
    ("energy", EffectType.ENERGY),
    ("glow", EffectType.ENERGY),
    ("explod", EffectType.EXPLOSION),
    ("water", EffectType.WATER),
    ("ocean", EffectType.WATER),
    ("lightning", EffectType.LIGHTING),
    ("light streak", EffectType.LIGHTING),
)


def _resolve_transition(text: str, default: str) -> str:
    lowered = (text or "").lower()
    for fragment, transition in _TRANSITION_MAP:
        if fragment in lowered:
            return transition
    return default if default in TransitionType.ALL else TransitionType.CUT


def plan_transitions(
    scenes: "list[dict]",
    scene_timing: "list[dict]",
    camera_plan: dict,
    config: AnimationConfig,
) -> "list[dict]":
    timing_by_scene = {t["scene_id"]: t for t in scene_timing}
    transitions: "list[dict]" = []

    for index, scene in enumerate(scenes[:-1]):
        nxt = scenes[index + 1]
        out_text = ""
        scene_transitions = scene.get("transitions") or {}
        if isinstance(scene_transitions, dict):
            out_text = str(scene_transitions.get("out", ""))
        elif isinstance(scene_transitions, str):
            out_text = scene_transitions
        t_type = _resolve_transition(out_text, config.default_transition)
        at = float(timing_by_scene.get(scene.get("scene_id", ""), {}).get("end_sec", 0))
        duration = {
            TransitionType.CUT: 0.0,
            TransitionType.WHIP: 0.18,
            TransitionType.BLUR: 0.35,
            TransitionType.FADE: 0.6,
            TransitionType.DISSOLVE: 0.7,
            TransitionType.MATCH_CUT: 0.05,
            TransitionType.ZOOM: 0.4,
            TransitionType.OBJECT: 0.5,
        }.get(t_type, 0.25)
        transitions.append({
            "transition_id": f"tr_{scene.get('scene_id')}_{nxt.get('scene_id')}",
            "from_ref": str(scene.get("scene_id", "")),
            "to_ref": str(nxt.get("scene_id", "")),
            "transition_type": t_type,
            "duration_sec": duration,
            "at_sec": round(at, 3),
            "params": {"easing": "ease_in_out"},
        })

    # Shot-level cuts inside multi-shot scenes (always hard cuts unless noted).
    shots = camera_plan.get("shots", [])
    for index, shot in enumerate(shots[:-1]):
        nxt = shots[index + 1]
        if shot.get("scene_id") == nxt.get("scene_id"):
            transitions.append({
                "transition_id": f"tr_{shot['shot_id']}_{nxt['shot_id']}",
                "from_ref": shot["shot_id"],
                "to_ref": nxt["shot_id"],
                "transition_type": TransitionType.CUT,
                "duration_sec": 0.0,
                "at_sec": round(float(shot.get("end_sec", 0)), 3),
                "params": {},
            })
    return transitions


def plan_visual_effects(
    scenes: "list[dict]",
    scene_timing: "list[dict]",
    config: AnimationConfig,
) -> "tuple[list[dict], list[dict]]":
    """Return (visual_effects, particle_effects)."""
    if not config.enable_vfx:
        return [], []

    timing_by_scene = {t["scene_id"]: t for t in scene_timing}
    effects: "list[dict]" = []
    particles: "list[dict]" = []
    particle_types = {
        EffectType.SMOKE, EffectType.FIRE, EffectType.RAIN, EffectType.SNOW,
        EffectType.FOG, EffectType.DUST, EffectType.MAGIC, EffectType.ENERGY,
        EffectType.EXPLOSION, EffectType.WATER,
    }

    for scene in scenes:
        text = " ".join(
            str(scene.get(key, ""))
            for key in ("visual_description", "background", "motion_instructions", "lighting")
        ).lower()
        scene_id = scene.get("scene_id", "")
        timing = timing_by_scene.get(scene_id, {})
        start = float(timing.get("start_sec", 0))
        end = float(timing.get("end_sec", start + 3))
        matched = []
        for fragment, effect_type in _EFFECT_HINTS:
            if fragment in text and effect_type not in matched:
                matched.append(effect_type)
        for effect_type in matched:
            entry = {
                "effect_id": f"fx_{scene_id}_{effect_type}",
                "scene_id": scene_id,
                "effect_type": effect_type,
                "start_sec": start,
                "end_sec": end,
                "intensity": config.motion_intensity,
                "params": {},
                "plugin": "",
            }
            effects.append(entry)
            if effect_type in particle_types:
                particles.append({
                    **entry,
                    "effect_id": f"pt_{scene_id}_{effect_type}",
                    "params": {"emitter": "scene", "density": config.motion_intensity},
                })
    return effects, particles


def plan_lighting_cues(
    scenes: "list[dict]",
    scene_timing: "list[dict]",
    camera_plan: dict,
) -> "list[dict]":
    timing_by_scene = {t["scene_id"]: t for t in scene_timing}
    shots_by_scene: "dict[str, list]" = {}
    for shot in camera_plan.get("shots", []):
        shots_by_scene.setdefault(shot.get("scene_id", ""), []).append(shot)

    cues: "list[dict]" = []
    for scene in scenes:
        scene_id = scene.get("scene_id", "")
        timing = timing_by_scene.get(scene_id, {})
        lighting = str(scene.get("lighting", "soft key")).lower()
        mood = str(scene.get("emotion", "neutral"))
        temp = 5600
        if "warm" in lighting or "golden" in lighting:
            temp = 3200
        elif "cool" in lighting or "moon" in lighting or "night" in lighting:
            temp = 7200
        elif "neon" in lighting:
            temp = 9000
        intensity = 0.7
        if "dramatic" in lighting or "hard" in lighting:
            intensity = 0.95
        elif "soft" in lighting:
            intensity = 0.55
        shot_ids = [s["shot_id"] for s in shots_by_scene.get(scene_id, [])] or [""]
        for shot_id in shot_ids:
            cues.append({
                "cue_id": f"light_{scene_id}_{shot_id or 'scene'}",
                "scene_id": scene_id,
                "shot_id": shot_id,
                "start_sec": float(timing.get("start_sec", 0)),
                "end_sec": float(timing.get("end_sec", 0)),
                "mood": mood,
                "key_light": lighting or "soft key",
                "fill_light": "soft fill",
                "rim_light": "subtle rim" if intensity > 0.6 else "none",
                "color_temperature_k": temp,
                "intensity": intensity,
            })
    return cues


def plan_motion_graphics(
    scenes: "list[dict]",
    scene_timing: "list[dict]",
    item: dict,
    config: AnimationConfig,
) -> "list[dict]":
    if not config.enable_motion_graphics:
        return []
    if not scenes or not scene_timing:
        return []

    gfx: "list[dict]" = []
    first = scenes[0]
    first_t = scene_timing[0]
    title = str(item.get("title") or item.get("topic") or "Untitled")
    gfx.append({
        "gfx_id": "gfx_title",
        "scene_id": first.get("scene_id", ""),
        "kind": "title",
        "start_sec": float(first_t.get("start_sec", 0)),
        "end_sec": min(float(first_t.get("end_sec", 2)), float(first_t.get("start_sec", 0)) + 2.0),
        "text": title[:80],
        "motion": "fade_up",
        "style": config.animation_style,
    })
    if item.get("hook"):
        gfx.append({
            "gfx_id": "gfx_hook_lower_third",
            "scene_id": first.get("scene_id", ""),
            "kind": "lower_third",
            "start_sec": float(first_t.get("start_sec", 0)) + 0.4,
            "end_sec": min(float(first_t.get("end_sec", 3)), float(first_t.get("start_sec", 0)) + 3.0),
            "text": str(item.get("hook", ""))[:60],
            "motion": "slide_in",
            "style": config.animation_style,
        })
    last = scenes[-1]
    last_t = scene_timing[-1]
    gfx.append({
        "gfx_id": "gfx_end_card",
        "scene_id": last.get("scene_id", ""),
        "kind": "end_card",
        "start_sec": max(float(last_t.get("start_sec", 0)), float(last_t.get("end_sec", 0)) - 2.0),
        "end_sec": float(last_t.get("end_sec", 0)),
        "text": "Subscribe",
        "motion": "fade_in",
        "style": config.animation_style,
    })
    return gfx


def plan_audio_sync(
    scenes: "list[dict]",
    scene_timing: "list[dict]",
    item: dict,
) -> "list[dict]":
    audio = item.get("audio_package") or {}
    music = item.get("music_assets") or audio.get("music") or {}
    sync: "list[dict]" = []
    for timing in scene_timing:
        scene = next((s for s in scenes if s.get("scene_id") == timing["scene_id"]), {})
        if scene.get("narration"):
            sync.append({
                "sync_id": f"aud_voice_{timing['scene_id']}",
                "track": "voice",
                "ref_id": timing["scene_id"],
                "start_sec": timing["start_sec"],
                "end_sec": timing["end_sec"],
                "offset_sec": 0.0,
                "notes": "align to lip_sync_plan",
            })
    if scene_timing:
        sync.append({
            "sync_id": "aud_music_bed",
            "track": "music",
            "ref_id": str(music.get("asset_id") or music.get("uri") or "music_bed"),
            "start_sec": scene_timing[0]["start_sec"],
            "end_sec": scene_timing[-1]["end_sec"],
            "offset_sec": 0.0,
            "notes": "underscore full timeline",
        })
    return sync


def plan_subtitle_timing(
    scenes: "list[dict]",
    scene_timing: "list[dict]",
    lip_sync_plan: "list[dict]",
) -> "list[dict]":
    # Prefer lip-sync word/sentence timings when available.
    cues: "list[dict]" = []
    if lip_sync_plan:
        for plan in lip_sync_plan:
            for index, sentence in enumerate(plan.get("sentences") or []):
                cues.append({
                    "cue_id": f"sub_{plan['scene_id']}_{index}",
                    "start_sec": float(sentence.get("start_sec", 0)),
                    "end_sec": float(sentence.get("end_sec", 0)),
                    "text": str(sentence.get("text", "")),
                    "speaker": plan.get("character_id", ""),
                    "scene_id": plan.get("scene_id", ""),
                })
        if cues:
            return cues

    timing_by_scene = {t["scene_id"]: t for t in scene_timing}
    for scene in scenes:
        narration = str(scene.get("narration") or "").strip()
        if not narration:
            continue
        timing = timing_by_scene.get(scene.get("scene_id", ""), {})
        cues.append({
            "cue_id": f"sub_{scene.get('scene_id')}",
            "start_sec": float(timing.get("start_sec", 0)),
            "end_sec": float(timing.get("end_sec", 0)),
            "text": narration[:120],
            "speaker": (scene.get("characters") or ["narrator"])[0],
            "scene_id": scene.get("scene_id", ""),
        })
    return cues
