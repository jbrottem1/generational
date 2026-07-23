"""Build / attach Animation Engine packages (V2 cinematic evolution)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.animation_engine.camera import choose_camera, choose_transition
from services.animation_engine.cinematic import plan_cinematic_intent
from services.animation_engine.intent import detect_world_type
from services.animation_engine.layers import enrich_scene_layers
from services.animation_engine.models import (
    PACKAGE_TYPE,
    PACKAGE_VERSION,
    TARGET_SCENE_SEC_HIGH,
    TARGET_SCENE_SEC_LOW,
)
from services.animation_engine.score import animation_excellence, quality_gate, score_scene

ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = ROOT / "data" / "animation_engine" / "packages"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _scenes(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    vp = candidate.get("visual_package") if isinstance(candidate.get("visual_package"), dict) else {}
    scenes = list(vp.get("scenes") or candidate.get("scenes") or [])
    if scenes:
        return [dict(s) for s in scenes if isinstance(s, dict)]
    handoff = candidate.get("animation_handoff") if isinstance(candidate.get("animation_handoff"), dict) else {}
    for s in handoff.get("scenes") or []:
        if isinstance(s, dict):
            scenes.append(dict(s))
    return scenes


def _duration(scene: dict[str, Any]) -> float:
    d = float(scene.get("length_sec") or scene.get("duration_sec") or 0)
    if d <= 0:
        d = 3.0
    return d


def build_animation_package(
    candidate: dict[str, Any] | None = None,
    *,
    topic: str = "",
    production_id: str = "",
    write: bool = True,
    out_path: str | Path | None = None,
) -> dict[str, Any]:
    """Plan per-scene cinematic motion — story-first, immersion-tested."""
    candidate = dict(candidate or {})
    topic = topic or str(candidate.get("topic") or candidate.get("title") or "")
    scenes = _scenes(candidate)

    used_cameras: set[str] = set()
    decisions: list[dict[str, Any]] = []
    updated: list[dict[str, Any]] = []
    prev: dict[str, Any] | None = None
    prev_cine: dict[str, Any] | None = None

    for i, scene in enumerate(scenes):
        dur = _duration(scene)
        world_env = detect_world_type(candidate, scene, topic=topic)
        cine = plan_cinematic_intent(scene, world_env=world_env, topic=topic)
        # Honor Virtual Film Director + Cinematic Direction Studio seeds
        vfd_seed = scene.get("vfd_seed") if isinstance(scene.get("vfd_seed"), dict) else {}
        cds = scene.get("director_package") if isinstance(scene.get("director_package"), dict) else {}
        cds_seed = (cds.get("animation_seed") or {}) if cds else {}
        if scene.get("director_emotion") or cds_seed.get("emotion") or vfd_seed.get("emotion"):
            cine["emotion"] = (
                scene.get("director_emotion")
                or cds_seed.get("emotion")
                or vfd_seed.get("emotion")
                or cine.get("emotion")
            )
        if scene.get("lighting_mood") or cds_seed.get("lighting_mood") or vfd_seed.get("lighting_mood"):
            cine["lighting_mood"] = (
                scene.get("lighting_mood")
                or cds_seed.get("lighting_mood")
                or vfd_seed.get("lighting_mood")
                or cine.get("lighting_mood")
            )
        if scene.get("shot_size") or cds_seed.get("shot_size") or vfd_seed.get("shot_size"):
            cine["shot_size"] = (
                scene.get("shot_size")
                or cds_seed.get("shot_size")
                or vfd_seed.get("shot_size")
                or cine.get("shot_size")
            )
        if scene.get("scene_objective") or cds.get("story_objective"):
            cine["visual_moment"] = (
                scene.get("cinematic_payoff")
                or scene.get("scene_objective")
                or cds.get("story_objective")
            )
            cine["audience_understanding"] = scene.get("scene_objective") or cds.get(
                "emotional_objective"
            )
        if scene.get("shot_language") or cds.get("shot_type"):
            cine["shot_language"] = scene.get("shot_language") or cds.get("shot_type")
            cine["directed_by_vfd"] = True
            cine["directed_by_cinematic_direction_studio"] = bool(cds)
        camera = choose_camera(scene, scene_index=i, used=used_cameras, cinematic=cine)
        used_cameras.add(str(camera["camera_move"]))
        transition = choose_transition(
            prev, scene, index=i, prev_cinematic=prev_cine, nxt_cinematic=cine
        )
        # Prefer VFD transition language when present
        if scene.get("transition_style"):
            transition = {
                **transition,
                "transition": scene.get("transition_style"),
                "reason": f"VFD directed transition={scene.get('transition_style')}",
                "motivated": True,
                "source": "virtual_film_director",
            }
        layers = enrich_scene_layers(
            scene,
            candidate=candidate,
            topic=topic,
            camera=camera,
            transition=transition,
            cinematic=cine,
        )
        decision = {
            "scene_number": scene.get("scene_number") or i + 1,
            "scene_id": scene.get("scene_id") or scene.get("id") or f"scene_{i:02d}",
            "duration_sec": dur,
            "pacing_note": (
                "within_2_4s"
                if TARGET_SCENE_SEC_LOW <= dur <= TARGET_SCENE_SEC_HIGH
                else ("long_beat_requires_multiphase_motion" if dur > TARGET_SCENE_SEC_HIGH else "short_punch")
            ),
            "cinematic": cine,
            "vfd_seed": vfd_seed or None,
            "shot_language": scene.get("shot_language"),
            "layers": layers,
            "motion_effect": camera.get("motion_effect"),
            "true_motion_camera": camera.get("true_motion_camera"),
            "true_motion_performance": (layers.get("character") or {}).get("performance"),
            "world_palette": (layers.get("world") or {}).get("palette_hint"),
            "lighting_mood": (layers.get("world") or {}).get("lighting_mood") or cine.get("lighting_mood"),
            "emotion": cine.get("emotion"),
            "shot_size": cine.get("shot_size"),
            "immersion": layers.get("immersion"),
        }
        decision["excellence"] = score_scene(decision)
        decisions.append(decision)

        applied = dict(scene)
        applied["camera_motion"] = camera["camera_move"].replace("_", " ")
        applied["animation_camera"] = camera["true_motion_camera"]
        applied["animation_effect"] = camera["motion_effect"]
        applied["effect"] = {
            "effect": camera["motion_effect"],
            "zoom": {"start": 1.0, "end": 1.12 if camera.get("speed") != "glacial" else 1.06},
            "pan": {"x": 0.0, "y": 0.0},
            "intensity": {"energized": 82, "pressing": 78, "glacial": 55, "gentle": 60, "slow": 58, "resolved": 70, "measured": 72}.get(
                str(camera.get("speed") or "measured"), 72
            ),
            "easing": "ease_in_out",
            "source": "animation_engine_v2",
            "narrative_purpose": camera.get("narrative_purpose"),
            "emotion": cine.get("emotion"),
        }
        applied["ken_burns"] = False
        applied["forbid_static"] = True
        applied["max_still_sec"] = 2.0
        applied["transition_out"] = transition["transition"]
        applied["animation_layers"] = layers
        applied["cinematic_intent"] = cine
        # Prefer Character Performance Engine actor path over camera-only defaults
        cpe = scene.get("character_performance_package") if isinstance(
            scene.get("character_performance_package"), dict
        ) else {}
        cpe_tm = (cpe.get("true_motion") or {}) if cpe else {}
        if scene.get("true_motion") and isinstance(scene.get("true_motion"), dict):
            # Scene may already carry CPE true_motion fields from CWS
            cpe_tm = {**cpe_tm, **{k: v for k, v in scene["true_motion"].items() if v is not None}}
        cam_token = (
            cpe_tm.get("camera")
            or (scene.get("camera_follow") or {}).get("true_motion_camera")
            or camera["true_motion_camera"]
        )
        perf_token = (
            cpe_tm.get("performance")
            or scene.get("studio_performance")
            or (layers.get("character") or {}).get("performance")
            or "walk_explain"
        )
        applied["true_motion"] = {
            "camera": cam_token,
            "performance": perf_token,
            "palette": (
                scene.get("palette_hint")
                or (layers.get("world") or {}).get("palette_hint")
                or "ireland"
            ),
            "lighting_mood": (layers.get("world") or {}).get("lighting_mood") or cine.get("lighting_mood"),
            "shot_size": cine.get("shot_size"),
            "emotion": cine.get("emotion"),
            "depth_layers": (layers.get("world") or {}).get("depth_layers"),
            "character_plate_path": scene.get("character_plate_path")
            or (layers.get("character") or {}).get("character_plate_path"),
            "studio_character_id": scene.get("studio_character_id"),
            "living_background": True,
            "cinematic_v2": True,
            "not_ken_burns_only": True,
            "forbid_abstract_geometry": True,
            "forbid_placeholder_characters": True,
            "actor_driven": bool(cpe_tm.get("actor_driven") or cpe),
            "performance_path": cpe_tm.get("performance_path")
            or (scene.get("performance_simulation") and {
                "keyframes": (scene.get("performance_simulation") or {}).get("keyframes"),
                "actor_driven": True,
                "performance": perf_token,
            }),
            "character_performance_engine": bool(cpe),
            "camera_follow_mode": cpe_tm.get("camera_follow_mode")
            or (scene.get("camera_follow") or {}).get("mode"),
        }
        if cpe:
            applied["character_performance_package"] = cpe
            applied["character_blocking"] = scene.get("character_blocking") or cpe.get("blocking")
        applied["environment_fx"] = (layers.get("world") or {}).get("animations") or []
        applied["motion_graphics_plan"] = (layers.get("motion_graphics") or {}).get("items") or []
        applied["immersion"] = layers.get("immersion")
        updated.append(applied)
        prev = scene
        prev_cine = cine

    excellence = animation_excellence(decisions)
    gate = quality_gate(decisions)

    true_motion_plan = []
    for d in decisions:
        true_motion_plan.append(
            {
                "scene_number": d["scene_number"],
                "camera": d.get("true_motion_camera"),
                "performance": d.get("true_motion_performance"),
                "palette": d.get("world_palette"),
                "lighting_mood": d.get("lighting_mood"),
                "emotion": d.get("emotion"),
                "shot_size": d.get("shot_size"),
                "duration_sec": d.get("duration_sec"),
                "cinematic_v2": True,
                "not_ken_burns_only": True,
            }
        )

    package: dict[str, Any] = {
        "package_type": PACKAGE_TYPE,
        "package_version": PACKAGE_VERSION,
        "engine_label": "Cinematic Animation Engine V2",
        "generated_at": _now(),
        "topic": topic,
        "production_id": production_id,
        "scene_count": len(updated),
        "scene_decisions": decisions,
        "scenes": updated,
        "true_motion_plan": true_motion_plan,
        "animation_excellence": excellence,
        "quality_gate": gate,
        "philosophy": {
            "objective": "cinematic_educational_short_films",
            "not": ["more_animation_for_its_own_sake", "powerpoint_motion", "purposeless_drift"],
            "every_frame_intentional": True,
            "muted_story_test": True,
            "immersion_test": True,
        },
        "standards": {
            "every_scene_must_move": True,
            "every_move_must_have_purpose": True,
            "max_still_without_motion_sec": 2.0,
            "target_scene_duration_sec": [TARGET_SCENE_SEC_LOW, TARGET_SCENE_SEC_HIGH],
            "no_crossfade_default": True,
            "no_frozen_backgrounds": True,
            "no_abstract_geometry_worlds": True,
            "no_mannequin_characters": True,
            "re_render_immersion_failures": True,
        },
        "summary": {
            "animation_excellence_score": excellence.get("animation_excellence_score"),
            "quality_gate": gate.get("decision"),
            "unique_cameras": len({d["layers"]["camera"]["camera_move"] for d in decisions if d.get("layers")}),
            "character_scenes": sum(1 for d in decisions if (d.get("layers") or {}).get("character")),
            "motion_graphics_scenes": sum(
                1 for d in decisions if ((d.get("layers") or {}).get("motion_graphics") or {}).get("enabled")
            ),
            "immersion_pass_ratio": (gate.get("metrics") or {}).get("immersion_pass_ratio"),
            "re_render_scenes": gate.get("re_render_scenes") or [],
            "emotions": sorted({str(d.get("emotion")) for d in decisions if d.get("emotion")}),
        },
    }

    if candidate.get("animation_handoff"):
        package["upstream_cinematography_handoff"] = {
            "provider": (candidate.get("animation_handoff") or {}).get("provider"),
            "scene_count": len((candidate.get("animation_handoff") or {}).get("scenes") or []),
        }
    if candidate.get("VIRTUAL_FILM_DIRECTOR_PACKAGE") or candidate.get("SHOT_PLAN"):
        package["upstream_virtual_film_director"] = {
            "present": True,
            "path": (candidate.get("virtual_film_director") or {}).get("path")
            or (candidate.get("VIRTUAL_FILM_DIRECTOR_PACKAGE") or {}).get("path"),
            "director_decision": (candidate.get("virtual_film_director") or {}).get("director_decision")
            or ((candidate.get("VIRTUAL_FILM_DIRECTOR_PACKAGE") or {}).get("director_review") or {}).get("decision"),
            "honored_seeds": sum(1 for d in decisions if d.get("vfd_seed") or d.get("shot_language")),
        }

    if write:
        OUT_ROOT.mkdir(parents=True, exist_ok=True)
        if out_path:
            path = Path(out_path)
        else:
            slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in topic)[:48] or "topic"
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            path = OUT_ROOT / f"{slug}_{stamp}_ANIMATION_PACKAGE.json"
        if path.is_dir():
            path = path / "ANIMATION_PACKAGE.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(package, indent=2, default=str) + "\n", encoding="utf-8")
        package["path"] = str(path)
        md = _markdown_report(package)
        md_path = path.with_suffix(".md")
        md_path.write_text(md, encoding="utf-8")
        package["report_markdown_path"] = str(md_path)

    return package


def attach_animation_package(candidate: dict[str, Any], package: dict[str, Any]) -> dict[str, Any]:
    """Soft-attach — enrich scenes / motion for MotionPlanner + true_motion + assembler."""
    out = dict(candidate)
    out["animation_engine"] = {
        "path": package.get("path"),
        "version": package.get("package_version"),
        "engine_label": package.get("engine_label") or "Cinematic Animation Engine V2",
        "animation_excellence_score": (package.get("animation_excellence") or {}).get(
            "animation_excellence_score"
        ),
        "quality_gate": package.get("quality_gate"),
        "summary": package.get("summary"),
    }
    out["ANIMATION_PACKAGE"] = package
    out["animation_excellence_score"] = (package.get("animation_excellence") or {}).get(
        "animation_excellence_score"
    )
    out["true_motion_plan"] = package.get("true_motion_plan")

    vp = dict(out.get("visual_package") or {})
    scenes = list(package.get("scenes") or [])
    if scenes:
        vp["scenes"] = scenes
        out["visual_package"] = vp
        if out.get("scenes"):
            out["scenes"] = scenes

    handoff = dict(out.get("animation_handoff") or {})
    handoff_scenes = []
    for s in scenes:
        handoff_scenes.append(
            {
                "scene_number": s.get("scene_number"),
                "camera": s.get("animation_camera") or (s.get("true_motion") or {}).get("camera"),
                "effect": (s.get("effect") or {}).get("effect") or s.get("animation_effect"),
                "easing": "ease_in_out",
                "camera_motion": s.get("camera_motion"),
                "true_motion": s.get("true_motion"),
                "cinematic_intent": s.get("cinematic_intent"),
                "emotion": (s.get("cinematic_intent") or {}).get("emotion"),
                "lighting_mood": (s.get("true_motion") or {}).get("lighting_mood"),
            }
        )
    if handoff_scenes:
        handoff["scenes"] = handoff_scenes
        handoff["provider"] = handoff.get("provider") or "Cinematic Animation Engine V2"
        handoff["animation_engine_v1"] = True  # backward-compatible flag
        handoff["animation_engine_v2"] = True
        out["animation_handoff"] = handoff

    out["prefer_true_motion"] = True
    out["forbid_ken_burns_default"] = True
    out["cinematic_animation_v2"] = True
    out["animation_quality_gate"] = package.get("quality_gate")
    return out


def _markdown_report(package: dict[str, Any]) -> str:
    ex = package.get("animation_excellence") or {}
    gate = package.get("quality_gate") or {}
    dims = ex.get("dimensions") or {}
    lines = [
        "# Cinematic Animation Engine V2 — Report",
        "",
        f"**Topic:** {package.get('topic')}",
        f"**Excellence score:** {ex.get('animation_excellence_score')}",
        f"**Quality gate:** {gate.get('decision')} ({'pass' if gate.get('passed') else 'fail'})",
        f"**Package version:** {package.get('package_version')}",
        "",
        "## Philosophy",
        "",
        "- Every frame intentional",
        "- Movement must advance story or emotion",
        "- Worlds stay alive without narration",
        "- Immersion failures trigger scene re-render targets",
        "",
        "## Dimensions",
        "",
    ]
    for k, v in dims.items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Gate metrics", ""]
    for k, v in (gate.get("metrics") or {}).items():
        lines.append(f"- {k}: {v}")
    if gate.get("re_render_scenes"):
        lines += ["", "## Re-render scenes", ""]
        for s in gate["re_render_scenes"]:
            lines.append(f"- scene {s}")
    if gate.get("failures"):
        lines += ["", "## Failures", ""]
        for f in gate["failures"]:
            lines.append(f"- {f}")
    if gate.get("warnings"):
        lines += ["", "## Warnings", ""]
        for w in gate["warnings"]:
            lines.append(f"- {w}")
    lines += ["", "_Quality evolution of Animation Engine V1 — does not replace the renderer._", ""]
    return "\n".join(lines)
