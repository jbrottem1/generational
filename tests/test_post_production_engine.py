"""Tests for the Post-Production & Intelligent Editing Engine (Agent 17).

Proves: timeline generation, caption generation, audio synchronization,
color workflows, platform exports, quality validation, pipeline integration,
configuration, failure handling, and the engine contract.
"""

from __future__ import annotations

import engines  # noqa: F401 - importing registers all engines
from engines import registry
from engines.contracts import ContractEngine
from providers.post_production import (
    MockPostProductionProvider,
    default_post_production_provider,
    provider_catalog,
)
from services.orchestrator import ContentPackage, Orchestrator, StageStatus
from services.post_production import (
    POST_PRODUCTION_PACKAGE_FIELDS,
    build_post_production_package,
    configure,
    reset_post_production_config,
)
from services.post_production.editing import compute_scene_cuts
from services.post_production.models import EditStatus, PackageReadiness
from services.post_production.package import collect_post_production_items, post_produce_items
from services.post_production.quality import validate_post_production


def make_render_package():
    """Minimal render package for post-production testing."""
    return {
        "render_package_version": "2.0",
        "title": "Ocean Mystery",
        "duration_sec": 30.0,
        "timeline": {
            "total_duration_sec": 30.0,
            "fps": 30,
            "segments": [
                {
                    "scene_id": 1,
                    "start_time": 0.0,
                    "end_time": 10.0,
                    "duration": 10.0,
                    "narration_reference": "narr_1",
                    "visual_reference": "vis_1",
                    "caption_reference": "cap_1",
                    "audio_reference": "aud_1",
                    "transition_in": "cut",
                    "transition_out": "crossfade",
                    "motion_effect": "zoom",
                    "render_status": "planned",
                },
                {
                    "scene_id": 2,
                    "start_time": 10.0,
                    "end_time": 20.0,
                    "duration": 10.0,
                    "narration_reference": "narr_2",
                    "visual_reference": "vis_2",
                    "caption_reference": "cap_2",
                    "audio_reference": "aud_2",
                    "transition_in": "crossfade",
                    "transition_out": "cut",
                    "motion_effect": "static",
                    "render_status": "planned",
                },
                {
                    "scene_id": 3,
                    "start_time": 20.0,
                    "end_time": 30.0,
                    "duration": 10.0,
                    "narration_reference": "narr_3",
                    "visual_reference": "vis_3",
                    "caption_reference": "cap_3",
                    "audio_reference": "aud_3",
                    "transition_in": "cut",
                    "transition_out": "cut",
                    "motion_effect": "zoom",
                    "render_status": "planned",
                },
            ],
        },
        "caption_render_plan": {
            "mode": "word_by_word",
            "cues": [
                {"cue_id": "c1", "start_time": 0.0, "end_time": 3.0, "text": "The ocean vanishes", "emphasis_words": ["ocean"]},
                {"cue_id": "c2", "start_time": 3.0, "end_time": 6.0, "text": "overnight", "emphasis_words": []},
                {"cue_id": "c3", "start_time": 10.0, "end_time": 15.0, "text": "Scientists discover a rift", "emphasis_words": ["Scientists"]},
            ],
        },
        "audio_mix_plan": {
            "track_levels_db": {"narration": -3.0, "music": -18.0, "sfx": -10.0},
            "ducking": {"enabled": True, "trigger": "narration", "duck_to_db": -26.0},
            "loudness_target": {"integrated_lufs": -14.0, "true_peak_db": -1.0},
        },
        "transition_plan": {
            "transitions": [
                {"type": "crossfade", "duration_sec": 0.3},
                {"type": "cut", "duration_sec": 0.0},
            ],
        },
        "motion_plan": {"effects": []},
        "validation": {"problems": []},
    }


def make_item(project_id="proj_pp"):
    return {
        "project_id": project_id,
        "title": "Ocean Mystery",
        "topic": "deep sea creatures",
        "brand": "Generational",
        "platforms": ["youtube_shorts"],
        "render_package": make_render_package(),
        "audio_package": {
            "voice_style": {"name": "narrator"},
            "scene_cues": [
                {"scene_number": 1, "energy": 75, "purpose": "hook"},
                {"scene_number": 2, "energy": 60, "purpose": "story_beat"},
                {"scene_number": 3, "energy": 80, "purpose": "payoff"},
            ],
        },
        "creative_package": {
            "creative_blueprint": {"color_palette": {"primary": "#003366"}, "visual_style": "cinematic"},
        },
        "asset_package": {"asset_package_version": "1.1", "assets": []},
        "seo_package": {"title": "Ocean Mystery", "description": "What if the ocean disappeared?", "hashtags": ["#ocean"]},
    }


# --------------------------------------------------------- engine contract

