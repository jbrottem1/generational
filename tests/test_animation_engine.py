"""Tests for the Animation & Cinematic Production Engine (Agent 16).

Covers: timeline generation, camera planning, animation planning, lip sync,
provider abstraction, quality validation, pipeline integration,
configuration, and failure handling.
"""

from __future__ import annotations

import engines  # noqa: F401 - importing registers all engines
from engines import registry
from engines.contracts import ContractEngine
from providers.animation import (
    MockAnimationProvider,
    get_animation_provider,
    provider_for_capability,
    register_animation_provider,
)
from providers.animation_provider import ANIMATION_CAPABILITIES, ANIMATION_PROVIDER_IDS, AnimationProvider
from services.animation import (
    ANIMATION_PACKAGE_FIELDS,
    ANIMATION_SUMMARY_FIELDS,
    AnimationConfig,
    ReadinessStatus,
    batch_plan,
    build_animation_package,
    configure,
    plan_series,
    prepare_render_batch,
    reset_animation_config,
    validate_package,
)
from services.animation.camera import plan_camera, resolve_movement, resolve_shot_type
from services.animation.lip_sync import plan_lip_sync
from services.animation.models import CameraMovement, CameraShotType, TransitionType
from services.animation.timeline import build_scene_timing
from services.orchestrator import ContentPackage, Orchestrator, StageStatus
from services.orchestrator.stages import DISTRIBUTION_STAGES, STAGE_GROUPS


