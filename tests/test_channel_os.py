"""Tests for Multi-Channel Media OS — no new engines."""

from __future__ import annotations

from pathlib import Path

from services.channel_os.library import SUBFOLDERS, ensure_channel_tree, package_channel_production
from services.channel_os.production import install_sample_profiles, verify_channel_production
from services.channel_os.profiles import build_profile_from_template, list_template_ids
from services.channel_os.routing import profile_to_ops_kwargs, route_opportunity
from services.channel_os.store import get_profile, list_profiles, save_profile


def test_templates_cover_ten_example_brands():
    ids = list_template_ids()
    assert len(ids) >= 10
    assert "science_daily" in ids and "ai_explained" in ids and "space_explorer" in ids


def test_install_samples_and_route(tmp_path, monkeypatch):
    from services.channel_os import store as store_mod
    from services.channels import ChannelManager

    monkeypatch.setattr(store_mod, "ROOT", tmp_path)
    monkeypatch.setattr(store_mod, "PROFILES_DIR", tmp_path / "profiles")
    monkeypatch.setattr(store_mod, "DB_PATH", tmp_path / "CHANNEL_LIBRARY.db")
    monkeypatch.setattr(store_mod, "INDEX_JSON", tmp_path / "CHANNEL_PROFILES.json")
    monkeypatch.setattr(store_mod, "PRODUCTIONS_JSON", tmp_path / "CHANNEL_PRODUCTIONS.json")
    # Isolate legacy channel manager
    monkeypatch.setattr(store_mod, "get_channel_manager", lambda: ChannelManager(str(tmp_path / "legacy")))

    installed = install_sample_profiles()
    assert len(installed) == 3
    assert get_profile("science_daily") is not None
    assert len(list_profiles()) == 3

    routed = route_opportunity(
        {"topic": "How Neural Networks Learn", "category": "artificial_intelligence", "platform": "youtube_shorts"}
    )
    assert routed["ok"]
    assert routed["selected_channel_id"] == "ai_explained"

    space = route_opportunity({"topic": "Why Saturn Has Rings", "category": "astronomy"})
    assert space["selected_channel_id"] == "space_explorer"


def test_profile_maps_to_ops_kwargs():
    profile = build_profile_from_template("science_daily")
    kwargs = profile_to_ops_kwargs(profile, topic="Why Ice Floats")
    assert kwargs["narrator"] == "science_educator"
    assert kwargs["voice"] == "science_educator"
    assert kwargs["constraints"]["brand_name"] == "Science Daily"
    assert kwargs["constraints"]["publishing_enabled"] is False
    assert kwargs["context"]["channel_profile"]["visual_style"] == profile["visual_style"]
    assert kwargs["context"]["world_preferences"]["style"] == "reality_first"


def test_package_and_verify_library(tmp_path, monkeypatch):
    from services.channel_os import library as lib

    monkeypatch.setattr(lib, "resolve_videos_root", lambda: tmp_path / "Videos")

    profile = build_profile_from_template("space_explorer")
    save_profile(profile, sync_legacy=False)

    ops = {
        "production_id": "ops_channel_test",
        "success": True,
        "brief": {
            "topic": "Why Saturn Has Rings",
            "narrator": "documentary",
            "voice": "documentary",
            "style": "educational",
            "domain": "astronomy",
        },
        "report": {"topic": "Why Saturn Has Rings", "creative_excellence_score": 82},
        "status": {"success": True, "elapsed_ms": 1000},
        "context": {
            "brand_name": "Space Explorer",
            "channel_id": "space_explorer",
            "visual_style": profile["visual_style"],
            "world_preferences": profile["world_preferences"],
            "channel_profile": {
                "brand_name": "Space Explorer",
                "narrator_profile": "documentary",
                "voice_profile": "documentary",
                "visual_style": profile["visual_style"],
                "world_preferences": profile["world_preferences"],
            },
            "ops_constraints": {
                "brand_name": "Space Explorer",
                "channel_id": "space_explorer",
                "visual_style": profile["visual_style"],
                "world_preferences": profile["world_preferences"],
            },
        },
    }
    packaged = package_channel_production(ops, profile=profile, category="astronomy")
    root = Path(packaged["project_root"])
    assert root.is_dir()
    for sub in SUBFOLDERS:
        assert (root / sub).is_dir()
    assert Path(packaged["production_report"]).is_file()
    assert Path(packaged["branding_report"]).is_file()

    checks = verify_channel_production(ops, profile, packaged)
    assert checks["all_passed"] is True
    assert checks["correct_branding"]
    assert checks["correct_voice"]
    assert checks["correct_file_organization"]
