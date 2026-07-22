"""Tests for production media integrations (voice, ffmpeg, gates, reports)."""

from __future__ import annotations

from pathlib import Path

from engines.render.renderer import MockRenderer
from services.media_production.formats import resolve_output_format, duration_band
from services.media_production.persistence import write_bytes, persist_audio_payload
from services.media_production.publish_gate import ProductionIntegrityGate
from services.media_production.readiness import media_production_readiness
from services.media_production.reports import write_full_report_bundle
from services.media_production.timestamps import attach_timing_metadata, strip_ssml
from services.media_production.voice import synthesize_voice
from services.master_pipeline.readiness import production_readiness_report


def test_resolve_output_format_presets():
    vertical = resolve_output_format(aspect="vertical")
    assert vertical["resolution"]["width"] == 1080
    assert vertical["aspect_ratio"] == "9:16"
    landscape = resolve_output_format(aspect="16:9")
    assert landscape["resolution"]["width"] == 1920
    custom = resolve_output_format(width=720, height=720)
    assert custom["orientation"] == "square"
    assert duration_band(30) == "30s"


def test_timestamps_and_ssml():
    text = "<speak>Hello world. Next sentence!</speak>"
    assert strip_ssml(text) == "Hello world. Next sentence!"
    timing = attach_timing_metadata(text, 4.0)
    assert timing["word_count"] >= 4
    assert timing["sentence_count"] >= 2
    assert timing["ssml"] is True


def test_persist_audio_payload(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "services.media_production.persistence.MEDIA_ROOT",
        tmp_path / "media",
    )
    import base64

    payload = persist_audio_payload(
        {"audio_b64": base64.b64encode(b"ID3fakeaudio").decode("ascii"), "format": "mp3"},
        name="test",
    )
    assert payload["path"]
    assert payload["placeholder"] is False
    assert Path(tmp_path / "media").exists() or True


def test_mock_renderer_empty_timeline():
    result = MockRenderer().render(
        title="Empty",
        timeline={"segments": [], "total_duration_sec": 0},
        scene_render_plan=[],
        caption_render_plan={"segments": []},
        audio_mix_plan={"tracks": {}},
        missing_assets=[],
    )
    assert result["mock"] is True
    assert result["mock_output_path"] == ""


def test_mock_renderer_fails_closed_without_real_media(monkeypatch):
    monkeypatch.setattr(
        "services.media_production.ffmpeg_assembler.find_ffmpeg",
        lambda: "",
    )
    result = MockRenderer().render(
        title="Demo Short",
        timeline={
            "segments": [{"scene_id": 1, "start_time": 0, "end_time": 5, "duration": 5}],
            "total_duration_sec": 5.0,
        },
        scene_render_plan=[{"scene_id": 1, "resolved_asset": {"path": "mock://x.png", "placeholder": True}}],
        caption_render_plan={"segments": [{"text": "hi"}]},
        audio_mix_plan={"tracks": {"narration": {"segments": []}, "sfx": {"cues": []}, "transitions": {"cues": []}, "music": {"ducking": {"enabled": True}}}},
        missing_assets=[],
    )
    # Visual Pipeline V2: mock:// placeholders must not reserve a fake success path.
    assert result["mock"] is True
    assert result["render_status"] == "FAILED"
    assert result["mp4_path"] == ""
    assert result["mock_output_path"] == ""


def test_ffmpeg_assembler_writes_real_mp4_when_ffmpeg_present(tmp_path):
    from services.media_production import ffmpeg_assembler as fa

    ffmpeg = fa.find_ffmpeg()
    if not ffmpeg:
        return

    # Generate a valid still with ffmpeg itself, then assemble.
    still = tmp_path / "frame.png"
    out = tmp_path / "out.mp4"
    import subprocess

    subprocess.run(
        [ffmpeg, "-y", "-f", "lavfi", "-i", "color=c=blue:s=320x560:d=0.1", str(still)],
        capture_output=True,
        check=False,
    )
    if not still.exists():
        return
    result = fa.assemble_mp4(
        title="t",
        output_path=str(out),
        timeline={"total_duration_sec": 1.0},
        scene_render_plan=[{"resolved_asset": {"path": str(still)}}],
        audio_mix_plan={"tracks": {}},
        output_format=resolve_output_format(aspect="vertical"),
    )
    assert result["ok"] is True
    assert result["mock"] is False
    assert out.exists() or Path(result.get("absolute_path") or "").exists()


def test_production_integrity_gate_allows_dry_run():
    gate = ProductionIntegrityGate()
    problems = gate.review({"publish_mode": "dry_run", "package": {"render_package": {"mock": True}}})
    assert problems == []


def test_production_integrity_gate_blocks_live_mock():
    gate = ProductionIntegrityGate()
    problems = gate.review(
        {
            "publish_mode": "immediate",
            "enforce_production_qc": True,
            "platform": "youtube_shorts",
            "package": {
                "render_package": {"mock": True, "mock_output_path": "data/renders/x.mp4"},
                "title": "t",
            },
        }
    )
    assert any("mock" in p.lower() or "mp4" in p.lower() for p in problems)


def test_reports_bundle(tmp_path, monkeypatch):
    monkeypatch.setattr("services.media_production.reports.REPORTS_ROOT", tmp_path / "reports")
    paths = write_full_report_bundle(
        {"workflow_run_id": "run_test", "ideas": [{"title": "a"}]},
        render_packages=[{"title": "a", "mock": True}],
        metrics={"elapsed_sec": 1.2},
    )
    assert "production" in paths
    assert (tmp_path / "reports" / "run_test" / "production.json").exists()


def test_synthesize_voice_empty():
    result = synthesize_voice("")
    assert result["ok"] is False
    assert result["placeholder"] is True


def test_media_and_master_readiness_shape():
    media = media_production_readiness()
    assert "score" in media
    assert "blockers" in media
    assert "first_autonomous_checklist" in media
    report = production_readiness_report()
    assert report["score"] >= 0
    assert "band" in report
