"""Creative Intelligence (Agent 12, v1.1) — worlds, camera direction,
color & lighting, animation planning, asset planning, platform
adaptation, creative memory, the learning loop, and the extended quality
validation, plus contract and failure-handling coverage."""

from __future__ import annotations

import pytest

# Imported first (like every engine test) so the engines package fully
# initializes before conftest's publishing fixture touches
# services.publishing — entering that package first trips a pre-existing
# publishing↔seo↔engines import cycle.
import engines  # noqa: F401

from services.creative_studio import (
    CAMERA_SHOT_FIELDS,
    COLOR_LIGHTING_FIELDS,
    CREATIVE_GUIDANCE_FIELDS,
    MEMORY_ENTRY_FIELDS,
    PLATFORM_ADAPTATION_FIELDS,
    STORYBOARD_SCENE_FIELDS,
    WORLD_FIELDS,
    CharacterKind,
    CreativeMemory,
    MemoryKind,
    apply_guidance_to_item,
    build_animation_plan,
    build_asset_plan,
    build_blueprint,
    build_camera_plan,
    build_color_lighting_plan,
    build_creative_package,
    build_platform_adaptations,
    build_storyboard,
    build_asset_requirements,
    cast_characters,
    create_character,
    derive_creative_guidance,
    get_platform_profile,
    get_style,
    get_world,
    record_production,
    register_platform_profile,
    register_world,
    select_production_type,
    select_world,
    validate_package,
)


@pytest.fixture
def item() -> dict:
    return {
        "project_id": "ci_test",
        "topic": "why the ocean is running out of oxygen",
        "niche": "science",
        "title": "The Ocean Is Suffocating",
        "hook": "The ocean is losing its breath",
        "script": (
            "The ocean is losing its breath. Oxygen levels have dropped ten percent. "
            "Dead zones are spreading across every coast. Warm water holds less oxygen. "
            "Fish are fleeing to the poles. But scientists found something unexpected. "
            "Some ecosystems are adapting faster than predicted. Here is what happens next."
        ),
    }


@pytest.fixture
def designed(item):
    blueprint = build_blueprint(item)
    production_type = select_production_type(item)
    characters = cast_characters(item, production_type)
    storyboard = build_storyboard(item, blueprint, characters)
    return item, blueprint, characters, storyboard


# ------------------------------------------------------------ storyboards


def test_scenes_carry_the_full_v11_contract(designed):
    _, _, _, storyboard = designed
    for scene in storyboard:
        for field in STORYBOARD_SCENE_FIELDS:
            assert field in scene, f"scene missing {field}"
        assert scene["psychological_objective"]
        assert scene["music_mood"]
        assert 0 < scene["expected_retention"] <= 100


def test_retention_declines_across_the_board_but_hooks_start_high(designed):
    _, _, _, storyboard = designed
    retentions = [scene["expected_retention"] for scene in storyboard]
    assert retentions[0] >= 90
    assert retentions[-1] < retentions[0]


def test_hook_scene_gets_hook_sfx_and_psychology(designed):
    _, _, _, storyboard = designed
    hook = storyboard[0]
    assert "curiosity gap" in hook["psychological_objective"]
    assert any("whoosh" in sfx or "impact" in sfx for sfx in hook["sound_effects"])


# ----------------------------------------------------------------- worlds


def test_every_production_gets_a_world(designed):
    _, blueprint, _, _ = designed
    assert blueprint["world_id"]
    assert get_world(blueprint["world_id"]) is not None


def test_world_selection_matches_content_signals():
    world = select_world({"topic": "the future of space travel to mars"})
    assert world["world_id"] == "meridian_station"


def test_worlds_carry_the_full_contract():
    world = get_world("everwood")
    for field in WORLD_FIELDS:
        assert field in world, f"world missing {field}"
    assert world["weather"]
    assert world["environmental_storytelling"]


def test_world_engine_expands_at_runtime():
    register_world(
        {
            "world_id": "test_deep_sea",
            "label": "The Deep",
            "keywords": ["abyss", "trench"],
            "environments": ["nature"],
        }
    )
    assert select_world({"topic": "creatures of the abyss trench"})["world_id"] == "test_deep_sea"