def make_item(project_id="proj1", with_creative=True):
    """One ContentPackage-style dict with optional creative blueprint."""
    item = {
        "project_id": project_id,
        "topic": "deep sea creatures",
        "niche": "science",
        "title": "The Ocean Mystery",
        "hook": "What if the ocean disappeared tomorrow?",
        "script": (
            "The ocean vanishes overnight. Cities panic as the tides stop. "
            "Scientists trace the cause to a rift. The rift is growing. "
            "Humanity must act before dawn."
        ),
        "keywords": ["ocean", "science"],
        "quality_score": 80,
        "publish_ready": True,
        "target_platforms": ["youtube_shorts"],
        "script_package": {
            "script": (
                "The ocean vanishes overnight. Cities panic as the tides stop. "
                "Scientists trace the cause to a rift."
            ),
            "script_score": 78,
        },
        "visual_package": {"scenes": []},
        "audio_package": {"voice_style": {"name": "narrator"}},
        "render_package": {"render_package_version": "2.0"},
        "asset_package": {"assets": [{"asset_id": "a1", "status": "ready"}]},
        "psychology_package": {"energy": "high"},
    }
    if with_creative:
        item["creative_package"] = {
            "creative_package_version": "1.0",
            "creative_blueprint": {
                "production_type": "science_visualization",
                "visual_style": "cinematic_realism",
                "aspect_ratio": "9:16",
                "target_duration_sec": 15,
                "pacing": {"tempo": "dynamic"},
                "cinematic_language": {"camera_grammar": "documentary"},
                "production_complexity": "standard",
            },
            "storyboard": [
                {
                    "scene_id": "scene_1",
                    "purpose": "hook",
                    "emotion": "curiosity",
                    "narration": "What if the ocean disappeared tomorrow?",
                    "visual_description": "Wide establishing shot of a calm ocean under fog.",
                    "camera_angle": "establishing wide",
                    "camera_movement": "slow push",
                    "lighting": "cool blue soft key",
                    "color_palette": "deep blue",
                    "animation_style": "cinematic",
                    "motion_instructions": "gentle water motion",
                    "transitions": {"in": "fade", "out": "cut"},
                    "background": "ocean_surface",
                    "props": [],
                    "characters": ["char_narrator"],
                    "overlay_graphics": [],
                    "estimated_duration_sec": 3.0,
                    "asset_requirements": ["a1"],
                    "production_notes": "",
                },
                {
                    "scene_id": "scene_2",
                    "purpose": "develop",
                    "emotion": "fear",
                    "narration": "Cities panic as the tides stop.",
                    "visual_description": "Medium shot of a coastal city in rain and smoke.",
                    "camera_angle": "medium",
                    "camera_movement": "handheld drift",
                    "lighting": "dramatic hard key",
                    "color_palette": "desaturated",
                    "animation_style": "cinematic",
                    "motion_instructions": "crowd walking in panic",
                    "transitions": {"in": "cut", "out": "dissolve"},
                    "background": "city_coast",
                    "props": ["umbrella"],
                    "characters": ["char_narrator", "char_crowd"],
                    "overlay_graphics": [],
                    "estimated_duration_sec": 4.0,
                    "asset_requirements": [],
                    "production_notes": "",
                },
                {
                    "scene_id": "scene_3",
                    "purpose": "payoff",
                    "emotion": "surprise",
                    "narration": "Humanity must act before dawn.",
                    "visual_description": "Close-up of a glowing energy rift under water.",
                    "camera_angle": "close-up",
                    "camera_movement": "orbit",
                    "lighting": "neon energy",
                    "color_palette": "cyan magenta",
                    "animation_style": "cinematic",
                    "motion_instructions": "energy pulse",
                    "transitions": {"in": "dissolve", "out": "fade"},
                    "background": "rift",
                    "props": [],
                    "characters": ["char_narrator"],
                    "overlay_graphics": ["countdown"],
                    "estimated_duration_sec": 5.0,
                    "asset_requirements": [],
                    "production_notes": "",
                },
            ],
            "shot_list": [
                {
                    "shot_id": "shot_1",
                    "scene_id": "scene_1",
                    "shot_number": 1,
                    "shot_type": "establishing",
                    "camera_angle": "wide",
                    "camera_movement": "push",
                    "subject": "ocean",
                    "duration_sec": 3.0,
                    "notes": "",
                },
                {
                    "shot_id": "shot_2",
                    "scene_id": "scene_2",
                    "shot_number": 2,
                    "shot_type": "medium",
                    "camera_angle": "medium",
                    "camera_movement": "pan",
                    "subject": "city",
                    "duration_sec": 4.0,
                    "notes": "",
                },
                {
                    "shot_id": "shot_3",
                    "scene_id": "scene_3",
                    "shot_number": 3,
                    "shot_type": "close_up",
                    "camera_angle": "close-up",
                    "camera_movement": "orbit",
                    "subject": "rift",
                    "duration_sec": 5.0,
                    "notes": "",
                },
            ],
            "character_plan": {
                "cast": [
                    {"character_id": "char_narrator", "name": "Narrator", "role": "narrator"},
                    {"character_id": "char_crowd", "name": "Crowd", "role": "original"},
                ],
            },
            "camera_plan": {"cinematic_language": {"camera_grammar": "documentary"}},
            "asset_requirements": [{"asset_id": "a1", "asset_type": "ai_video"}],
            "animation_plan": {"animation_style": "cinematic"},
        }
    return item


# ----------------------------------------------------------------- contract


def test_animation_is_a_live_contract_engine():
    engine = registry.get_engine("animation")
    assert isinstance(engine, ContractEngine)
    assert engine.is_ready() is True
    diag = engine.diagnostics()
    assert diag["engine_id"] == "animation"
    assert diag["version"] == "1.0.0"
    assert "unified_packages" in diag["input_contract"]
    assert "animation_summary" in diag["output_contract"]
    assert "animation_packages" in diag["output_contract"]
    assert "quality" in diag["dependencies"]
    assert "animation-planning" in diag["capabilities"]
    assert engine.health_check()["healthy"] is True


