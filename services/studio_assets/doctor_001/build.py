"""Build permanent Studio Character DOCTOR_001 — complete reusable package."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.studio_assets.doctor_001.catalog import (
    ASSET_SLUG,
    ASSET_VERSION,
    CAMERA_TESTS,
    CHARACTER_ID,
    CORE_ANIMATIONS,
    ENVIRONMENT_INTERACTIONS,
    EXPRESSIONS,
    HAND_POSES,
    LEGACY_ALIAS,
    LIGHTING_REFS,
    ORTHOGRAPHIC_VIEWS,
    REACTION_ANIMATIONS,
)
from services.studio_assets.doctor_001.identity import (
    COLOR_PALETTE,
    biography_md,
    catch_phrases,
    continuity_rules_md,
    emotional_profile,
    identity_core,
    personality_profile,
    strengths_flaws,
    teaching_style_md,
    voice_identity,
)
from services.studio_assets.doctor_001.plates import (
    lighting_sidecar,
    render_camera_test,
    render_closeup,
    render_env_interaction,
    render_expression,
    render_fullbody,
    render_hand_pose,
    render_lighting_ref,
    render_orthographic,
    render_scale_reference,
)
from services.studio_assets.doctor_001.specs import (
    animation_clip,
    animation_constraints,
    blinking_model,
    breathing_profile,
    clothing_simulation,
    eye_movement_model,
    facial_topology,
    gesture_library,
    hair_profile,
    hand_pose_library,
    materials,
    muscle_definition,
    rig_specification,
    silhouette_rules,
    skeletal_proportions,
    skin_material,
)
from services.studio_assets.registry import upsert_asset
from services.studio_assets.the_doctor.world import gmri_world_package, lighting_presets

ROOT = Path(__file__).resolve().parents[3]
ASSET_ROOT = ROOT / "data" / "studio_assets" / ASSET_SLUG


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")


def _write_md(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return str(path)


def _character_bible() -> str:
    return f"""# Generational Studio Character — {CHARACTER_ID}

**Name:** The Doctor  
**Role:** Canonical medical educator for the Generational Universe  
**Version:** {ASSET_VERSION}  
**Status:** Permanent reusable studio asset  

This is not an episode character sheet.

This package is the permanent visual and performance identity for The Doctor.
Every future production must cast `{CHARACTER_ID}` from these libraries so the
character remains visually identical across every video.

Legacy pipeline alias: `{LEGACY_ALIAS}` (same character).

