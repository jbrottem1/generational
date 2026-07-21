"""Build / attach Virtual Film Director package — directs before Animation executes."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.virtual_film_director.models import PACKAGE_TYPE, PACKAGE_VERSION
from services.virtual_film_director.review import review_shot_plan, rewrite_shot_plan
from services.virtual_film_director.shots import plan_shot

ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = ROOT / "data" / "virtual_film_director" / "packages"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _scenes(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    vp = candidate.get("visual_package") if isinstance(candidate.get("visual_package"), dict) else {}
    scenes = list(vp.get("scenes") or candidate.get("scenes") or [])
    if scenes:
        return [dict(s) for s in scenes if isinstance(s, dict)]
    # Fallback from cinematic direction package
    cdp = candidate.get("cinematic_direction_package") if isinstance(
        candidate.get("cinematic_direction_package"), dict
    ) else {}
    for s in cdp.get("shot_list") or []:
        if isinstance(s, dict):
            scenes.append(dict(s))
    return scenes


def build_shot_plan(
    candidate: dict[str, Any] | None = None,
    *,
    topic: str = "",
) -> list[dict[str, Any]]:
    candidate = dict(candidate or {})
    topic = topic or str(candidate.get("topic") or candidate.get("title") or "")
    scenes = _scenes(candidate)
    used: set[str] = set()
    shots: list[dict[str, Any]] = []
    prev: dict[str, Any] | None = None
    total = len(scenes) or 1
    for i, scene in enumerate(scenes):
        shot = plan_shot(
            scene,
            candidate=candidate,
            topic=topic,
            index=i,
            total=total,
            used_shots=used,
            prev_shot=prev,
        )
        used.add(str(shot.get("shot_language") or ""))
        shots.append(shot)
        prev = shot
    return shots


def build_emotional_timeline(shots: list[dict[str, Any]]) -> dict[str, Any]:
    t = 0.0
    beats = []
    for s in shots:
        dur = float(s.get("estimated_duration_sec") or 3.0)
        beats.append(
            {
                "scene_number": s.get("scene_number"),
                "start_sec": round(t, 2),
                "end_sec": round(t + dur, 2),
                "emotional_beat": s.get("emotional_beat"),
                "emotion": s.get("emotion"),
                "lighting_mood": s.get("lighting_mood"),
                "shot_language": s.get("shot_language"),
            }
        )
        t += dur
    return {
        "total_duration_sec": round(t, 2),
        "beats": beats,
        "rhythm": [b.get("emotional_beat") for b in beats],
        "avoids_flatness": len({b.get("emotional_beat") for b in beats}) >= min(2, len(beats)),
    }


def _markdown_director_notes(package: dict[str, Any]) -> str:
    review = package.get("director_review") or {}
    lines = [
        "# Director Notes — Virtual Film Director",
        "",
        f"**Topic:** {package.get('topic')}",
        f"**Decision:** {review.get('decision')}",
        f"**Generated:** {package.get('generated_at')}",
        "",
        "## Creative brief",
        "",
        "The Animation Engine executes. The Virtual Film Director decides.",
        "Every camera move must answer: what story is this movement telling?",
        "",
        "## Review questions",
        "",
    ]
    for k, v in (review.get("questions") or {}).items():
        lines.append(f"- {k}: {'YES' if v else 'NO'}")
    if review.get("failures"):
        lines += ["", "## Failures (rewrite before animate)", ""]
        for f in review["failures"]:
            lines.append(f"- {f}")
    if review.get("warnings"):
        lines += ["", "## Warnings", ""]
        for w in review["warnings"]:
            lines.append(f"- {w}")
    lines += ["", "## Scene direction", ""]
    for s in package.get("shot_plan") or []:
        lines.append(
            f"### Scene {s.get('scene_number')} — `{s.get('shot_language')}`"
        )
        lines.append(f"- Objective: {s.get('scene_objective')}")
        lines.append(f"- Emotion / beat: {s.get('emotion')} / {s.get('emotional_beat')}")
        lines.append(f"- Lighting: {s.get('lighting_mood')}")
        lines.append(f"- Payoff: {s.get('cinematic_payoff')}")
        lines.append(f"- Transition: {s.get('transition_style')}")
        lines.append("")
    lines.append("_Direction layer only — no new renderer._")
    lines.append("")
    return "\n".join(lines)


def _markdown_camera_script(package: dict[str, Any]) -> str:
    lines = [
        "# Camera Script — Virtual Film Director",
        "",
        f"**Topic:** {package.get('topic')}",
        "",
        "| Scene | Shot | Angle | Lens | Begin → End | Transition |",
        "|---:|---|---|---|---|---|",
    ]
    for s in package.get("shot_plan") or []:
        lines.append(
            f"| {s.get('scene_number')} | `{s.get('shot_language')}` | {s.get('camera_angle')} | "
            f"{s.get('lens_style')} | {s.get('camera_begin')} → {s.get('camera_end')} | "
            f"{s.get('transition_style')} |"
        )
    lines += ["", "## Motivation", ""]
    for s in package.get("shot_plan") or []:
        seed = s.get("animation_seed") or {}
        lines.append(
            f"- Scene {s.get('scene_number')}: {seed.get('narrative_purpose') or s.get('scene_objective')}"
        )
    lines.append("")
    return "\n".join(lines)


def _markdown_storyboard(package: dict[str, Any]) -> str:
    lines = [
        "# Visual Storyboard — Virtual Film Director",
        "",
        f"**Topic:** {package.get('topic')}",
        "",
        "Muted-viewer test: each panel must teach without audio.",
        "",
    ]
    for s in package.get("shot_plan") or []:
        lines += [
            f"## Panel {s.get('scene_number')}",
            "",
            f"- **Notice first:** {s.get('notice_first')}",
            f"- **Shot:** {s.get('shot_language')} ({s.get('shot_size')})",
            f"- **Subject:** {s.get('primary_subject')}",
            f"- **World:** {(s.get('environmental_motion') or {}).get('environment')} — "
            f"{', '.join((s.get('environmental_motion') or {}).get('ambient_motion') or [])}",
            f"- **Character:** "
            + (
                "active performance"
                if (s.get("character_blocking") or {}).get("enabled")
                else "environment / concept led"
            ),
            f"- **Muted payoff:** {s.get('muted_story_test')}",
            f"- **Composition:** rule-of-thirds={'yes' if (s.get('composition') or {}).get('rule_of_thirds') else 'no'}; "
            f"FG/MG/BG={'yes' if (s.get('composition') or {}).get('fg_mg_bg') else 'no'}",
            "",
        ]
    return "\n".join(lines)


def build_virtual_film_director_package(
    candidate: dict[str, Any] | None = None,
    *,
    topic: str = "",
    production_id: str = "",
    write: bool = True,
    out_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Produce mandatory direction artifacts before Animation Engine runs."""
    candidate = dict(candidate or {})
    topic = topic or str(candidate.get("topic") or candidate.get("title") or "")
    shots = build_shot_plan(candidate, topic=topic)
    review = review_shot_plan(shots)
    if not review.get("approved"):
        shots = rewrite_shot_plan(shots, review)
        review = review_shot_plan(shots)
        review["rewritten"] = True
    else:
        review["rewritten"] = False

    timeline = build_emotional_timeline(shots)
    package: dict[str, Any] = {
        "package_type": PACKAGE_TYPE,
        "package_version": PACKAGE_VERSION,
        "engine_label": "Virtual Film Director",
        "generated_at": _now(),
        "topic": topic,
        "production_id": production_id,
        "shot_plan": shots,
        "emotional_timeline": timeline,
        "director_review": review,
        "philosophy": {
            "directs_before_animates": True,
            "animation_executes": True,
            "no_new_renderer": True,
            "no_pipeline_redesign": True,
            "muted_story_test": True,
        },
        "summary": {
            "shot_count": len(shots),
            "director_decision": review.get("decision"),
            "approved": review.get("approved"),
            "emotional_rhythm": timeline.get("rhythm"),
            "rewrite_scenes": review.get("rewrite_scenes") or [],
        },
    }

    # Compose upstream cinematic director if present
    if candidate.get("cinematic_direction_package"):
        package["upstream_cinematic_director"] = {
            "present": True,
            "version": (candidate.get("cinematic_direction_package") or {}).get("package_version"),
        }

    if write:
        if out_dir:
            base = Path(out_dir)
        else:
            OUT_ROOT.mkdir(parents=True, exist_ok=True)
            slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in topic)[:48] or "topic"
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            base = OUT_ROOT / f"{slug}_{stamp}"
        base.mkdir(parents=True, exist_ok=True)

        shot_path = base / "SHOT_PLAN.json"
        shot_path.write_text(json.dumps({"shot_plan": shots, "summary": package["summary"]}, indent=2, default=str) + "\n")
        notes_path = base / "DIRECTOR_NOTES.md"
        notes_path.write_text(_markdown_director_notes(package), encoding="utf-8")
        cam_path = base / "CAMERA_SCRIPT.md"
        cam_path.write_text(_markdown_camera_script(package), encoding="utf-8")
        emo_path = base / "EMOTIONAL_TIMELINE.json"
        emo_path.write_text(json.dumps(timeline, indent=2, default=str) + "\n", encoding="utf-8")
        board_path = base / "VISUAL_STORYBOARD.md"
        board_path.write_text(_markdown_storyboard(package), encoding="utf-8")
        pkg_path = base / "VIRTUAL_FILM_DIRECTOR_PACKAGE.json"
        package["artifacts"] = {
            "SHOT_PLAN.json": str(shot_path),
            "DIRECTOR_NOTES.md": str(notes_path),
            "CAMERA_SCRIPT.md": str(cam_path),
            "EMOTIONAL_TIMELINE.json": str(emo_path),
            "VISUAL_STORYBOARD.md": str(board_path),
            "VIRTUAL_FILM_DIRECTOR_PACKAGE.json": str(pkg_path),
        }
        package["path"] = str(pkg_path)
        package["out_dir"] = str(base)
        pkg_path.write_text(json.dumps(package, indent=2, default=str) + "\n", encoding="utf-8")

    return package