def test_animation_stage_is_wired():
    assert "animation" in STAGE_GROUPS
    assert STAGE_GROUPS["animation"] == ["animation"]
    assert "animation" in DISTRIBUTION_STAGES
    assert list(DISTRIBUTION_STAGES).index("animation") > list(DISTRIBUTION_STAGES).index("asset_generation")
    assert list(DISTRIBUTION_STAGES).index("animation") < list(DISTRIBUTION_STAGES).index("render")


# ----------------------------------------------------------- package output


def test_every_item_gets_a_full_animation_package():
    items = [make_item("p1"), make_item("p2")]
    updates = registry.get_engine("animation").run({"unified_packages": items})

    assert len(updates["animation_packages"]) == 2
    for item, package in zip(items, updates["animation_packages"]):
        assert item["animation_package"] is package
        for field in ANIMATION_PACKAGE_FIELDS:
            assert field in package, field
        assert package["timeline"]["tracks"]
        assert package["camera_plan"]["shots"]
        assert package["scene_timing"]
        assert package["production_readiness"]["status"] in ReadinessStatus.ALL


def test_summary_carries_the_full_contract():
    updates = registry.get_engine("animation").run({"unified_packages": [make_item()]})
    summary = updates["animation_summary"]
    for field in ANIMATION_SUMMARY_FIELDS:
        assert field in summary, field
    assert summary["status"] == "planned"
    assert summary["packages"] == 1
    assert summary["total_duration_sec"] > 0


def test_other_agents_slots_are_never_mutated():
    item = make_item()
    before = {
        key: repr(item[key])
        for key in (
            "script_package", "visual_package", "audio_package",
            "render_package", "creative_package", "asset_package",
        )
    }
    registry.get_engine("animation").run({"unified_packages": [item]})
    for key, snapshot in before.items():
        assert repr(item[key]) == snapshot, f"{key} was mutated"


def test_empty_context_reports_no_items_never_fails():
    updates = registry.get_engine("animation").run({"command": "probe"})
    assert updates["animation_summary"]["status"] == "no_items"
    assert updates["animation_summary"]["items"] == 0
    assert updates["animation_packages"] == []


def test_ideas_fallback_when_no_unified_packages():
    context = {"ideas": [make_item("i1")]}
    updates = registry.get_engine("animation").run(context)
    assert updates["animation_summary"]["items"] == 1
    assert context["ideas"][0]["animation_package"]["timeline"]


def test_script_only_item_still_plans():
    item = make_item("script_only", with_creative=False)
    package = build_animation_package(item)
    assert package["scene_timing"]
    assert package["camera_plan"]["shots"]
    assert package["lip_sync_plan"]
    assert package["timeline"]["total_duration_sec"] > 0


# -------------------------------------------------------------- timeline


def test_timeline_generation_covers_all_track_types():
    package = build_animation_package(make_item())
    track_types = {track["track_type"] for track in package["timeline"]["tracks"]}
    for required in ("scene", "shot", "animation", "audio", "subtitle", "effects", "transition"):
        assert required in track_types
    assert package["timeline"]["fps"] == 30
    assert package["timeline"]["total_frames"] == int(round(package["timeline"]["total_duration_sec"] * 30))


def test_scene_timing_respects_target_duration():
    config = AnimationConfig(target_duration_sec=20.0, fps=24)
    scenes = (make_item()["creative_package"]["storyboard"])
    timing = build_scene_timing(scenes, [], config)
    total = sum(t["duration_sec"] for t in timing)
    assert abs(total - 20.0) < 0.05


# ---------------------------------------------------------------- camera


def test_camera_planning_resolves_shot_types_and_movements():
    assert resolve_shot_type("extreme close-up") == CameraShotType.EXTREME_CLOSE_UP
    assert resolve_shot_type("over the shoulder") == CameraShotType.OVER_THE_SHOULDER
    assert resolve_movement("slow push") == CameraMovement.PUSH
    assert resolve_movement("orbit around subject") == CameraMovement.ORBIT

    config = AnimationConfig(camera_style="cinematic", motion_intensity="high")
    plan = plan_camera(
        make_item()["creative_package"]["storyboard"],
        make_item()["creative_package"]["shot_list"],
        config,
    )
    assert plan["shot_count"] == 3
    for shot in plan["shots"]:
        assert shot["shot_type"] in CameraShotType.ALL
        assert shot["movement"] in CameraMovement.ALL
        assert len(shot["keyframes"]) >= 2
        assert shot["motion_curve"]["interpolation"] == "bezier"


