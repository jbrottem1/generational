"""Build / attach Character & World Studio packages."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.character_world_studio.casting import (
    assign_scene_performers,
    choose_hosts,
    choose_location,
)
from services.character_world_studio.continuity import continuity_notes, remember_production
from services.character_world_studio.gate import review_studio_package
from services.character_world_studio.models import PACKAGE_TYPE, PACKAGE_VERSION, PERFORMANCE_VERBS, STYLE_IDENTITY
from services.character_world_studio.plates import draw_cast_plates

ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = ROOT / "data" / "character_world_studio" / "packages"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _scenes(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    vp = candidate.get("visual_package") if isinstance(candidate.get("visual_package"), dict) else {}
    scenes = list(vp.get("scenes") or candidate.get("scenes") or [])
    return [dict(s) for s in scenes if isinstance(s, dict)]


def build_character_world_studio_package(
    candidate: dict[str, Any] | None = None,
    *,
    topic: str = "",
    production_id: str = "",
    write: bool = True,
    out_dir: str | Path | None = None,
) -> dict[str, Any]:
    candidate = dict(candidate or {})
    topic = topic or str(candidate.get("topic") or candidate.get("title") or "")
    location = choose_location(candidate, topic=topic)
    hosts = choose_hosts(candidate, topic=topic, location=location)
    scenes = assign_scene_performers(_scenes(candidate), hosts, location=location)
    # Complete shot contracts: facial performance + environment construction
    try:
        from services.shot_assembly import attach_complete_shots

        hosts_by_id = {str(h["id"]).upper(): h for h in hosts}
        scenes = attach_complete_shots(scenes, hosts_by_id=hosts_by_id, location=location)
    except Exception:  # noqa: BLE001
        pass
    # Ensure stage world refs remain after complete-shot enrichment
    try:
        from services.stage_world_simulation import attach_world_simulation

        scenes = attach_world_simulation(scenes, location=location)
    except Exception:  # noqa: BLE001
        pass
    try:
        from services.physics_interaction import attach_physics_interactions

        hosts_by_id = {str(h["id"]).upper(): h for h in hosts}
        # Rebuild physics against latest stage refs
        for s in scenes:
            s.pop("physics_bundle", None)
        scenes = attach_physics_interactions(
            scenes, hosts_by_id=hosts_by_id, location=location
        )
    except Exception:  # noqa: BLE001
        pass
    notes = continuity_notes(hosts, location)

    if out_dir:
        base = Path(out_dir)
    else:
        slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in topic)[:48] or "topic"
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        base = OUT_ROOT / f"{slug}_{stamp}"
    plates_dir = base / "plates"
    plates: dict[str, str] = {}
    plates = draw_cast_plates(hosts, plates_dir=plates_dir, expression="smile")

    package: dict[str, Any] = {
        "package_type": PACKAGE_TYPE,
        "package_version": PACKAGE_VERSION,
        "engine_label": "Character & World Studio",
        "generated_at": _now(),
        "topic": topic,
        "production_id": production_id,
        "visual_identity": dict(STYLE_IDENTITY),
        "cast": hosts,
        "primary_host": hosts[0] if hosts else None,
        "location": location,
        "character_plates": plates,
        "scene_bindings": scenes,
        "performance_library": list(PERFORMANCE_VERBS),
        "continuity": notes,
        "world_living_requirements": {
            "continues_without_narration": True,
            "ambient_life": location.get("ambient_life"),
            "environmental_animation": location.get("environmental_animation"),
            "detail_dressing": location.get("detail_dressing"),
            "forbid_empty_sets": True,
        },
        "camera_follow_characters": True,
        "muted_storytelling": True,
        "philosophy": {
            "living_animated_universe": True,
            "no_new_renderer": True,
            "no_pipeline_redesign": True,
            "does_not_replace_animation_engine": True,
            "human_realism_framework": True,
        },
        "human_realism": {
            "framework": "HUMAN_REALISM_FRAMEWORK_V1",
            "gold_standard": "DOCTOR_001",
            "performance_plans_attached": all(
                bool(s.get("performance_plan")) for s in scenes
            )
            if scenes
            else False,
        },
        "facial_performance_standard": {
            "version": "1.0.0",
            "plans_attached": all(bool(s.get("facial_performance_plan")) for s in scenes)
            if scenes
            else False,
            "quality_rule": "Plan completeness is not proof — inspect the final MP4.",
        },
        "environment_construction_standard": {
            "version": "1.0.0",
            "packages_attached": all(bool(s.get("environment_package")) for s in scenes)
            if scenes
            else False,
            "quality_rule": "Package completeness is not proof — inspect the final MP4.",
        },
    }
    package["quality_gate"] = review_studio_package(package)
    package["summary"] = {
        "primary_host": (hosts[0] or {}).get("name") if hosts else None,
        "cast_ids": [h["id"] for h in hosts],
        "location_id": location.get("id"),
        "location_name": location.get("name"),
        "plate_count": len(plates),
        "quality_gate": package["quality_gate"].get("decision"),
        "recognize_characters": (package["quality_gate"].get("questions") or {}).get(
            "viewers_would_recognize_characters"
        ),
        "feels_like_series": (package["quality_gate"].get("questions") or {}).get("feels_like_original_series"),
    }

    if write:
        base.mkdir(parents=True, exist_ok=True)
        pkg_path = base / "CHARACTER_WORLD_STUDIO_PACKAGE.json"
        md_path = base / "STUDIO_NOTES.md"
        package["path"] = str(pkg_path)
        package["out_dir"] = str(base)
        package["artifacts"] = {
            "CHARACTER_WORLD_STUDIO_PACKAGE.json": str(pkg_path),
            "STUDIO_NOTES.md": str(md_path),
            "plates": plates,
        }
        pkg_path.write_text(json.dumps(package, indent=2, default=str) + "\n", encoding="utf-8")
        md_path.write_text(_markdown(package), encoding="utf-8")
        remember_production(topic=topic, production_id=production_id or "local", hosts=hosts, location=location)
    else:
        package["character_plates"] = plates
        package["out_dir"] = str(base)

    return package


def attach_character_world_studio(
    candidate: dict[str, Any],
    package: dict[str, Any],
) -> dict[str, Any]:
    out = dict(candidate)
    out["character_world_studio"] = {
        "path": package.get("path"),
        "out_dir": package.get("out_dir"),
        "version": package.get("package_version"),
        "summary": package.get("summary"),
        "quality_gate": package.get("quality_gate"),
        "artifacts": package.get("artifacts"),
    }
    out["CHARACTER_WORLD_STUDIO_PACKAGE"] = package
    out["studio_cast"] = package.get("cast")
    out["studio_location"] = package.get("location")
    out["character_plates"] = package.get("character_plates")
    out["primary_host"] = package.get("primary_host")
    out["generational_universe"] = True

    # Location enrich without fighting World Builder camera fields
    loc = package.get("location") or {}
    wp = dict(out.get("world_package") or {})
    wp["studio_location_id"] = loc.get("id")
    wp["studio_location_name"] = loc.get("name")
    wp["studio_ambient_life"] = loc.get("ambient_life")
    wp["studio_environmental_animation"] = loc.get("environmental_animation")
    wp["studio_detail_dressing"] = loc.get("detail_dressing")
    wp["studio_palette_hint"] = loc.get("palette_hint")
    wp["living_universe"] = True
    if not wp.get("world_type"):
        wp["world_type"] = loc.get("name")
    out["world_package"] = wp
    # Stage & World Simulation — persistent stage ref on candidate
    try:
        from services.stage_world_simulation import attach_world_to_candidate

        out = attach_world_to_candidate(out, location=loc)
    except Exception:  # noqa: BLE001
        pass

    bindings = {int(s.get("scene_number") or i + 1): s for i, s in enumerate(package.get("scene_bindings") or [])}
    plates = package.get("character_plates") or {}
    vp = dict(out.get("visual_package") or {})
    scenes = list(vp.get("scenes") or out.get("scenes") or [])
    enriched = []
    for i, scene in enumerate(scenes):
        row = dict(scene)
        num = int(row.get("scene_number") or i + 1)
        bind = bindings.get(num) or (package.get("scene_bindings") or [None])[min(i, len(package.get("scene_bindings") or []) - 1) or 0] or {}
        if isinstance(bind, dict):
            cid = bind.get("studio_character_id")
            row["studio_character_id"] = cid
            row["studio_character_name"] = bind.get("studio_character_name")
            row["studio_performance"] = bind.get("studio_performance")
            row["studio_expression"] = bind.get("studio_expression")
            row["studio_gestures"] = bind.get("studio_gestures")
            if bind.get("performance_plan"):
                row["performance_plan"] = bind.get("performance_plan")
                row["studio_emotion"] = bind.get("studio_emotion")
                row["studio_gaze_target"] = bind.get("studio_gaze_target")
                row["studio_body_language"] = bind.get("studio_body_language")
                row["studio_walking_style"] = bind.get("studio_walking_style")
                row["studio_breathing"] = bind.get("studio_breathing")
            if bind.get("facial_performance_plan"):
                row["facial_performance_plan"] = bind.get("facial_performance_plan")
            if bind.get("environment_package"):
                row["environment_package"] = bind.get("environment_package")
            if bind.get("complete_shot"):
                row["complete_shot"] = bind.get("complete_shot")
            if bind.get("character_performance_package"):
                row["character_performance_package"] = bind.get("character_performance_package")
                row["character_blocking"] = bind.get("character_blocking")
                row["actor_locomotion"] = bind.get("actor_locomotion")
                row["performance_simulation"] = bind.get("performance_simulation")
                row["camera_follow"] = bind.get("camera_follow")
                if bind.get("true_motion"):
                    row["true_motion"] = bind.get("true_motion")
            if bind.get("character_rig_ref") or bind.get("character_rig_package"):
                row["character_rig_ref"] = bind.get("character_rig_ref")
                row["character_rig_package"] = bind.get("character_rig_package")
                row["character_continuity_version"] = bind.get("character_continuity_version")
                if bind.get("studio_asset_path"):
                    row["studio_asset_path"] = bind.get("studio_asset_path")
            if bind.get("stage_world_package") or bind.get("world_package_ref"):
                row["stage_world_package"] = bind.get("stage_world_package")
                row["world_id"] = bind.get("world_id")
                row["world_package_ref"] = bind.get("world_package_ref")
            if bind.get("physics_bundle") or bind.get("interaction_packages"):
                row["physics_bundle"] = bind.get("physics_bundle")
                row["physics_profile"] = bind.get("physics_profile")
                row["interaction_packages"] = bind.get("interaction_packages")
                row["physics_constraints"] = bind.get("physics_constraints")
            if bind.get("director_package"):
                row["director_package"] = bind.get("director_package")
                row["actor_direction"] = bind.get("actor_direction")
                row["director_shot_type"] = bind.get("director_shot_type")
                row["director_emotion"] = bind.get("director_emotion")
            if cid and plates.get(cid):
                row["character_plate_path"] = plates[cid]
                row["approved_character_path"] = plates[cid]
            row["studio_location_id"] = loc.get("id")
            row["environment_life"] = loc.get("environmental_animation")
            row["environment_details"] = loc.get("detail_dressing")
            if loc.get("palette_hint"):
                row["palette_hint"] = loc.get("palette_hint")
        enriched.append(row)
    if enriched:
        vp["scenes"] = enriched
        out["visual_package"] = vp
        if out.get("scenes"):
            out["scenes"] = enriched

    out["forbid_placeholder_characters"] = True
    out["forbid_empty_environments"] = True
    out["prefer_studio_character_plates"] = True
    return out


def studio_place_candidate(
    candidate: dict[str, Any],
    *,
    topic: str = "",
    production_id: str = "",
    write: bool = True,
    out_dir: str | Path | None = None,
) -> dict[str, Any]:
    pkg = build_character_world_studio_package(
        candidate,
        topic=topic or str(candidate.get("topic") or candidate.get("title") or ""),
        production_id=production_id,
        write=write,
        out_dir=out_dir,
    )
    return attach_character_world_studio(candidate, pkg)


def _markdown(package: dict[str, Any]) -> str:
    gate = package.get("quality_gate") or {}
    loc = package.get("location") or {}
    lines = [
        "# Character & World Studio Notes",
        "",
        f"**Topic:** {package.get('topic')}",
        f"**Gate:** {gate.get('decision')}",
        f"**Location:** {loc.get('name')} (`{loc.get('id')}`)",
        "",
        "## Cast",
        "",
    ]
    for h in package.get("cast") or []:
        lines.append(f"- **{h.get('name')}** (`{h.get('id')}`) — {h.get('role')}")
        lines.append(f"  - Personality: {', '.join(h.get('personality') or [])}")
        lines.append(f"  - Silhouette: {h.get('silhouette')}")
    lines += ["", "## World life", ""]
    lines.append(f"- Ambient: {', '.join(loc.get('ambient_life') or [])}")
    lines.append(f"- Animation: {', '.join(loc.get('environmental_animation') or [])}")
    lines.append(f"- Dressing: {', '.join(loc.get('detail_dressing') or [])}")
    lines += ["", "## Self-review", ""]
    for k, v in (gate.get("questions") or {}).items():
        lines.append(f"- {k}: {'YES' if v else 'NO'}")
    lines += ["", "_Universe layer — Animation Engine still executes motion._", ""]
    return "\n".join(lines)