# -------------------------------------------------------- camera director


def test_camera_plan_directs_every_scene_at_lens_level(designed):
    _, blueprint, _, storyboard = designed
    plan = build_camera_plan(storyboard, blueprint)
    assert len(plan["shots"]) == len(storyboard)
    for shot in plan["shots"]:
        for field in CAMERA_SHOT_FIELDS:
            assert field in shot, f"shot missing {field}"
        assert "mm" in shot["lens"]
        assert shot["depth_of_field"]
        assert shot["composition"]
    assert plan["lens_kit"]


def test_camera_direction_is_deterministic(designed):
    _, blueprint, _, storyboard = designed
    assert build_camera_plan(storyboard, blueprint) == build_camera_plan(storyboard, blueprint)


# ------------------------------------------------------- color & lighting


def test_color_lighting_plan_carries_the_full_contract(designed):
    item, blueprint, _, storyboard = designed
    style = get_style(blueprint["visual_style"]) or {}
    plan = build_color_lighting_plan(storyboard, blueprint, style, item)
    for field in COLOR_LIGHTING_FIELDS:
        assert field in plan, f"plan missing {field}"
    assert len(plan["lighting_setups"]) == len(storyboard)
    assert len(plan["emotional_color_map"]) == len(storyboard)


def test_accessibility_guidance_is_always_present(designed):
    item, blueprint, _, storyboard = designed
    plan = build_color_lighting_plan(storyboard, blueprint, {}, item)
    accessibility = plan["accessibility"]
    assert "caption_contrast" in accessibility
    assert "flash_safety" in accessibility
    assert "color_independence" in accessibility


def test_emotions_map_to_distinct_color_treatments(designed):
    item, blueprint, _, storyboard = designed
    plan = build_color_lighting_plan(storyboard, blueprint, {}, item)
    by_emotion = {entry["emotion"]: entry["treatment"] for entry in plan["emotional_color_map"]}
    if "curiosity" in by_emotion and "satisfaction" in by_emotion:
        assert by_emotion["curiosity"] != by_emotion["satisfaction"]


# ------------------------------------------------------ animation planning


def test_animation_plan_covers_movement_faces_camera_and_lip_sync(designed):
    _, blueprint, characters, storyboard = designed
    plan = build_animation_plan(storyboard, blueprint, characters)
    assert len(plan["character_movement"]) == len(characters)
    assert len(plan["facial_animation"]) == len(storyboard)
    assert len(plan["camera_animation"]) == len(storyboard)
    assert len(plan["lip_sync"]) == len(storyboard)
    assert plan["physics_notes"]
    # v1.0 keys survive for downstream consumers.
    assert "animation_style" in plan and "scenes" in plan


def test_lip_sync_windows_never_exceed_scene_duration(designed):
    _, blueprint, characters, storyboard = designed
    plan = build_animation_plan(storyboard, blueprint, characters)
    by_scene = {scene["scene_id"]: scene["estimated_duration_sec"] for scene in storyboard}
    for sync in plan["lip_sync"]:
        assert sync["speech_window_sec"] <= by_scene[sync["scene_id"]] + 0.01


# --------------------------------------------------------- asset planning


def test_asset_plan_requests_backgrounds_icons_logo_and_vfx(designed):
    item, blueprint, characters, storyboard = designed
    base = build_asset_requirements(storyboard, blueprint, characters)
    plan = build_asset_plan(storyboard, blueprint, characters, base, item)
    categories = {request["category"] for request in plan}
    assert {"scene_visual", "background", "icon", "logo", "vfx"} <= categories
    assert all(request["status"] == "planned" for request in plan)


def test_asset_plan_only_requests_never_generates(designed):
    item, blueprint, characters, storyboard = designed
    base = build_asset_requirements(storyboard, blueprint, characters)
    plan = build_asset_plan(storyboard, blueprint, characters, base, item)
    for request in plan:
        assert "prompt" in request and "asset_type" in request
        assert "content" not in request and "url" not in request