See `CONTINUITY_RULES.md`, `IDENTITY.json`, and folder libraries in this package.
"""


def ensure_doctor_001_asset(*, force: bool = False) -> dict[str, Any]:
    ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}

    # Identity + prose
    _write_json(ASSET_ROOT / "IDENTITY.json", identity_core())
    _write_json(ASSET_ROOT / "COLOR_PALETTE.json", COLOR_PALETTE)
    _write_json(ASSET_ROOT / "PERSONALITY_PROFILE.json", personality_profile())
    _write_json(ASSET_ROOT / "EMOTIONAL_PROFILE.json", emotional_profile())
    _write_json(ASSET_ROOT / "STRENGTHS_FLAWS.json", strengths_flaws())
    _write_json(ASSET_ROOT / "VOICE_IDENTITY.json", voice_identity())
    _write_json(ASSET_ROOT / "CATCH_PHRASES.json", catch_phrases())
    _write_md(ASSET_ROOT / "BIOGRAPHY.md", biography_md())
    _write_md(ASSET_ROOT / "TEACHING_STYLE.md", teaching_style_md())
    _write_md(ASSET_ROOT / "CONTINUITY_RULES.md", continuity_rules_md())
    _write_md(ASSET_ROOT / "CHARACTER_BIBLE.md", _character_bible())

    # Technical specs
    _write_json(ASSET_ROOT / "FACIAL_TOPOLOGY.json", facial_topology())
    _write_json(ASSET_ROOT / "EYE_MOVEMENT_MODEL.json", eye_movement_model())
    _write_json(ASSET_ROOT / "BLINKING_MODEL.json", blinking_model())
    _write_json(ASSET_ROOT / "BREATHING_PROFILE.json", breathing_profile())
    _write_json(ASSET_ROOT / "PROPORTIONS.json", identity_core()["proportions"])
    _write_json(ASSET_ROOT / "SKELETAL_PROPORTIONS.json", skeletal_proportions())
    _write_json(ASSET_ROOT / "MUSCLE_DEFINITION.json", muscle_definition())
    _write_json(ASSET_ROOT / "SKIN_MATERIAL.json", skin_material())
    _write_json(ASSET_ROOT / "HAIR_PROFILE.json", hair_profile())
    _write_json(ASSET_ROOT / "MATERIALS.json", materials())
    _write_json(ASSET_ROOT / "CLOTHING_SIMULATION.json", clothing_simulation())
    _write_json(ASSET_ROOT / "SILHOUETTE_RULES.json", silhouette_rules())
    _write_json(ASSET_ROOT / "RIG_SPECIFICATION.json", rig_specification())
    _write_json(ASSET_ROOT / "ANIMATION_CONSTRAINTS.json", animation_constraints())
    _write_json(ASSET_ROOT / "GESTURE_LIBRARY.json", gesture_library())
    _write_json(ASSET_ROOT / "HAND_POSE_LIBRARY.json", hand_pose_library())

    # Orthographic
    ortho_dir = ASSET_ROOT / "ORTHOGRAPHIC"
    ortho_index: dict[str, str] = {}
    for view in ORTHOGRAPHIC_VIEWS:
        p = ortho_dir / f"{view}.png"
        if force or not p.is_file():
            render_orthographic(p, view)
        ortho_index[view] = str(p.relative_to(ASSET_ROOT))
    _write_json(ortho_dir / "index.json", ortho_index)
    counts["orthographic"] = len(ortho_index)

    # Expressions 50+
    expr_dir = ASSET_ROOT / "EXPRESSIONS"
    expr_index: dict[str, str] = {}
    for exp in EXPRESSIONS:
        p = expr_dir / f"{exp}.png"
        if force or not p.is_file():
            render_expression(p, exp)
        expr_index[exp] = str(p.relative_to(ASSET_ROOT))
    _write_json(
        expr_dir / "index.json",
        {"count": len(expr_index), "expressions": expr_index, "character_id": CHARACTER_ID},
    )
    counts["expressions"] = len(expr_index)

    # Hand poses
    hand_dir = ASSET_ROOT / "HAND_POSES"
    hand_index: dict[str, str] = {}
    for hp in HAND_POSES:
        p = hand_dir / f"{hp}.png"
        if force or not p.is_file():
            render_hand_pose(p, hp)
        hand_index[hp] = str(p.relative_to(ASSET_ROOT))
    _write_json(hand_dir / "index.json", hand_index)
    counts["hand_poses"] = len(hand_index)

    # Animations
    anim_dir = ASSET_ROOT / "ANIMATION"
    anim_index: dict[str, str] = {}
    for name in CORE_ANIMATIONS:
        loop = name in {"idle", "breathing", "blinking", "walking_cycle", "running_cycle"}
        extra = {}
        if name == "walking_cycle":
            extra = {"phases": animation_constraints()["walk_phases"], "traits": animation_constraints()["doctor_walk_traits"]}
        if name == "running_cycle":
            extra = {"includes_airborne_phase": True, "style": "controlled_urgent_clinical"}
        if name == "talking":
            extra = {"lipsync": True, "coordinate_with": ["jaw", "brows", "gesture_accents"]}
        clip = animation_clip(name, loop=loop, extra=extra)
        _write_json(anim_dir / f"{name}.json", clip)
        anim_index[name] = f"{name}.json"
    react_dir = anim_dir / "reactions"
    for name in REACTION_ANIMATIONS:
        clip = animation_clip(name, loop=False, extra={"category": "reaction"})
        _write_json(react_dir / f"{name}.json", clip)
        anim_index[name] = f"reactions/{name}.json"
    _write_json(anim_dir / "index.json", {"clips": anim_index, "count": len(anim_index)})
    counts["animations"] = len(anim_index)

    # References
    close_dir = ASSET_ROOT / "CLOSEUP_REFERENCE"
    full_dir = ASSET_ROOT / "FULLBODY_REFERENCE"
    scale_dir = ASSET_ROOT / "SCALE_REFERENCE"
    for d, renderer, fname in (
        (close_dir, render_closeup, "closeup_hero.png"),
        (full_dir, render_fullbody, "fullbody_hero.png"),
        (scale_dir, render_scale_reference, "scale_185cm.png"),
    ):
        p = d / fname
        if force or not p.is_file():
            renderer(p)
        _write_json(d / "index.json", {"plate": str(p.relative_to(ASSET_ROOT))})

    # Lighting reference
    light_dir = ASSET_ROOT / "LIGHTING_REFERENCE"
    light_index: dict[str, Any] = {}
    for name in LIGHTING_REFS:
        p = light_dir / f"{name}.png"
        if force or not p.is_file():
            render_lighting_ref(p, name)
        meta = lighting_sidecar(name)
        _write_json(light_dir / f"{name}.json", meta)
        light_index[name] = {"plate": str(p.relative_to(ASSET_ROOT)), "meta": f"{name}.json"}
    # include GMRI presets for production reuse
    for name, preset in lighting_presets().items():
        _write_json(light_dir / f"gmri_{name}.json", preset)
    _write_json(light_dir / "index.json", light_index)
    counts["lighting_refs"] = len(light_index)

    # Camera tests
    cam_dir = ASSET_ROOT / "CAMERA_TESTS"
    cam_index: dict[str, str] = {}
    for name in CAMERA_TESTS:
        p = cam_dir / f"{name}.png"
        if force or not p.is_file():
            render_camera_test(p, name)
        cam_index[name] = str(p.relative_to(ASSET_ROOT))
    _write_json(cam_dir / "index.json", cam_index)
    counts["camera_tests"] = len(cam_index)

    # Environment interactions
    env_dir = ASSET_ROOT / "ENVIRONMENT_INTERACTIONS"
    env_index: dict[str, str] = {}
    for name in ENVIRONMENT_INTERACTIONS:
        p = env_dir / f"{name}.png"
        if force or not p.is_file():
            render_env_interaction(p, name)
        env_index[name] = str(p.relative_to(ASSET_ROOT))
    _write_json(env_dir / "index.json", env_index)
    _write_json(env_dir / "WORLD_PACKAGE.json", gmri_world_package())
    counts["environment_interactions"] = len(env_index)

    _write_json(
        ASSET_ROOT / "VERSION.json",
        {
            "character_id": CHARACTER_ID,
            "legacy_alias": LEGACY_ALIAS,
            "version": ASSET_VERSION,
            "status": "permanent",
            "updated_at": _now(),
            "changelog": [
                {
                    "version": "1.0.0",
                    "note": (
                        "First permanent Generational Studio Character package — "
                        "complete reusable medical educator asset (not episode sheet)."
                    ),
                },
                {
                    "version": "1.1.0",
                    "note": (
                        "Official master concept art lock — 20 permanent visual identity "
                        "plates under MASTER_CONCEPT_ART/ (hero, turnaround, expressions, studies)."
                    ),
                },
            ],
        },
    )

    # Human Realism inheritance materialization into this package
    try:
        from services.human_realism import materialize_character

        materialize_character(CHARACTER_ID, also_to=ASSET_ROOT)
    except Exception:  # noqa: BLE001
        pass

    # Facial Performance + Environment Construction standards
    try:
        from services.character_performance import face_rig_profile
        from services.environment_department import build_environment_package

        _write_json(ASSET_ROOT / "FACE_RIG_PROFILE.json", face_rig_profile(CHARACTER_ID))
        env_pkg = build_environment_package("LOC-GMRI", owner=CHARACTER_ID)
        env_dir = ASSET_ROOT / "ENVIRONMENT_CONSTRUCTION"
        env_dir.mkdir(parents=True, exist_ok=True)
        _write_json(env_dir / "ENVIRONMENT_PACKAGE.json", env_pkg)
        _write_json(ASSET_ROOT / "ENVIRONMENT_PACKAGE.json", env_pkg)
    except Exception:  # noqa: BLE001
        pass

    manifest = {
        "package_type": "GENERATIONAL_STUDIO_CHARACTER",
        "character_id": CHARACTER_ID,
        "legacy_alias": LEGACY_ALIAS,
        "name": "The Doctor",
        "version": ASSET_VERSION,
        "status": "permanent",
        "generated_at": _now(),
        "root": str(ASSET_ROOT),
        "counts": counts,
        "libraries": {
            "ORTHOGRAPHIC": True,
            "EXPRESSIONS": counts.get("expressions", 0),
            "HAND_POSES": counts.get("hand_poses", 0),
            "ANIMATION": counts.get("animations", 0),
            "LIGHTING_REFERENCE": True,
            "CAMERA_TESTS": counts.get("camera_tests", 0),
            "ENVIRONMENT_INTERACTIONS": counts.get("environment_interactions", 0),
            "CLOSEUP_REFERENCE": True,
            "FULLBODY_REFERENCE": True,
            "SCALE_REFERENCE": True,
            "MASTER_CONCEPT_ART": (ASSET_ROOT / "MASTER_CONCEPT_ART" / "INDEX.json").is_file(),
        },
        "master_concept_art": {
            "path": "MASTER_CONCEPT_ART/",
            "bible": "MASTER_CONCEPT_ART/MASTER_CONCEPT_BIBLE.md",
            "primary_keys": [
                "MASTER_CONCEPT_ART/doctor_001_06_hero_portrait.png",
                "MASTER_CONCEPT_ART/doctor_001_20_official_character_reference_sheet.png",
            ],
            "status": "permanent_visual_identity_lock",
        },
        "specs": [
            "FACIAL_TOPOLOGY.json",
            "EYE_MOVEMENT_MODEL.json",
            "BLINKING_MODEL.json",
            "BREATHING_PROFILE.json",
            "SKELETAL_PROPORTIONS.json",
            "MUSCLE_DEFINITION.json",
            "SKIN_MATERIAL.json",
            "HAIR_PROFILE.json",
            "MATERIALS.json",
            "CLOTHING_SIMULATION.json",
            "SILHOUETTE_RULES.json",
            "RIG_SPECIFICATION.json",
            "ANIMATION_CONSTRAINTS.json",
            "GESTURE_LIBRARY.json",
            "HAND_POSE_LIBRARY.json",
            "VOICE_IDENTITY.json",
            "PERSONALITY_PROFILE.json",
            "EMOTIONAL_PROFILE.json",
        ],
        "philosophy": {
            "not_episode_sheet": True,
            "permanent_reusable_ip": True,
            "visually_identical_across_videos": True,
            "no_new_renderer": True,
            "no_pipeline_redesign": True,
            "cinematic_realism": True,
        },
    }
    _write_json(ASSET_ROOT / "MANIFEST.json", manifest)

    upsert_asset(
        {
            "id": CHARACTER_ID,
            "legacy_alias": LEGACY_ALIAS,
            "asset_number": "0001",
            "name": "The Doctor",
            "slug": ASSET_SLUG,
            "version": ASSET_VERSION,
            "status": "permanent",
            "role": "Canonical Medical Educator",
            "path": f"data/studio_assets/{ASSET_SLUG}/",
            "home_world": "LOC-GMRI",
            "flagship_science_educator": True,
            "manifest": "MANIFEST.json",
            "package_type": "GENERATIONAL_STUDIO_CHARACTER",
        }
    )
    # Keep legacy registry row pointing at same character
    upsert_asset(
        {
            "id": LEGACY_ALIAS,
            "canonical_id": CHARACTER_ID,
            "name": "The Doctor",
            "slug": ASSET_SLUG,
            "version": ASSET_VERSION,
            "status": "permanent",
            "role": "Canonical Medical Educator",
            "path": f"data/studio_assets/{ASSET_SLUG}/",
            "home_world": "LOC-GMRI",
            "flagship_science_educator": True,
            "alias_of": CHARACTER_ID,
        }
    )
    return manifest
