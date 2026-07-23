"""Tests for cinematic visual storytelling upgrades."""

from __future__ import annotations

from pathlib import Path

from services.asset_production.visual_story import build_visual_story_plans, enrich_scene_story_plan, MEDIA_HIERARCHY
from services.asset_production.cinematic_fallback import generate_cinematic_fallback_still
from services.media_production.ffmpeg_assembler import assemble_mp4, ffmpeg_available


def test_media_hierarchy_complete():
    assert "ai_cinematic_artwork" in MEDIA_HIERARCHY
    assert MEDIA_HIERARCHY[-1] == "cinematic_fallback_still"


def test_enrich_scene_never_static_default():
    scene = enrich_scene_story_plan(
        {
            "scene_number": 2,
            "purpose": "story_beat",
            "narration": "DNA folds inside every cell.",
            "length_sec": 4,
        },
        niche="science",
        title="DNA",
        index=1,
    )
    assert scene["camera_motion"] != "static"
    assert scene["visual_story_plan"]["media_type"]
    assert "cinematic" in scene["ai_image_prompt"].lower() or "scientific" in scene["ai_image_prompt"].lower()
    assert scene["ai_image_prompt"] != scene["narration"]


def test_build_visual_story_plans_from_segments():
    asset = {
        "title": "How CRISPR Works",
        "niche": "science",
        "video_script": {
            "segments": [
                {"segment_type": "hook", "start_time": 0, "end_time": 3, "voiceover": "DNA can be edited."},
                {"segment_type": "evidence", "start_time": 3, "end_time": 8, "voiceover": "Cas9 cuts with a guide."},
                {"segment_type": "payoff", "start_time": 8, "end_time": 12, "voiceover": "That is CRISPR."},
            ]
        },
    }
    scenes = build_visual_story_plans(asset, niche="science")
    assert len(scenes) >= 3
    assert all(s.get("visual_story_plan") for s in scenes)
    assert all(s.get("camera_motion") for s in scenes)


def test_cinematic_fallback_writes_real_png(tmp_path):
    if not ffmpeg_available():
        return
    out = tmp_path / "fallback.png"
    result = generate_cinematic_fallback_still(
        output_path=out,
        title="CRISPR",
        overlay="Gene Edit",
        scene_number=1,
    )
    assert result.get("placeholder") is False
    assert Path(result["path"]).exists()
    assert Path(result["path"]).stat().st_size > 500


def test_assemble_rejects_empty_visuals(tmp_path):
    if not ffmpeg_available():
        return
    out = tmp_path / "empty.mp4"
    result = assemble_mp4(
        title="Empty",
        output_path=str(out),
        timeline={"total_duration_sec": 3},
        scene_render_plan=[{"scene_id": 1, "resolved_asset": {"path": "mock://x.png", "placeholder": True}}],
        audio_mix_plan={"tracks": {}},
        allow_color_bed=False,
    )
    assert result["ok"] is False
    assert result.get("visual_count", 0) == 0


def test_assemble_multi_scene_with_motion(tmp_path):
    if not ffmpeg_available():
        return
    # Create two fallback stills then assemble
    img1 = tmp_path / "a.png"
    img2 = tmp_path / "b.png"
    generate_cinematic_fallback_still(output_path=img1, title="One", overlay="Scene One", scene_number=1)
    generate_cinematic_fallback_still(output_path=img2, title="Two", overlay="Scene Two", scene_number=2)
    out = tmp_path / "multi.mp4"
    result = assemble_mp4(
        title="Multi",
        output_path=str(out),
        timeline={"total_duration_sec": 4},
        scene_render_plan=[
            {
                "scene_id": 1,
                "duration_sec": 2,
                "resolved_asset": {"path": str(img1), "placeholder": False},
                "effect": {
                    "effect": "ken_burns",
                    "zoom": {"start_scale": 1.0, "end_scale": 1.1},
                    "pan": {"direction": "right", "amount_pct": 8},
                },
            },
            {
                "scene_id": 2,
                "duration_sec": 2,
                "resolved_asset": {"path": str(img2), "placeholder": False},
                "effect": {
                    "effect": "slow_zoom_in",
                    "zoom": {"start_scale": 1.0, "end_scale": 1.12},
                    "pan": {"direction": "none", "amount_pct": 0},
                },
            },
        ],
        audio_mix_plan={"tracks": {}},
        allow_color_bed=False,
    )
    assert result["ok"] is True
    assert result["visual_count"] == 2
    assert out.exists() or Path(result.get("absolute_path") or "").exists()
    assert any("multi_scene" in str(x) or "single_scene" in str(x) or "scene→clip" in str(x) for x in result.get("log") or [])