# ------------------------------------------------------------- animation


def test_character_facial_and_body_animation_planned():
    package = build_animation_package(make_item())
    assert package["character_motion"]
    assert package["facial_animation"]
    assert package["body_animation"]
    assert package["choreography"]
    expressions = {face["expression"] for face in package["facial_animation"]}
    assert "curiosity" in expressions or "fear" in expressions or "surprise" in expressions


# -------------------------------------------------------------- lip sync


def test_lip_sync_planning_maps_phonemes_and_words():
    item = make_item()
    scenes = item["creative_package"]["storyboard"]
    timing = build_scene_timing(scenes, [], AnimationConfig())
    plans = plan_lip_sync(scenes, timing, item, AnimationConfig(enable_lip_sync=True))
    assert plans
    plan = plans[0]
    assert plan["words"]
    assert plan["phonemes"]
    assert plan["sentences"]
    # Word timings stay inside the scene window.
    scene = next(t for t in timing if t["scene_id"] == plan["scene_id"])
    assert plan["words"][0]["start_sec"] >= scene["start_sec"] - 0.05
    assert plan["words"][-1]["end_sec"] <= scene["end_sec"] + 0.3


def test_lip_sync_can_be_disabled():
    package = build_animation_package(make_item(), config=AnimationConfig(enable_lip_sync=False))
    assert package["lip_sync_plan"] == []


# ------------------------------------------------------------- providers


def test_mock_animation_provider_serves_every_capability():
    provider = MockAnimationProvider()
    for capability in ANIMATION_CAPABILITIES:
        assert provider.supports(capability)
    result = provider.plan({"id": "x", "capability": "camera", "brief": {"movement": "push"}})
    assert result["placeholder"] is True
    assert result["provider"] == "mock_animation"


def test_provider_registry_lists_future_adapters():
    for provider_id in ANIMATION_PROVIDER_IDS:
        assert provider_id  # reserved ids exist
    # Without API keys, capability resolution falls back to mock.
    assert provider_for_capability("video").provider_id == "mock_animation"
    assert get_animation_provider("runway").provider_id == "mock_animation"


def test_provider_registry_swaps_real_backends():
    from providers.animation.adapters import RunwayAdapter

    class FakeRunway(AnimationProvider):
        name = "runway"
        provider_id = "runway"
        capabilities = ("video", "camera", "motion")

        def is_available(self):
            return True

        def plan(self, brief):
            return {"provider": "runway", "ok": True}

    register_animation_provider("runway", FakeRunway())
    try:
        assert get_animation_provider("runway").provider_id == "runway"
        assert provider_for_capability("camera", ["runway"]).provider_id == "runway"
    finally:
        register_animation_provider("runway", RunwayAdapter())


def test_package_emits_provider_instructions():
    package = build_animation_package(make_item())
    assert package["provider_instructions"]
    assert all("provider_id" in ins for ins in package["provider_instructions"])


# --------------------------------------------------------------- quality


def test_quality_validation_detects_empty_production():
    validation = validate_package({
        "timeline": {},
        "scene_timing": [],
        "camera_plan": {"shots": []},
        "character_motion": [],
        "facial_animation": [],
        "lip_sync_plan": [],
        "body_animation": [],
        "lighting_cues": [],
        "transitions": [],
        "visual_effects": [],
        "particle_effects": [],
        "motion_graphics": [],
        "audio_synchronization": [],
        "subtitle_timing": [],
        "export_metadata": {},
        "provider_instructions": [],
        "choreography": [],
    })
    assert validation["status"] == "FAILED"
    assert validation["blockers"]