def test_vehicle_props_are_typed_as_vehicles(designed):
    item, blueprint, characters, _ = designed
    storyboard = [
        {
            "scene_id": "s1", "purpose": "development", "background": "city",
            "props": ["a red car", "coffee cup"], "overlay_graphics": [],
            "lighting": "", "color_palette": "",
        }
    ]
    plan = build_asset_plan(storyboard, blueprint, characters, [], item)
    vehicle = [request for request in plan if request["category"] == "vehicle"]
    assert len(vehicle) == 1 and "car" in vehicle[0]["description"]


# ----------------------------------------------------- platform adaptation


def test_adaptations_cover_the_targeted_platforms(designed):
    item, _, _, storyboard = designed
    item = dict(item, target_platforms=["tiktok", "linkedin"])
    adaptations = build_platform_adaptations(item, storyboard)
    assert {a["platform"] for a in adaptations} == {"tiktok", "linkedin"}
    for adaptation in adaptations:
        for field in PLATFORM_ADAPTATION_FIELDS:
            assert field in adaptation, f"adaptation missing {field}"


def test_platforms_differ_where_it_matters():
    tiktok = get_platform_profile("tiktok")
    linkedin = get_platform_profile("linkedin")
    assert tiktok["aspect_ratio"] != linkedin["aspect_ratio"]
    assert tiktok["opening_seconds"] != linkedin["opening_seconds"]


def test_future_platforms_register_at_runtime(designed):
    item, _, _, storyboard = designed
    register_platform_profile(
        {"platform": "test_vr_feed", "aspect_ratio": "360", "max_duration_sec": 300}
    )
    item = dict(item, target_platforms=["test_vr_feed"])
    adaptations = build_platform_adaptations(item, storyboard)
    assert adaptations[0]["platform"] == "test_vr_feed"


# --------------------------------------------------------- creative memory


def test_memory_remembers_and_recalls(tmp_path):
    memory = CreativeMemory(directory=str(tmp_path))
    entry = memory.remember(MemoryKind.MOTIF, "slow_reveal", {"works_for": "science"})
    for field in MEMORY_ENTRY_FIELDS:
        assert field in entry, f"entry missing {field}"
    assert memory.latest(MemoryKind.MOTIF, "slow_reveal")["content"]["works_for"] == "science"
    assert memory.entry_count() == 1


def test_memory_is_append_only(tmp_path):
    memory = CreativeMemory(directory=str(tmp_path))
    memory.remember(MemoryKind.STYLE, "minimal", {"used": 1})
    memory.remember(MemoryKind.STYLE, "minimal", {"used": 2})
    assert memory.entry_count() == 2
    assert memory.latest(MemoryKind.STYLE, "minimal")["content"]["used"] == 2


def test_productions_are_remembered(item, tmp_path, monkeypatch):
    import services.creative_studio.memory as memory_module

    monkeypatch.setattr(memory_module, "_DEFAULT_DIR", str(tmp_path))
    package = build_creative_package(item)
    entries = record_production(package, item)
    kinds = {entry["kind"] for entry in entries}
    assert MemoryKind.CHARACTER in kinds
    assert MemoryKind.WORLD in kinds
    assert MemoryKind.STYLE in kinds
    assert MemoryKind.SCENE_STRUCTURE in kinds


def test_broken_memory_never_breaks_the_studio(item, monkeypatch):
    import services.creative_studio.memory as memory_module

    monkeypatch.setattr(memory_module, "_DEFAULT_DIR", "/dev/null/impossible")
    package = build_creative_package(item)
    entries = record_production(package, item)
    assert entries == [] or entries is not None  # degraded, not raised


# ------------------------------------------------------------ learning loop


def test_guidance_is_empty_without_upstream_intelligence():
    guidance = derive_creative_guidance({})
    for field in CREATIVE_GUIDANCE_FIELDS:
        assert field in guidance, f"guidance missing {field}"
    assert guidance["sources"] == []


def test_learning_recommendations_shape_pacing():
    context = {
        "learning_recommendations": [
            {
                "target_engine": "visual_intelligence",
                "recommendation": "use shorter scenes with faster pacing",
            }
        ]
    }
    guidance = derive_creative_guidance(context)
    assert guidance["pacing_hint"] == "rapid"
    assert "learning_recommendations" in guidance["sources"]