def attach_virtual_film_director(
    candidate: dict[str, Any],
    package: dict[str, Any],
) -> dict[str, Any]:
    """Soft-attach — stamp directed fields onto scenes for Animation Engine."""
    out = dict(candidate)
    out["virtual_film_director"] = {
        "path": package.get("path"),
        "out_dir": package.get("out_dir"),
        "version": package.get("package_version"),
        "director_decision": (package.get("director_review") or {}).get("decision"),
        "summary": package.get("summary"),
        "artifacts": package.get("artifacts"),
    }
    out["VIRTUAL_FILM_DIRECTOR_PACKAGE"] = package
    out["SHOT_PLAN"] = package.get("shot_plan")
    out["EMOTIONAL_TIMELINE"] = package.get("emotional_timeline")

    shots = list(package.get("shot_plan") or [])
    by_num = {int(s.get("scene_number") or i + 1): s for i, s in enumerate(shots)}

    vp = dict(out.get("visual_package") or {})
    scenes = list(vp.get("scenes") or out.get("scenes") or [])
    enriched = []
    for i, scene in enumerate(scenes):
        row = dict(scene)
        num = int(row.get("scene_number") or i + 1)
        shot = by_num.get(num) or (shots[i] if i < len(shots) else {})
        seed = shot.get("animation_seed") or {}
        row["vfd_shot"] = shot
        row["shot_language"] = shot.get("shot_language")
        row["director_emotion"] = shot.get("emotion")
        row["emotional_beat"] = shot.get("emotional_beat")
        row["lighting_mood"] = shot.get("lighting_mood")
        row["shot_size"] = shot.get("shot_size") or seed.get("shot_size")
        row["camera_angle"] = shot.get("camera_angle")
        row["lens_style"] = shot.get("lens_style")
        row["transition_style"] = shot.get("transition_style")
        row["scene_objective"] = shot.get("scene_objective")
        row["cinematic_payoff"] = shot.get("cinematic_payoff")
        row["animation_priority"] = shot.get("animation_priority")
        row["vfd_seed"] = seed
        # Prefer directed tokens without fighting later animation stamp
        if seed.get("true_motion_camera"):
            row["animation_camera"] = seed["true_motion_camera"]
        if seed.get("ae_camera_move"):
            row["vfd_camera_move"] = seed["ae_camera_move"]
        if seed.get("narrative_purpose"):
            row["camera_narrative_purpose"] = seed["narrative_purpose"]
        # Intentionally set purpose-adjacent cinematic fields Animation V2 already reads
        if shot.get("emotion"):
            row["emotion"] = shot["emotion"]
        enriched.append(row)
    if enriched:
        vp["scenes"] = enriched
        out["visual_package"] = vp
        if out.get("scenes"):
            out["scenes"] = enriched

    # Refresh animation_handoff seed (Animation Engine may rebuild, but studio_render benefits)
    handoff = dict(out.get("animation_handoff") or {})
    handoff_scenes = []
    for s in shots:
        seed = s.get("animation_seed") or {}
        handoff_scenes.append(
            {
                "scene_number": s.get("scene_number"),
                "scene_id": s.get("scene_id"),
                "camera": seed.get("true_motion_camera"),
                "effect": None,
                "shot_language": s.get("shot_language"),
                "emotion": s.get("emotion"),
                "lighting_mood": s.get("lighting_mood"),
                "transition": s.get("transition_style"),
                "narrative_purpose": seed.get("narrative_purpose"),
                "source": "virtual_film_director",
            }
        )
    if handoff_scenes:
        handoff["vfd_scenes"] = handoff_scenes
        handoff["virtual_film_director"] = True
        out["animation_handoff"] = handoff

    out["directed_by_vfd"] = True
    out["prefer_vfd_shot_plan"] = True
    return out


def direct_candidate(
    candidate: dict[str, Any],
    *,
    topic: str = "",
    production_id: str = "",
    write: bool = True,
    out_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Façade: build package + soft-attach. Safe to call from cinematography engine."""
    pkg = build_virtual_film_director_package(
        candidate,
        topic=topic or str(candidate.get("topic") or candidate.get("title") or ""),
        production_id=production_id,
        write=write,
        out_dir=out_dir,
    )
    out = attach_virtual_film_director(candidate, pkg)
    # Cinematic Direction Studio — DIRECTOR_PACKAGE objectives + actor beats
    try:
        from services.cinematic_direction_studio import (
            attach_cinematic_direction_to_candidate,
        )

        out = attach_cinematic_direction_to_candidate(
            out,
            topic=topic or str(out.get("topic") or out.get("title") or ""),
            location=out.get("studio_location"),
            write=write,
        )
    except Exception:  # noqa: BLE001
        pass
    return out