def test_quality_validation_flags_invalid_transitions():
    package = build_animation_package(make_item())
    package["transitions"].append({
        "transition_id": "bad",
        "from_ref": "a",
        "to_ref": "b",
        "transition_type": "not_a_real_transition",
        "duration_sec": 0.1,
        "at_sec": 1.0,
        "params": {},
    })
    validation = validate_package(package)
    assert any("invalid transition" in w for w in validation["warnings"])


def test_transitions_use_supported_vocabulary():
    package = build_animation_package(make_item())
    for transition in package["transitions"]:
        assert transition["transition_type"] in TransitionType.ALL


# ---------------------------------------------------------- configuration


def test_configuration_overrides_fps_and_style():
    reset_animation_config()
    try:
        configure(fps=24, camera_style="anime", animation_style="anime", motion_intensity="extreme")
        package = build_animation_package(make_item())
        assert package["export_metadata"]["fps"] == 24
        assert package["export_metadata"]["camera_style"] == "anime"
        assert package["config"]["motion_intensity"] == "extreme"
    finally:
        reset_animation_config()


# --------------------------------------------------------------- batching


def test_batch_and_series_planning():
    items = [make_item(f"ep{i}") for i in range(1, 4)]
    batch = batch_plan(items)
    assert batch["items"] == 3
    assert batch["packages"]
    series = plan_series(items, series_id="ocean_saga")
    assert series["series_id"] == "ocean_saga"
    assert series["episodes"] == 3
    assert items[0]["series_id"] == "ocean_saga"
    manifest = prepare_render_batch(series["packages"])
    assert manifest["job_count"] == 3


# ------------------------------------------------------ failure handling


def test_broken_item_degrades_not_crash():
    # Non-dict scene_breakdown exercises fallback / guard paths.
    broken = {"project_id": "bad1", "scene_breakdown": "not-a-list"}
    updates = registry.get_engine("animation").run({
        "unified_packages": [broken, make_item("ok1")],
    })
    assert updates["animation_summary"]["packages"] == 2
    # At least the good item should plan successfully.
    statuses = [
        pkg.get("production_readiness", {}).get("status")
        for pkg in updates["animation_packages"]
    ]
    assert ReadinessStatus.READY in statuses or ReadinessStatus.NEEDS_REVIEW in statuses


# ------------------------------------------------------------ content package


def test_content_package_carries_animation_slot():
    package = ContentPackage(animation_package={"animation_package_version": "1.0"})
    data = package.to_dict()
    assert data["animation_package"] == {"animation_package_version": "1.0"}
    restored = ContentPackage.from_dict(data)
    assert restored.animation_package == {"animation_package_version": "1.0"}


# ------------------------------------------------------------- orchestrator


def test_animation_stage_runs_through_orchestrator():
    context = {"command": "probe", "unified_packages": [make_item("p1")]}
    report = Orchestrator().run_animation_stage(context)
    assert report.status == StageStatus.SUCCESS
    assert not report.errors
    assert context["animation_summary"]["status"] == "planned"
    assert context["unified_packages"][0]["animation_package"]["camera_plan"]["shots"]


def test_animation_stage_is_safe_without_input():
    context = {"command": "probe"}
    report = Orchestrator().run_animation_stage(context)
    assert report.status == StageStatus.SUCCESS
    assert not report.errors
    assert context["animation_summary"]["items"] == 0
    assert context["animation_packages"] == []


def test_effects_and_audio_sync_present_when_enabled():
    package = build_animation_package(make_item())
    # Fog/smoke/rain/energy hints in storyboard should yield effects.
    assert package["visual_effects"] or package["particle_effects"]
    assert package["audio_synchronization"]
    assert package["subtitle_timing"]
    assert package["lighting_cues"]
    assert package["motion_graphics"]
