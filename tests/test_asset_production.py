"""Tests for the automatic asset production executor."""

from __future__ import annotations

from core.script_models import PIPELINE_STAGE_KEYS, VideoScript, apply_script_to_asset
from services.asset_production.executor import run_asset_production, _scenes_from_script


VALID_SCRIPT = {
    "title": "Glow Facts",
    "target_duration_seconds": 30,
    "tone": "curious",
    "primary_emotion": "wonder",
    "script_summary": "Bioluminescence short",
    "full_voiceover": "Animals glow for a reason. Deep oceans hide living light. Watch closely.",
    "call_to_action": "Follow for more",
    "estimated_word_count": 20,
    "segments": [
        {
            "segment_number": 1,
            "start_time": 0,
            "end_time": 5,
            "segment_type": "hook",
            "voiceover": "Animals glow for a reason.",
            "emotion": "curiosity",
            "delivery": "urgent",
            "retention_device": "open loop",
        },
        {
            "segment_number": 2,
            "start_time": 5,
            "end_time": 15,
            "segment_type": "context",
            "voiceover": "Deep oceans hide living light.",
            "emotion": "wonder",
            "delivery": "steady",
            "retention_device": "visual reveal",
        },
        {
            "segment_number": 3,
            "start_time": 15,
            "end_time": 25,
            "segment_type": "payoff",
            "voiceover": "Watch closely as chemistry becomes cinema.",
            "emotion": "awe",
            "delivery": "building",
            "retention_device": "payoff",
        },
        {
            "segment_number": 4,
            "start_time": 25,
            "end_time": 30,
            "segment_type": "cta",
            "voiceover": "Follow for more nature secrets.",
            "emotion": "warm",
            "delivery": "friendly",
            "retention_device": "cta",
        },
    ],
}


def test_scenes_from_script():
    asset = apply_script_to_asset({"title": "Glow Facts", "asset_id": "a1"}, VideoScript.from_dict(VALID_SCRIPT))
    scenes = _scenes_from_script(asset)
    assert len(scenes) == 4
    assert scenes[0]["purpose"] == "hook"
    assert scenes[0]["narration"]


