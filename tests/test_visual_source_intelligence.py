"""Visual Source Intelligence — select strongest source before render."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from services.visual_source_intelligence import (
    attach_visual_source_package,
    build_visual_source_package,
    choose_source,
    creative_review,
)
from services.visual_source_intelligence.intent import build_scene_intent
from services.visual_source_intelligence.select import apply_choice_to_scene


def test_hook_prefers_motion_over_static():
    scene = {
        "scene_number": 1,
        "purpose": "hook",
        "narration": "These colors could determine whether firefighters save your house.",
        "visual_description": "Three fire hydrants different colors",
        "ai_video_prompt": "cinematic suburban street three hydrants",
        "ai_image_prompt": "still hydrants",
        "stock_footage_query": "fire hydrant suburban street",
    }
    choice = choose_source(scene, topic="Why Fire Hydrants Are Different Colors", scene_index=0)
    assert choice["tier"] <= 4
    assert choice["asset_type"] in {"stock_footage", "ai_video", "ai_image"}
    assert choice["selected"]["source_key"] in {
        "stock_video",
        "ai_video",
        "animated_diagram",
        "ai_still_motion",
        "static_image",
    }
    # Hook should not default to static when AI video is available
    assert choice["selected"]["source_key"] != "static_image"


def test_diagram_beat_prefers_animated_diagram():
    scene = {
        "scene_number": 3,
        "purpose": "story_beat",
        "narration": "Each color indicates a flow rating firefighters read at a glance.",
        "visual_description": "Color legend diagram for hydrant ratings",
        "ai_image_prompt": "diagram",
        "stock_footage_query": "fire hydrant colors",
    }
    choice = choose_source(scene, topic="Fire hydrant colors", scene_index=2)
    assert choice["selected"]["source_key"] == "animated_diagram"
    assert choice["tier"] == 3
    applied = apply_choice_to_scene(scene, choice)
    assert applied.get("annotation_plan")
    assert applied.get("motion_plan")


def test_build_package_attaches_requests_and_review(tmp_path):
    plate = tmp_path / "lib.png"
    Image.new("RGB", (1080, 1920), (30, 120, 60)).save(plate)

    candidate = {
        "topic": "Why Fire Hydrants Are Different Colors",
        "visual_package": {
            "scenes": [
                {
                    "scene_number": 1,
                    "purpose": "hook",
                    "narration": "These colors could determine whether firefighters save your house.",
                    "stock_footage_query": "fire hydrant colors street",
                    "ai_video_prompt": "drone over hydrants",
                    "ai_image_prompt": "hydrants",
                },
                {
                    "scene_number": 2,
                    "purpose": "story_beat",
                    "narration": "A map of the water main shows why two nearby hydrants can differ.",
                    "visual_description": "utility map overlay",
                    "stock_footage_query": "water main map",
                },
                {
                    "scene_number": 3,
                    "purpose": "payoff",
                    "narration": "Flow rate matters when seconds decide if a house is saved.",
                    "ai_video_prompt": "water flow visualization",
                },
            ]
        },
        "visual_assets": [
            {
                "asset_id": "hydrant_still",
                "path": str(plate),
                "kind": "image",
                "topic": "fire hydrant",
            }
        ],
    }
    pkg = build_visual_source_package(candidate, topic=candidate["topic"], write=True)
    assert pkg["package_type"] == "VISUAL_SOURCE_INTELLIGENCE"
    assert pkg["scene_count"] == 3
    assert Path(pkg["path"]).is_file()
    assert pkg["asset_requests"]
    assert pkg["creative_review"]["answers"]["weakest_scene"] is not None
    # Camera motions should diversify across scenes
    motions = {d["camera_motion"] for d in pkg["scene_decisions"]}
    assert len(motions) >= 2

    attached = attach_visual_source_package(candidate, pkg)
    assert attached["prefer_vsi_asset_requests"] is True
    assert attached["visual_package"]["scenes"][0].get("vsi_source")
    assert attached["visual_package"]["asset_requests"]

    review = creative_review(attached, package=pkg)
    assert "every_scene_explains_narration" in review["answers"]
    assert "markdown" in review


def test_intent_answers_planning_questions():
    scene = {
        "purpose": "hook",
        "narration": "These colors could determine whether firefighters save your house.",
        "subject": "fire hydrants",
    }
    intent = build_scene_intent(scene, topic="Hydrant colors")
    assert intent["viewer_understanding"]
    assert intent["ideal_visual"]
    assert intent["prefers_motion"] is True


def test_stock_fulfiller_honors_resolved_path(tmp_path):
    from engines.render.assets import StockFootageFulfiller

    plate = tmp_path / "clip_proxy.png"
    Image.new("RGB", (640, 360), (10, 10, 10)).save(plate)
    # Use a tiny valid PNG size >= 500 bytes
    Image.new("RGB", (1280, 720), (200, 40, 40)).save(plate)
    assert plate.stat().st_size >= 500

    asset = StockFootageFulfiller().fulfil(
        {
            "scene_number": 1,
            "query": "hydrants",
            "resolved_path": str(plate),
            "vsi_fallback_reason": "library hit",
        }
    )
    assert asset["path"] == str(plate.resolve())
    assert asset.get("placeholder") is False
    assert asset.get("provider") == "visual_source_intelligence"