def test_post_production_is_a_live_contract_engine():
    engine = registry.get_engine("post_production")
    assert isinstance(engine, ContractEngine)
    assert engine.is_ready() is True
    diag = engine.diagnostics()
    assert diag["engine_id"] == "post_production"
    assert "unified_packages" in diag["input_contract"]
    assert "post_production_summary" in diag["output_contract"]
    assert "post_production_packages" in diag["output_contract"]
    assert "render" in diag["dependencies"]


def test_post_production_package_fields_contract():
    package = build_post_production_package(make_item())
    for field in POST_PRODUCTION_PACKAGE_FIELDS:
        assert field in package, f"Missing field: {field}"


# --------------------------------------------------------- timeline generation

def test_edit_timeline_has_tracks_and_clips():
    package = build_post_production_package(make_item())
    timeline = package["edit_timeline"]
    assert timeline["total_duration_sec"] == 30.0
    assert timeline["fps"] == 30
    assert len(timeline["tracks"]) >= 5
    video_track = next(t for t in timeline["tracks"] if t["track_type"] == "video")
    assert len(video_track["clips"]) == 3
    assert timeline["markers"]


def test_scene_cuts_applied():
    package = build_post_production_package(make_item())
    cuts = package["scene_cuts"]
    assert len(cuts) == 3
    for cut in cuts:
        assert cut["edited_end"] > cut["edited_start"]
        assert cut["cut_type"] in ("trim", "hold", "jump_cut", "speed_ramp", "freeze")
        assert 0 <= cut["pacing_score"] <= 100


def test_retention_editing_applies_jump_cuts():
    configure(editing_style="retention", enable_jump_cuts=True)
    try:
        cuts = compute_scene_cuts(make_render_package(), make_item()["audio_package"])
        jump_cuts = [c for c in cuts if c["cut_type"] == "jump_cut"]
        assert jump_cuts
    finally:
        reset_post_production_config()


# --------------------------------------------------------- audio synchronization

def test_audio_mix_finalized_from_render_plan():
    package = build_post_production_package(make_item())
    audio = package["audio_mix"]
    assert audio["source_plan"] == "render.audio_mix_plan"
    assert audio["dialogue_level_db"] == -3.0
    assert audio["ducking"]["enabled"] is True
    assert audio["normalization"]["enabled"] is True
    assert audio["effects"]["compression"]["enabled"] is True
    assert audio["platform_targets"]


def test_music_ducking_can_be_disabled():
    configure(enable_music_ducking=False)
    try:
        package = build_post_production_package(make_item())
        assert package["audio_mix"]["ducking"]["enabled"] is False
    finally:
        reset_post_production_config()


# --------------------------------------------------------- caption generation

def test_caption_timeline_from_render_plan():
    package = build_post_production_package(make_item())
    captions = package["caption_timeline"]
    assert captions["mode"] == "word_by_word"
    assert len(captions["entries"]) == 3
    assert captions["burn_in"] is True
    assert "srt" in captions["export_formats"]


def test_subtitle_styling_has_theme():
    package = build_post_production_package(make_item())
    styling = package["subtitle_styling"]
    assert styling["preset"] == "bold_pop"
    assert styling["font"]
    assert styling["safe_area"]


def test_caption_theme_configurable():
    configure(caption_theme="karaoke_highlight")
    try:
        package = build_post_production_package(make_item())
        assert package["caption_timeline"]["theme"] == "karaoke_highlight"
        assert package["subtitle_styling"]["preset"] == "karaoke_highlight"
    finally:
        reset_post_production_config()


# --------------------------------------------------------- color workflows

def test_color_grading_from_creative_package():
    package = build_post_production_package(make_item())
    color = package["color_grading"]
    assert color["preset"] == "vibrant"
    assert color["corrections"]
    assert len(color["corrections"]) == 3


def test_color_preset_configurable():
    configure(color_preset="cinematic_warm")
    try:
        package = build_post_production_package(make_item())
        assert package["color_grading"]["preset"] == "cinematic_warm"
    finally:
        reset_post_production_config()


# --------------------------------------------------------- effects and motion graphics

def test_transitions_planned():
    package = build_post_production_package(make_item())
    assert len(package["transitions"]) == 3


def test_motion_graphics_include_intro_outro_cta():
    package = build_post_production_package(make_item())
    types = {g["graphic_type"] for g in package["motion_graphics"]}
    assert "intro" in types
    assert "outro" in types
    assert "cta" in types
    assert "watermark" in types


def test_motion_graphics_can_be_disabled():
    configure(enable_motion_graphics=False)
    try:
        package = build_post_production_package(make_item())
        assert package["motion_graphics"] == []
    finally:
        reset_post_production_config()


# --------------------------------------------------------- platform exports

def test_platform_exports_for_target_platforms():
    configure(target_platforms=["youtube_shorts", "tiktok"])
    try:
        package = build_post_production_package(make_item())
        exports = package["platform_exports"]
        assert len(exports) == 2
        platforms = {e["platform"] for e in exports}
        assert "youtube_shorts" in platforms
        assert "tiktok" in platforms
        for export in exports:
            assert export["safe_zones"]
            assert export["caption_placement"]
    finally:
        reset_post_production_config()


