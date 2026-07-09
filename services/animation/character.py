"""Character motion, body animation, facial system, and scene choreography.

Plans HOW characters move — walking, talking, gestures, blocking, multi-
character coordination — without generating pixels. Consumes Creative Studio
character_plan / storyboard cast lists and optional IP engine character refs.
"""

from __future__ import annotations

from services.animation.config import AnimationConfig
from services.animation.models import CharacterAction, FacialExpression

_EMOTION_TO_EXPRESSION = (
    ("fear", FacialExpression.FEAR),
    ("afraid", FacialExpression.FEAR),
    ("surpris", FacialExpression.SURPRISE),
    ("shock", FacialExpression.SURPRISE),
    ("anger", FacialExpression.ANGER),
    ("angry", FacialExpression.ANGER),
    ("confus", FacialExpression.CONFUSION),
    ("curios", FacialExpression.CURIOSITY),
    ("wonder", FacialExpression.CURIOSITY),
    ("smile", FacialExpression.SMILE),
    ("joy", FacialExpression.SMILE),
    ("happy", FacialExpression.SMILE),
    ("warm", FacialExpression.SMILE),
)


def _cast_from_item(item: dict) -> "list[dict]":
    creative = item.get("creative_package") or {}
    character_plan = creative.get("character_plan") or {}
    cast = list(character_plan.get("cast") or [])
    if cast:
        return cast

    ip = item.get("ip_package") or item.get("character_package") or {}
    for key in ("characters", "cast", "roster"):
        entries = ip.get(key) or []
        if entries:
            return list(entries)

    # Minimal narrator fallback so every production has a performer track.
    return [{
        "character_id": "char_narrator",
        "name": "Narrator",
        "role": "narrator",
    }]


def _characters_in_scene(scene: dict, cast: "list[dict]") -> "list[dict]":
    ids = scene.get("characters") or []
    if not ids:
        return cast[:1] if cast else []
    by_id = {c.get("character_id"): c for c in cast}
    found = [by_id[cid] for cid in ids if cid in by_id]
    return found or cast[:1]


def _expression_for(emotion: str) -> str:
    lowered = (emotion or "").lower()
    for fragment, expression in _EMOTION_TO_EXPRESSION:
        if fragment in lowered:
            return expression
    return FacialExpression.NEUTRAL


def _action_for(scene: dict, has_narration: bool) -> str:
    text = " ".join(
        str(scene.get(key, ""))
        for key in ("motion_instructions", "purpose", "visual_description")
    ).lower()
    if "run" in text:
        return CharacterAction.RUNNING
    if "walk" in text or "enter" in text:
        return CharacterAction.WALKING
    if "gesture" in text or "point" in text:
        return CharacterAction.GESTURE
    if "interact" in text or "hold" in text or "pick" in text:
        return CharacterAction.OBJECT_INTERACTION
    if has_narration:
        return CharacterAction.TALKING
    return CharacterAction.IDLE


def plan_character_motion(
    scenes: "list[dict]",
    scene_timing: "list[dict]",
    item: dict,
    config: AnimationConfig,
) -> "list[dict]":
    cast = _cast_from_item(item)
    timing_by_scene = {entry["scene_id"]: entry for entry in scene_timing}
    motions: "list[dict]" = []
    for scene in scenes:
        scene_id = scene.get("scene_id", "")
        timing = timing_by_scene.get(scene_id, {})
        start = float(timing.get("start_sec", 0.0))
        end = float(timing.get("end_sec", start + 3.0))
        narration = bool(scene.get("narration") or scene.get("purpose"))
        primary_action = _action_for(scene, narration)
        performers = _characters_in_scene(scene, cast)
        group = f"coord_{scene_id}" if len(performers) > 1 else ""
        for index, character in enumerate(performers):
            cid = str(character.get("character_id", f"char_{index}"))
            actions = [
                {
                    "action": primary_action,
                    "start_sec": start,
                    "end_sec": end,
                    "intensity": config.motion_intensity,
                },
                {
                    "action": CharacterAction.BREATHING,
                    "start_sec": start,
                    "end_sec": end,
                    "intensity": "subtle",
                },
                {
                    "action": CharacterAction.BLINKING,
                    "start_sec": start,
                    "end_sec": end,
                    "intensity": "subtle",
                },
            ]
            if index == 0 and primary_action != CharacterAction.IDLE:
                actions.append({
                    "action": CharacterAction.EYE_MOVEMENT,
                    "start_sec": start,
                    "end_sec": end,
                    "intensity": "moderate",
                })
            motions.append({
                "motion_id": f"motion_{scene_id}_{cid}",
                "scene_id": scene_id,
                "character_id": cid,
                "actions": actions,
                "blocking": {
                    "slot": index,
                    "x": round(-0.8 + index * 0.8, 2),
                    "y": 0.0,
                    "z": 0.0,
                    "facing": "camera" if index == 0 else "lead",
                },
                "coordination_group": group,
            })
    return motions


