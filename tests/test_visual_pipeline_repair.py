"""Visual pipeline V2 — fail-closed media contract tests."""

from __future__ import annotations

from pathlib import Path

from engines.render.assets import AIImageFulfiller, AssetResolver
from engines.render.renderer import MockRenderer
from services.media_production.ffmpeg_assembler import assemble_mp4
from services.media_production.formats import resolve_output_format
from services.media_production.visual_qa import validate_scene_visuals, write_visual_pipeline_report


def test_runtime_demo_image_is_not_treated_as_success(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "services.media_production.persistence.MEDIA_ROOT",
        tmp_path / "media",
    )

    class FakeRuntime:
        def generate_image(self, payload, **kwargs):
            from services.provider_runtime.models import ProviderResponse

            return ProviderResponse(
                success=True,
                operation="generate_image",
                provider="demo",
                demo_mode=True,
                data={"placeholder": True, "path": "runtime://image/demo"},
            )

    monkeypatch.setattr(
        "services.provider_runtime.engine_api.get_provider_runtime",
        lambda: FakeRuntime(),
    )
    from services.provider_runtime.engine_api import runtime_generate_image

    asset = runtime_generate_image("octopus with three hearts")
    assert asset["placeholder"] is True
    assert asset["status"] == "failed"
    assert not str(asset.get("path") or "").startswith("runtime://")


def test_asset_resolver_uses_photographic_fallback(monkeypatch, tmp_path):
    still = tmp_path / "octopus.jpg"
    still.write_bytes(b"real-photo-bytes" * 200)

    monkeypatch.setattr(
        "engines.render.assets.runtime_generate_image",
        lambda prompt, metadata=None: {"path": "", "placeholder": True, "status": "failed", "provider": "demo"},
    )
    monkeypatch.setattr(
        "services.media_production.photographic_fallback.fetch_photographic_fallback",
        lambda prompt, name="scene", keywords=None: {
            "path": str(still),
            "provider": "wikimedia_curated",
            "placeholder": False,
            "approved_fallback_visual": True,
            "status": "approved_fallback",
        },
    )
    asset = AIImageFulfiller().fulfil(
        {"prompt": "Why octopuses have three hearts", "scene_number": 1, "duration_sec": 3}
    )
    assert asset["placeholder"] is False
    assert Path(asset["path"]).exists()

    resolved = AssetResolver().resolve(
        [{"source": "ai_image", "prompt": "octopus hearts", "scene_number": 1, "duration_sec": 3}]
    )
    assert resolved["missing_assets"] == []
    assert resolved["assets"][0]["placeholder"] is False


def test_visual_qa_fails_on_runtime_placeholder():
    qa = validate_scene_visuals(
        [
            {
                "scene_number": 1,
                "narration": "Octopuses have three hearts.",
                "resolved_asset": {"path": "runtime://image/demo", "placeholder": True, "provider": "demo"},
            }
        ]
    )
    assert qa["ok"] is False
    assert qa["failed"] == 1


def test_renderer_refuses_color_bed_without_media(tmp_path):
    result = MockRenderer().render(
        title="Blank Trap",
        timeline={
            "segments": [{"scene_id": 1, "start_time": 0, "end_time": 3, "duration": 3}],
            "total_duration_sec": 3.0,
        },
        scene_render_plan=[
            {
                "scene_id": 1,
                "narration": "No media here",
                "resolved_asset": {"path": "runtime://image/demo", "placeholder": True},
            }
        ],
        caption_render_plan={"segments": [{"text": "hi"}]},
        audio_mix_plan={"tracks": {"narration": {"segments": []}, "sfx": {"cues": []}, "transitions": {"cues": []}, "music": {"ducking": {"enabled": False}}}},
        missing_assets=[{"scene_number": 1, "source": "ai_image", "reason": "demo"}],
    )
    assert result["render_status"] == "FAILED"
    assert result["mp4_path"] == ""
    assert result["assembly"].get("rejected_color_bed") is True


def test_assembler_rejects_color_bed_by_default(tmp_path):
    out = tmp_path / "should_not_exist.mp4"
    result = assemble_mp4(
        title="t",
        output_path=str(out),
        timeline={"total_duration_sec": 2.0},
        scene_render_plan=[{"resolved_asset": {"path": "runtime://image/demo", "placeholder": True}}],
        audio_mix_plan={"tracks": {}},
        output_format=resolve_output_format(aspect="vertical"),
        allow_color_bed=False,
    )
    assert result["ok"] is False
    assert "refusing color-bed" in (result.get("error") or "")


def test_visual_pipeline_report_written(tmp_path):
    still = tmp_path / "ok.png"
    still.write_bytes(b"x" * 2048)
    qa = validate_scene_visuals(
        [
            {
                "scene_number": 1,
                "narration": "Hook",
                "visual_description": "octopus",
                "resolved_asset": {
                    "path": str(still),
                    "provider": "test",
                    "placeholder": False,
                    "width": 1080,
                    "height": 1920,
                },
            }
        ]
    )
    report = write_visual_pipeline_report(qa, output_path=tmp_path / "VISUAL_PIPELINE_REPORT.md", title="Octopus")
    text = Path(report).read_text(encoding="utf-8")
    assert "PASS" in text
    assert "octopus" in text.lower() or "Octopus" in text
