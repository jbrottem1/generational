"""Character / world / object / motion-graphics layer planners (V2 cinematic)."""

from __future__ import annotations

from typing import Any

from services.animation_engine.cinematic import immersion_checklist, plan_cinematic_intent
from services.animation_engine.intent import (
    detect_characters,
    detect_object_animations,
    detect_world_type,
    muted_comprehension_beat,
    narration_text,
)
from services.animation_engine.models import (
    CHARACTER_ACTIONS,
    CHARACTER_MICRO,
    MOTION_GRAPHICS_TYPES,
    WORLD_ANIMATIONS,
    WORLD_DEPTH_LAYERS,
)


def plan_character_layer(
    scene: dict[str, Any],
    *,
    topic: str = "",
    cinematic: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    cinematic = cinematic or {}
    # Prefer Character & World Studio host when stamped
    if scene.get("studio_character_id"):
        emotion = str(cinematic.get("emotion") or scene.get("director_emotion") or "focus")
        perf = str(scene.get("studio_performance") or "point_teach")
        return {
            "enabled": True,
            "characters": [
                {
                    "name": scene.get("studio_character_name") or scene.get("studio_character_id"),
                    "kind": "studio_host",
                    "id": scene.get("studio_character_id"),
                    "source": "character_world_studio",
                }
            ],
            "actions": list(CHARACTER_ACTIONS),
            "micro_performance": list(CHARACTER_MICRO),
            "performance": perf,
            "emotion": emotion,
            "expression": scene.get("studio_expression"),
            "gestures": list(scene.get("studio_gestures") or []),
            "character_plate_path": scene.get("character_plate_path") or scene.get("approved_character_path"),
            "alive_requirements": [
                "blink_naturally",
                "breathe",
                "weight_shift",
                "eye_focus",
                "head_turn",
                "gesture_while_speaking",
                "facial_expression",
                "anticipation_and_follow_through",
                "visual_consistency_across_scenes",
                "no_mannequin_behavior",
                "no_abstract_placeholder",
            ],
            "primary": {
                "name": scene.get("studio_character_name"),
                "id": scene.get("studio_character_id"),
            },
            "forbid_mannequin": True,
            "forbid_stick_placeholder": True,
            "source": "character_world_studio",
        }

    chars = detect_characters(scene, topic=topic)
    if not chars:
        return None
    primary = chars[0]
    text = narration_text(scene).lower()
    emotion = str(cinematic.get("emotion") or "focus")
    if any(w in text for w in ("point", "show", "look", "notice", "this")):
        performance = "point_teach"
    elif any(w in text for w in ("swim", "ocean", "sea", "float")):
        performance = "swim_float"
    elif any(w in text for w in ("win", "save", "triumph", "celebrate")) or emotion == "clarity":
        performance = "celebrate"
    else:
        performance = "walk_explain"
    return {
        "enabled": True,
        "characters": chars,
        "actions": list(CHARACTER_ACTIONS),
        "micro_performance": list(CHARACTER_MICRO),
        "performance": performance,
        "emotion": emotion,
        "alive_requirements": [
            "blink_naturally",
            "breathe",
            "weight_shift",
            "eye_focus",
            "head_turn",
            "gesture_while_speaking",
            "anticipation_and_follow_through",
            "lip_sync_with_narration",
            "visual_consistency_across_scenes",
            "no_mannequin_behavior",
        ],
        "primary": primary,
        "forbid_mannequin": True,
    }


def plan_world_layer(
    candidate: dict[str, Any],
    scene: dict[str, Any],
    *,
    topic: str = "",
    cinematic: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cinematic = cinematic or {}
    env = detect_world_type(candidate, scene, topic=topic)
    anims = list(WORLD_ANIMATIONS.get(env) or WORLD_ANIMATIONS["generic"])
    depth = dict(WORLD_DEPTH_LAYERS.get(env) or WORLD_DEPTH_LAYERS["generic"])
    lighting = str(cinematic.get("lighting_mood") or "soft_daylight")
    palette = {
        "forest": "forest",
        "ocean": "ocean",
        "laboratory": "lab",
        "space": "night",
        "city": "night",
        "countryside": "ireland",
        "interior": "lab",
    }.get(env, "ireland" if "irish" in topic.lower() or "ireland" in topic.lower() else "ocean")
    if lighting in {"golden_hour", "firelight"}:
        palette = "gold" if env in {"countryside", "interior"} else palette
    if lighting == "moonlight":
        palette = "night"
    return {
        "enabled": True,
        "environment": env,
        "animations": anims,
        "depth_layers": depth,
        "living_background": True,
        "forbid_frozen_background": True,
        "allow_abstract_geometry": False,
        "continues_without_narration": True,
        "lighting_mood": lighting,
        "atmospheric_perspective": True,
        "volumetric_lighting": lighting in {"volumetric_sunlight", "golden_hour", "god_rays", "firelight"},
        "palette_hint": palette,
        "environmental_storytelling": True,
    }


def plan_object_layer(scene: dict[str, Any], *, topic: str = "") -> dict[str, Any]:
    objs = detect_object_animations(scene, topic=topic)
    return {
        "enabled": bool(objs),
        "objects": objs,
        "physics_believable": True,
        "note": "Objects obey weight and momentum — no mechanical teleport motion",
    }


def plan_particles_and_light(scene: dict[str, Any], world: dict[str, Any]) -> dict[str, Any]:
    env = str(world.get("environment") or "generic")
    mood = str(world.get("lighting_mood") or "soft_daylight")
    particles = {
        "forest": ["pollen", "leaf_specks", "god_ray_motes"],
        "ocean": ["spray_mist", "caustics"],
        "laboratory": ["dust_motes", "screen_glow"],
        "space": ["star_field_drift", "nebula_wisps"],
        "city": ["rain_or_heat_haze", "headlight_streaks"],
        "countryside": ["mist", "dust_motes", "pollen"],
        "interior": ["dust_motes", "lamp_haze"],
    }.get(env, ["ambient_particles", "dust_motes"])
    lighting = {
        "soft_daylight": ["key_soft", "fill_bounce", "rim_soft"],
        "golden_hour": ["warm_key", "long_shadow_drift", "volumetric_wash"],
        "storm": ["cool_key", "flash_accent", "heavy_cloud_shadow"],
        "moonlight": ["cool_rim", "low_fill", "silver_highlight"],
        "firelight": ["warm_flicker", "ember_rise", "practical_bounce"],
        "volumetric_sunlight": ["god_rays", "mote_drift", "canopy_break"],
        "cinematic_contrast": ["hard_key", "deep_shadow", "rim_edge"],
        "practical_interior": ["practical_glow", "ambient_bounce", "screen_wash"],
    }.get(mood, ["key_drift", "rim_pulse", "practical_flicker"])
    return {
        "particle_effects": particles,
        "lighting_movement": lighting,
        "lighting_mood": mood,
        "physics_animation": bool(plan_object_layer(scene).get("enabled")),
        "grounded_not_floating": True,
    }


def plan_motion_graphics(scene: dict[str, Any], *, cinematic: dict[str, Any] | None = None) -> dict[str, Any]:
    text = narration_text(scene).lower()
    cinematic = cinematic or {}
    items: list[dict[str, Any]] = []
    if any(w in text for w in ("map", "where", "across", "street", "ireland")):
        items.append({"type": "map", "ease_in": "ease_out", "reason": "Location/context beat"})
    if any(w in text for w in ("percent", "%", "rate", "number", "million")) or any(c.isdigit() for c in text):
        items.append({"type": "kinetic_typography", "reason": "Numeric / claim emphasis"})
    if any(w in text for w in ("diagram", "label", "indicates", "color", "legend", "means")):
        items.append({"type": "animated_label", "reason": "Clarify meaning with callouts"})
        items.append({"type": "arrow", "reason": "Direct eye to the subject"})
    if any(w in text for w in ("timeline", "century", "medieval", "modern", "later", "earlier")):
        items.append({"type": "timeline", "reason": "Temporal contrast"})
    if not items and str(scene.get("purpose") or "") in {"hook", "payoff"}:
        items.append(
            {
                "type": "callout",
                "reason": f"Hook/payoff title — emotion={cinematic.get('emotion') or 'focus'}",
            }
        )
    for row in items:
        if row["type"] not in MOTION_GRAPHICS_TYPES:
            row["type"] = "callout"
        row["story_role"] = "explain_not_decorate"
        row["forbid_floating_icon"] = True
    return {
        "enabled": bool(items),
        "items": items,
        "animate_into_scene": True,
        "integrated_not_powerpoint": True,
    }


def plan_ui_overlay(scene: dict[str, Any]) -> dict[str, Any]:
    return {
        "enabled": str(scene.get("purpose") or "") in {"hook", "payoff", "cta"},
        "animations": ["caption_pop", "lower_third_slide"]
        if str(scene.get("purpose") or "") != "cta"
        else ["follow_prompt_pulse"],
    }


def scene_must_move_checklist(layers: dict[str, Any]) -> list[str]:
    """Return which MOTION_CLASSES are active for the fail-if-nothing-moves gate."""
    active: list[str] = []
    if layers.get("camera"):
        active.append("camera_movement")
    if (layers.get("character") or {}).get("enabled"):
        active.append("character_animation")
    if (layers.get("object") or {}).get("enabled"):
        active.append("object_movement")
    if (layers.get("world") or {}).get("enabled"):
        active.append("environmental_movement")
    fx = layers.get("fx") or {}
    if fx.get("particle_effects"):
        active.append("particle_effects")
    if fx.get("lighting_movement"):
        active.append("lighting_movement")
    if fx.get("physics_animation"):
        active.append("physics_animation")
    if (layers.get("ui") or {}).get("enabled"):
        active.append("ui_animation")
    if (layers.get("motion_graphics") or {}).get("enabled"):
        active.append("motion_graphics")
    return active


def enrich_scene_layers(
    scene: dict[str, Any],
    *,
    candidate: dict[str, Any],
    topic: str,
    camera: dict[str, Any] | None = None,
    transition: dict[str, Any] | None = None,
    cinematic: dict[str, Any] | None = None,
) -> dict[str, Any]:
    # Intent first — camera/layers remix around story, not the reverse
    world_env = detect_world_type(candidate, scene, topic=topic)
    cine = cinematic or plan_cinematic_intent(scene, world_env=world_env, topic=topic)

    # If caller didn't pass a motivated camera yet, create one from cinematic intent
    if not camera:
        from services.animation_engine.camera import choose_camera

        camera = choose_camera(scene, cinematic=cine)
    if not transition:
        from services.animation_engine.camera import choose_transition

        transition = choose_transition(None, scene, index=0, nxt_cinematic=cine)

    world = plan_world_layer(candidate, scene, topic=topic, cinematic=cine)
    character = plan_character_layer(scene, topic=topic, cinematic=cine)
    obj = plan_object_layer(scene, topic=topic)
    fx = plan_particles_and_light(scene, world)
    mg = plan_motion_graphics(scene, cinematic=cine)
    ui = plan_ui_overlay(scene)
    layers = {
        "cinematic": cine,
        "camera": camera,
        "character": character,
        "world": world,
        "object": obj,
        "fx": fx,
        "motion_graphics": mg,
        "ui": ui,
        "transition_in": transition,
        "muted_comprehension": muted_comprehension_beat(scene),
        "visual_moment": cine.get("visual_moment"),
        "audience_understanding": cine.get("audience_understanding"),
    }
    active = scene_must_move_checklist(layers)
    if "camera_movement" not in active:
        active.append("camera_movement")
    if "environmental_movement" not in active:
        active.append("environmental_movement")
        layers["world"]["enabled"] = True
    # Lighting always counts toward life
    if "lighting_movement" not in active and fx.get("lighting_movement"):
        active.append("lighting_movement")
    layers["active_motion_classes"] = active
    layers["passes_motion_minimum"] = len(active) >= 1
    layers["immersion"] = immersion_checklist(layers)
    layers["quality_rejects"] = list(cine.get("forbid") or [])
    return layers