def plan_body_animation(character_motion: "list[dict]") -> "list[dict]":
    bodies: "list[dict]" = []
    for motion in character_motion:
        actions = motion.get("actions", [])
        locomotion = next(
            (
                a["action"] for a in actions
                if a.get("action") in (
                    CharacterAction.WALKING, CharacterAction.RUNNING, CharacterAction.IDLE,
                    CharacterAction.TALKING,
                )
            ),
            CharacterAction.IDLE,
        )
        gestures = [a for a in actions if a.get("action") == CharacterAction.GESTURE]
        hands = [a for a in actions if a.get("action") == CharacterAction.HAND_MOVEMENT]
        interactions = [a for a in actions if a.get("action") == CharacterAction.OBJECT_INTERACTION]
        start = min((float(a.get("start_sec", 0)) for a in actions), default=0.0)
        end = max((float(a.get("end_sec", 0)) for a in actions), default=0.0)
        bodies.append({
            "body_id": f"body_{motion['motion_id']}",
            "scene_id": motion["scene_id"],
            "character_id": motion["character_id"],
            "locomotion": locomotion,
            "gestures": gestures,
            "hand_tracks": hands,
            "interactions": interactions,
            "start_sec": start,
            "end_sec": end,
        })
    return bodies


def plan_facial_animation(
    scenes: "list[dict]",
    scene_timing: "list[dict]",
    item: dict,
    config: AnimationConfig,
) -> "list[dict]":
    if not config.enable_facial:
        return []
    cast = _cast_from_item(item)
    timing_by_scene = {entry["scene_id"]: entry for entry in scene_timing}
    faces: "list[dict]" = []
    for scene in scenes:
        scene_id = scene.get("scene_id", "")
        timing = timing_by_scene.get(scene_id, {})
        start = float(timing.get("start_sec", 0.0))
        end = float(timing.get("end_sec", start + 3.0))
        expression = _expression_for(str(scene.get("emotion", "")))
        for character in _characters_in_scene(scene, cast):
            cid = str(character.get("character_id", "char_0"))
            blend = {expression: 1.0}
            if expression != FacialExpression.NEUTRAL:
                blend[FacialExpression.NEUTRAL] = 0.15
            faces.append({
                "facial_id": f"face_{scene_id}_{cid}",
                "scene_id": scene_id,
                "character_id": cid,
                "expression": expression,
                "blend": blend,
                "eye_direction": "audience" if scene.get("narration") else "subject",
                "head_movement": "subtle_nod" if scene.get("narration") else "hold",
                "start_sec": start,
                "end_sec": end,
            })
    return faces


def plan_choreography(
    scenes: "list[dict]",
    character_motion: "list[dict]",
) -> "list[dict]":
    by_scene: "dict[str, list]" = {}
    for motion in character_motion:
        by_scene.setdefault(motion["scene_id"], []).append(motion)

    choreography: "list[dict]" = []
    for scene in scenes:
        scene_id = scene.get("scene_id", "")
        motions = by_scene.get(scene_id, [])
        placements = {
            m["character_id"]: m.get("blocking", {})
            for m in motions
        }
        paths = [
            {
                "character_id": m["character_id"],
                "from": m.get("blocking", {}),
                "to": {
                    **m.get("blocking", {}),
                    "x": round(float(m.get("blocking", {}).get("x", 0)) + 0.2, 2),
                },
            }
            for m in motions
            if any(
                a.get("action") in (CharacterAction.WALKING, CharacterAction.RUNNING, CharacterAction.ENTRANCE)
                for a in m.get("actions", [])
            )
        ]
        purpose = str(scene.get("purpose", "")).lower()
        choreography.append({
            "scene_id": scene_id,
            "placements": placements,
            "paths": paths,
            "entrances": [
                m["character_id"] for m in motions
                if any(a.get("action") == CharacterAction.ENTRANCE for a in m.get("actions", []))
            ],
            "exits": [
                m["character_id"] for m in motions
                if any(a.get("action") == CharacterAction.EXIT for a in m.get("actions", []))
            ],
            "interactions": [
                {
                    "characters": [m["character_id"] for m in motions],
                    "type": "dialogue" if scene.get("narration") else "presence",
                }
            ] if len(motions) > 1 else [],
            "composition": scene.get("visual_description", "")[:160],
            "crowd_layout": "clustered" if "crowd" in purpose else "none",
        })
    return choreography