def test_run_asset_production_offline_pipeline(monkeypatch, tmp_path):
    """Full chain with stubbed providers — still produces artifacts and stage reports."""
    monkeypatch.setattr("services.asset_production.artifacts.PRODUCTIONS_ROOT", tmp_path / "productions")
    monkeypatch.setattr("services.asset_production.artifacts.ROOT", tmp_path)

    # Stub image gen to real local files (cinematic path rejects placeholders)
    def fake_image(prompt, meta=None):
        img = tmp_path / f"gen_{abs(hash(prompt)) % 10**6}.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 600)
        return {
            "path": str(img),
            "local_path": str(img),
            "placeholder": False,
            "status": "generated",
            "prompt": prompt,
        }

    monkeypatch.setattr(
        "services.provider_runtime.engine_api.runtime_generate_image",
        fake_image,
    )

    def fake_cinematic_fallback(**kwargs):
        out = Path(kwargs.get("output_path") or tmp_path / "fallback.png")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 600)
        return {
            "path": str(out),
            "local_path": str(out),
            "placeholder": False,
            "status": "fallback_still",
            "provider": "cinematic_fallback",
        }

    from pathlib import Path

    monkeypatch.setattr(
        "services.asset_production.cinematic_fallback.generate_cinematic_fallback_still",
        fake_cinematic_fallback,
    )
    monkeypatch.setattr(
        "services.provider_runtime.engine_api.runtime_generate_video",
        lambda *a, **k: {"path": "", "placeholder": True, "async": True},
    )

    # Stub voice to write a real tiny file
    voice_file = tmp_path / "voice.mp3"
    voice_file.write_bytes(b"ID3fake")

    def fake_voice(text, profile=None, settings=None, mode="ai"):
        return {
            "ok": True,
            "placeholder": False,
            "path": str(voice_file),
            "duration_sec": 8.0,
            "voice_package": {
                "path": str(voice_file),
                "placeholder": False,
                "duration_sec": 8.0,
                "timing": {
                    "sentence_timestamps": [
                        {"text": "Animals glow for a reason.", "start": 0, "end": 3},
                        {"text": "Deep oceans hide living light.", "start": 3, "end": 6},
                    ]
                },
                "provider": "test",
            },
            "metadata": {},
            "asset_id": "v1",
            "mode": mode,
        }

    monkeypatch.setattr("services.media_production.voice.synthesize_voice", fake_voice)
    monkeypatch.setattr(
        "services.provider_runtime.config.has_credential",
        lambda env: env == "OPENAI_API_KEY",
    )

    # Stub ffmpeg assembly to write a real mp4-ish file
    def fake_assemble(**kwargs):
        from pathlib import Path as P

        out = P(kwargs.get("output_path") or (tmp_path / "out.mp4"))
        if not out.is_absolute():
            out = tmp_path / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 200)
        try:
            rel = str(out.relative_to(tmp_path))
        except ValueError:
            rel = str(out)
        return {
            "ok": True,
            "mock": False,
            "output_path": rel,
            "absolute_path": str(out),
            "bytes": out.stat().st_size,
            "log": ["multi_scene→mp4 scenes=2 effect=character_performance"],
            "visual_count": 2,
            "color_bed": False,
            "has_audio": True,
            "true_motion": {"motion_class": "true_layered_animation"},
        }

    monkeypatch.setattr("services.media_production.ffmpeg_assembler.assemble_mp4", fake_assemble)
    monkeypatch.setattr("services.media_production.ffmpeg_assembler.find_ffmpeg", lambda: "/usr/bin/ffmpeg")
    monkeypatch.setattr("services.media_production.ffmpeg_assembler.write_assembly_sidecar", lambda *a, **k: "")

    # Desktop ready-to-post export (avoid real ffmpeg probe on stub bytes)
    dest_dir = tmp_path / "desktop_export"
    dest_dir.mkdir(parents=True, exist_ok=True)

    def fake_final_export(source_mp4, *, title, qc_passed, render_package=None, when=None):
        from pathlib import Path as P
        import shutil

        assert qc_passed
        src = P(source_mp4)
        out = dest_dir / f"test_{title.replace(' ', '_')}.mp4"
        if src.exists():
            shutil.copy2(src, out)
        else:
            out.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 200)
        return {
            "ok": True,
            "final_export_path": str(out),
            "final_export_dir": str(dest_dir),
            "bytes": out.stat().st_size,
            "verification": {"ok": True, "duration_sec": 8.0, "has_video": True, "has_audio": True},
            "message": "Ready-to-post video saved successfully.",
        }

    monkeypatch.setattr(
        "services.asset_production.final_export.export_ready_to_post_mp4",
        fake_final_export,
    )

    asset = apply_script_to_asset(
        {"title": "Glow Facts", "hook": "Living light", "asset_id": "glow1", "hashtags": ["#nature"]},
        VideoScript.from_dict(VALID_SCRIPT),
    )
    project = {"name": "Test", "model": "gpt-4o-mini", "niche": "science", "platform": "youtube_shorts"}

    events = []
    result = run_asset_production(asset, project, on_progress=events.append, max_images=2)

    assert result.get("production_ok") is True
    stages = (result.get("production_pipeline") or {}).get("stages") or {}
    assert set(PIPELINE_STAGE_KEYS).issubset(set(stages.keys()))
    assert stages["script"]["status"] == "completed"
    assert stages["scenes"]["status"] == "completed"
    assert stages["captions"]["status"] == "completed"
    assert stages["render"]["status"] == "completed"
    assert stages["export"]["status"] == "completed"
    # No OAuth → publish skipped
    assert stages["publish"]["status"] in {"skipped", "completed"}
    assert (result.get("render_package") or {}).get("mp4_path")
    assert result.get("final_export_path")
    assert (tmp_path / "productions" / "glow1" / "scenes.json").exists()
    assert (tmp_path / "productions" / "glow1" / "captions.srt").exists()
    assert (tmp_path / "productions" / "glow1" / "metadata.json").exists()
    assert events  # live progress fired