def test_explicit_item_choices_beat_learned_guidance():
    guidance = {"pacing_hint": "rapid", "style_hint": "minimal"}
    item = {"pacing": "slow", "visual_style": "luxury"}
    guided = apply_guidance_to_item(item, guidance)
    assert guided["pacing"] == "slow"
    assert guided["visual_style"] == "luxury"


def test_guidance_fills_unstated_preferences():
    guided = apply_guidance_to_item({}, {"pacing_hint": "measured", "style_hint": "minimal"})
    assert guided["pacing"] == "measured"
    assert guided["visual_style"] == "minimal"


def test_package_records_its_learning_adaptations(item):
    context = {
        "learning_recommendations": [
            {"target_engine": "creative_studio", "recommendation": "use shorter hooks"}
        ]
    }
    package = build_creative_package(item, context)
    assert package["learning_adaptations"]["sources"] == ["learning_recommendations"]


# --------------------------------------------------------------- characters


def test_characters_carry_the_v11_identity_fields():
    character = create_character(
        {
            "name": "Test Dragon",
            "kind": CharacterKind.FANTASY,
            "description": "A small teal dragon.",
            "expressions": ["smug", "sleepy"],
            "movement_style": "lazy glides",
            "emotion_profile": {"surprise": "wings flare"},
            "accessories": ["tiny scarf"],
            "memory_hooks": ["test_dragon"],
        }
    )
    assert character["kind"] == CharacterKind.FANTASY
    assert character["expressions"] == ["smug", "sleepy"]
    assert character["emotion_profile"]["surprise"] == "wings flare"
    assert character["memory_hooks"] == ["test_dragon"]


def test_characters_default_to_sensible_identity():
    character = create_character({"name": "Plain", "description": "A plain human."})
    assert character["kind"] == CharacterKind.HUMAN
    assert character["expressions"]
    assert character["memory_hooks"] == [character["character_id"]]


# ------------------------------------------------------- quality validation


def test_duplicate_characters_are_flagged(designed):
    item, *_ = designed
    package = build_creative_package(item)
    cast = package["character_plan"]["cast"]
    package["character_plan"]["cast"] = cast + [dict(cast[0])]
    validation = validate_package(package)
    assert any("cast more than once" in warning for warning in validation["warnings"])


def test_broken_story_flow_is_flagged(designed):
    item, *_ = designed
    package = build_creative_package(item)
    package["storyboard"][0]["purpose"] = "payoff"
    validation = validate_package(package)
    assert any("story flow" in warning for warning in validation["warnings"])


def test_brand_violations_are_flagged(designed):
    item, *_ = designed
    package = build_creative_package(item)
    package["character_plan"]["cast"][0]["brand_id"] = "someone_elses_brand"
    validation = validate_package(package)
    assert any("brand" in warning for warning in validation["warnings"])


def test_missing_accessibility_guidance_is_flagged(designed):
    item, *_ = designed
    package = build_creative_package(item)
    package["color_lighting_plan"] = {}
    validation = validate_package(package)
    assert any("accessibility" in warning for warning in validation["warnings"])


def test_healthy_package_passes_the_extended_checks(designed):
    item, *_ = designed
    package = build_creative_package(item)
    checks = package["validation"]["checks"]
    assert checks["duplicate_characters"]["duplicates"] == 0
    assert checks["story_flow"]["issues"] == 0
    assert checks["brand"]["violations"] == 0
    assert checks["accessibility"]["guidance_present"] is True


# ------------------------------------------------------ package integration


def test_v11_package_carries_every_new_section(item):
    package = build_creative_package(item)
    assert package["creative_package_version"] == "1.1"
    for section in (
        "world_plan", "color_lighting_plan", "platform_adaptations",
        "creative_memory", "learning_adaptations",
    ):
        assert section in package, f"package missing {section}"
    assert package["world_plan"]["world"]["world_id"]
    assert len(package["camera_plan"]["shots"]) == len(package["storyboard"])
    assert package["animation_plan"]["lip_sync"]
    assert package["platform_adaptations"]


def test_package_building_is_deterministic(item):
    first = build_creative_package(dict(item))
    second = build_creative_package(dict(item))
    first.pop("generated_at"), second.pop("generated_at")
    assert first == second