def test_export_presets_include_resolutions():
    package = build_post_production_package(make_item())
    presets = package["export_presets"]
    preset_ids = {p["preset_id"] for p in presets}
    assert "1080p_vertical" in preset_ids
    assert "1080p_horizontal" in preset_ids
    assert "4k_horizontal" in preset_ids
    assert "archive_master" in preset_ids
    assert "proxy_720p" in preset_ids


# --------------------------------------------------------- quality validation

def test_quality_report_passes_for_valid_package():
    package = build_post_production_package(make_item())
    report = package["quality_report"]
    assert report["status"] in ("pass", "warning")
    assert report["score"] >= 60
    assert report["ready_for_export"] is True
    assert report["checks_passed"] > 0


def test_quality_detects_invalid_cuts():
    package = build_post_production_package(make_item())
    package["scene_cuts"] = [{
        "scene_id": 1, "original_start": 0, "original_end": 10,
        "edited_start": 5, "edited_end": 3, "cut_type": "trim",
        "reason": "test", "pacing_score": 0,
    }]
    report = validate_post_production(package, make_render_package())
    assert report["status"] == "fail"
    assert any(i["category"] == "cut" for i in report["issues"])


def test_production_readiness_scoring():
    package = build_post_production_package(make_item())
    readiness = package["production_readiness"]
    assert readiness["status"] in PackageReadiness.ALL
    assert readiness["score"] >= 60


# --------------------------------------------------------- provider abstraction

def test_mock_provider_assembles_and_exports():
    provider = MockPostProductionProvider()
    package = build_post_production_package(make_item())
    assembled = provider.assemble(package)
    assert assembled["status"] == "assembled"
    exported = provider.export(package, "1080p_vertical")
    assert exported["status"] == "exported"
    validated = provider.validate(package)
    assert validated["score"] >= 0


def test_provider_catalog():
    catalog = provider_catalog()
    assert any(p["name"] == "mock" for p in catalog)


def test_default_provider():
    assert default_post_production_provider().name == "mock"


# --------------------------------------------------------- pipeline integration

def test_engine_writes_only_post_production_package_slot():
    item = make_item()
    context = {"unified_packages": [item]}
    registry.get_engine("post_production").run(context)
    assert item["post_production_package"]["edit_timeline"]
    assert "render_package" in item  # not mutated


def test_engine_handles_empty_context():
    updates = registry.get_engine("post_production").run({"command": "probe"})
    assert updates["post_production_summary"]["status"] == EditStatus.SKIPPED
    assert updates["post_production_summary"]["items"] == 0


def test_engine_produces_summary():
    updates = registry.get_engine("post_production").run({"unified_packages": [make_item()]})
    summary = updates["post_production_summary"]
    assert summary["status"] in (EditStatus.SUCCESS, EditStatus.WARNING)
    assert summary["packages"] == 1
    assert summary["average_readiness"] >= 0


def test_post_production_stage_runs_through_orchestrator():
    context = {"unified_packages": [make_item()]}
    report = Orchestrator().run_post_production_stage(context)
    assert report.status in (StageStatus.SUCCESS, StageStatus.WARNING)
    assert context["post_production_summary"]["packages"] == 1
    assert context["unified_packages"][0]["post_production_package"]["edit_timeline"]


def test_content_package_round_trip_with_post_production():
    package = ContentPackage(post_production_package={"post_production_package_version": "1.0"})
    data = package.to_dict()
    assert data["post_production_package"] == {"post_production_package_version": "1.0"}
    restored = ContentPackage.from_dict(data)
    assert restored.post_production_package == {"post_production_package_version": "1.0"}


def test_collect_post_production_items_prefers_unified_packages():
    items, key = collect_post_production_items({"unified_packages": [make_item()]})
    assert len(items) == 1
    assert key == "unified_packages"


def test_post_produce_items_batch():
    items = [make_item("p1"), make_item("p2")]
    packages = post_produce_items(items)
    assert len(packages) == 2
    assert all(i["post_production_package"] for i in items)


# --------------------------------------------------------- configuration

def test_configuration_changes_editing_behavior():
    configure(editing_style="educational", pacing_profile="conservative")
    try:
        package = build_post_production_package(make_item())
        assert package["scene_cuts"]
    finally:
        reset_post_production_config()


def test_provider_instructions_present():
    package = build_post_production_package(make_item())
    instructions = package["provider_instructions"]
    assert len(instructions) >= 2
    providers = {i["provider"] for i in instructions}
    assert "mock" in providers
    assert "ffmpeg" in providers


def test_publishing_metadata_from_seo():
    package = build_post_production_package(make_item())
    meta = package["publishing_metadata"]
    assert meta["title"] == "Ocean Mystery"
    assert meta["tags"] == ["#ocean"]
    assert meta["end_screen"]["enabled"] is True
