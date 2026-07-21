"""Regression tests — export reliability & final status truthfulness."""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

from services.animation.foundation_gate import evaluate_foundation_export
from services.generational_os.final_status import (
    FinalStatus,
    assign_final_status,
    format_completion_block,
)
from services.media_production.verified_export import assess_export_technical_validity
from services.quality.content_score import hard_fail_reasons, score_production


def _probe(**overrides):
    base = {
        "ok": True,
        "bytes": 1_500_000,
        "has_video": True,
        "has_audio": True,
        "duration_sec": 24.5,
        "width": 1080,
        "height": 1920,
        "video_codec": "h264",
        "audio_codec": "aac",
        "bit_rate": 500_000,
        "fps": 24.0,
    }
    base.update(overrides)
    return base


def _write_fake_mp4(path: Path, size: int = 120_000) -> Path:
    # Minimal ISO BMFF-ish header so placeholder detection does not trip
    path.write_bytes(b"\x00\x00\x00\x18ftypisom" + b"\x00" * max(0, size - 12))
    return path


def test_valid_small_short_form_not_export_too_small(tmp_path):
    """Short educational clips may be under 50KB yet still pass when verified."""
    mp4 = _write_fake_mp4(tmp_path / "short.mp4", size=40_000)
    prod = {
        "export_path": str(mp4),
        "export_bytes": 40_000,
        "duration_sec": 18.0,
        "demo_id": "foundation_short",
        "qc": {"passed": True, "mouth_varies": True, "idle_ratio": 0.3, "walk_ratio": 0.05},
        "verify": {"ok": True, "has_audio": True, "has_video": True, "bytes": 40_000},
        "hook": "Why do turtles have shells anyway?",
        "script": {"hook": "Why do turtles have shells anyway?", "takeaway": "Shells evolved."},
    }
    fails = hard_fail_reasons(prod, foundation=True)
    assert "export_too_small" not in fails
    report = score_production(prod, foundation=True)
    assert "export_too_small" not in report.hard_fails


def test_missing_animation_qc_with_valid_video_is_warning(tmp_path):
    mp4 = _write_fake_mp4(tmp_path / "ok.mp4", size=200_000)
    with mock.patch(
        "services.media_production.verified_export.assess_export_technical_validity",
        return_value={"ok": True, "hard_fails": [], "warnings": [], "probe": _probe(), "is_placeholder": False},
    ), mock.patch(
        "services.media_production.verified_export.ffprobe_mp4",
        return_value=_probe(),
    ):
        gate = evaluate_foundation_export(
            {
                "demo_id": "foundation_turtles",
                "foundation": True,
                "export_path": str(mp4),
                "export_bytes": 200_000,
                "verification": {"ok": True, "probe": _probe()},
                "hook": "Have you ever wondered where turtles came from?",
                "script": {
                    "hook": "Have you ever wondered where turtles came from?",
                    "takeaway": "Shells assembled gradually.",
                },
                "education_score": 80.0,
                "educational_review": {"score": 80.0, "accuracy_score": 75.0},
            }
        )
    assert gate.passed
    assert gate.final_status in (
        FinalStatus.SUCCESS.value,
        FinalStatus.SUCCESS_WITH_WARNINGS.value,
    )
    assert "animation_qc_missing" in gate.warnings or "qc_report_regenerated" in gate.warnings
    assert "animation_qc_missing" not in gate.hard_fails
    assert "missing_animation_qc" not in gate.hard_fails


def test_temp_exists_final_missing_is_failed(tmp_path):
    temp = _write_fake_mp4(tmp_path / "temp.mp4", size=100_000)
    final = tmp_path / "Biology" / "missing.mp4"
    status = assign_final_status(
        export_verified=False,
        export_path=final,
        hard_fails=["destination_not_created"],
        warnings=[],
    )
    assert status["final_status"] == FinalStatus.FAILED.value
    assert temp.is_file()  # temp preserved; final absent


def test_final_exists_manifest_path_null_recovers(tmp_path):
    mp4 = _write_fake_mp4(tmp_path / "Biology_001_202_Origin_of_Turtles.mp4", size=200_000)
    status = assign_final_status(
        export_verified=True,
        export_path=mp4,
        hard_fails=[],
        warnings=["manifest_path_null_recovered"],
    )
    assert status["final_status"] == FinalStatus.SUCCESS_WITH_WARNINGS.value
    assert status["ok"] is True
    assert status["export_path"] == str(mp4.resolve())


def test_zero_byte_mp4_hard_fails(tmp_path):
    mp4 = tmp_path / "empty.mp4"
    mp4.write_bytes(b"")
    tech = assess_export_technical_validity(mp4, probe=_probe(ok=False, bytes=0, duration_sec=0, has_video=False, has_audio=False))
    assert tech["ok"] is False
    assert "export_zero_bytes" in tech["hard_fails"] or "invalid_duration" in tech["hard_fails"]
    status = assign_final_status(
        export_verified=False,
        export_path=mp4,
        hard_fails=tech["hard_fails"],
    )
    assert status["final_status"] == FinalStatus.FAILED.value


def test_missing_audio_hard_fails(tmp_path):
    mp4 = _write_fake_mp4(tmp_path / "noaudio.mp4")
    tech = assess_export_technical_validity(
        mp4,
        probe=_probe(ok=False, has_audio=False, bytes=mp4.stat().st_size),
    )
    assert "missing_audio" in tech["hard_fails"]
    status = assign_final_status(
        export_verified=False,
        export_path=mp4,
        hard_fails=tech["hard_fails"],
    )
    assert status["final_status"] == FinalStatus.FAILED.value


def test_missing_video_stream_hard_fails(tmp_path):
    mp4 = _write_fake_mp4(tmp_path / "novideo.mp4")
    tech = assess_export_technical_validity(
        mp4,
        probe=_probe(ok=False, has_video=False, bytes=mp4.stat().st_size),
    )
    assert "missing_video" in tech["hard_fails"]


def test_duration_mismatch_hard_fails(tmp_path):
    mp4 = _write_fake_mp4(tmp_path / "mismatch.mp4")
    tech = assess_export_technical_validity(
        mp4,
        probe=_probe(duration_sec=5.0, bytes=mp4.stat().st_size),
        expected_duration_sec=30.0,
    )
    assert "duration_mismatch" in tech["hard_fails"]


def test_stale_cloud_path_hard_fails(tmp_path):
    # Simulate cloud path detection via absolute path string check on a real file
    mp4 = _write_fake_mp4(tmp_path / "cloudish.mp4")
    with mock.patch.object(Path, "resolve", return_value=Path("/home/ubuntu/Desktop/fake.mp4")):
        tech = assess_export_technical_validity(mp4, probe=_probe(bytes=mp4.stat().st_size))
    assert "stale_cloud_path" in tech["hard_fails"]


def test_local_desktop_export_status_success(tmp_path):
    dest_dir = tmp_path / "Biology"
    dest_dir.mkdir(parents=True, exist_ok=True)
    mp4 = _write_fake_mp4(dest_dir / "Biology_001_202_Origin_of_Turtles.mp4", size=1_500_000)
    status = assign_final_status(
        export_verified=True,
        export_path=mp4,
        hard_fails=[],
        warnings=[],
    )
    assert status["final_status"] == FinalStatus.SUCCESS.value
    assert status["publishing_status"] == "ready_for_review"


def test_warning_only_qc_is_success_with_warnings(tmp_path):
    mp4 = _write_fake_mp4(tmp_path / "warn.mp4", size=200_000)
    status = assign_final_status(
        export_verified=True,
        export_path=mp4,
        hard_fails=["animation_qc_missing", "technical_validity_below_threshold"],
        warnings=["overall_below_target:77.4<78.0"],
    )
    assert status["final_status"] == FinalStatus.SUCCESS_WITH_WARNINGS.value
    assert status["ok"] is True
    assert "animation_qc_missing" in status["warnings"]
    assert status["hard_fails"] == []


def test_true_hard_failure_animation_qc_failed(tmp_path):
    mp4 = _write_fake_mp4(tmp_path / "bad.mp4", size=200_000)
    status = assign_final_status(
        export_verified=True,
        export_path=mp4,
        hard_fails=["animation_qc_failed"],
        warnings=[],
    )
    assert status["final_status"] == FinalStatus.FAILED.value
    assert status["ok"] is False


def test_completion_block_lists_warnings(tmp_path):
    mp4 = _write_fake_mp4(tmp_path / "done.mp4", size=1_400_000)
    block = format_completion_block(
        final_status=FinalStatus.SUCCESS_WITH_WARNINGS.value,
        export_path=mp4,
        probe=_probe(bytes=1_400_000),
        warnings=["animation_qc_missing"],
    )
    assert "STATUS: SUCCESS_WITH_WARNINGS" in block
    assert "FINAL FILE:" in block
    assert str(mp4.resolve()) in block
    assert "WARNINGS:" in block
    assert "animation_qc_missing" in block


def test_export_verified_production_persists_ready_for_review(tmp_path, monkeypatch):
    """Bookkeeping flags must be true when the manifest is written — Origin of Turtles bug."""
    from services.generational_os import export as export_mod

    src = _write_fake_mp4(tmp_path / "episode.mp4", size=200_000)
    lib = tmp_path / "Videos"
    (lib / "Biology").mkdir(parents=True)

    monkeypatch.setattr(export_mod, "get_execution_context", lambda: mock.Mock(
        can_render_media=True,
        can_claim_export_success=True,
    ))
    monkeypatch.setattr(export_mod, "library_root", lambda create=False: lib)
    monkeypatch.setattr(export_mod, "category_dir", lambda cat, create=False: (lib / cat).mkdir(parents=True, exist_ok=True) or (lib / cat))
    monkeypatch.setattr(
        export_mod,
        "classify_production",
        lambda **k: {"primary": "Biology", "secondary": []},
    )
    monkeypatch.setattr(export_mod, "find_duplicate", lambda *a, **k: None)
    monkeypatch.setattr(export_mod, "file_sha256", lambda p: "abc123")
    monkeypatch.setattr(
        export_mod,
        "versioned_export_path",
        lambda d, name, file_hash=None: (d / name, False),
    )
    monkeypatch.setattr(
        export_mod,
        "companion_dir_for",
        lambda dest: dest.with_suffix(""),
    )
    monkeypatch.setattr(
        export_mod,
        "write_companion_files",
        lambda *a, **k: {"script": str(tmp_path / "script.md")},
    )
    # Ensure companion check passes
    (tmp_path / "script.md").write_text("ok")
    monkeypatch.setattr(
        export_mod,
        "ffprobe_mp4",
        lambda p: _probe(bytes=Path(p).stat().st_size if Path(p).is_file() else 0, absolute_path=str(Path(p).resolve())),
    )
    monkeypatch.setattr(
        export_mod,
        "assess_export_technical_validity",
        lambda p, probe=None, expected_duration_sec=None: {
            "ok": True,
            "hard_fails": [],
            "warnings": [],
            "probe": probe or _probe(),
            "is_placeholder": False,
        },
    )
    monkeypatch.setattr(export_mod, "wait_for_file", lambda p, **k: True)
    monkeypatch.setattr(export_mod, "register_library_entry", lambda e: None)
    monkeypatch.setattr(export_mod, "update_from_manifest", lambda d: None)
    monkeypatch.setattr(export_mod, "upsert_production", lambda *a, **k: None)
    monkeypatch.setattr(export_mod, "reveal_export_in_finder", lambda p: False)
    monkeypatch.setattr(export_mod, "load_manifest", lambda pid: None)

    saved = {}

    def _fake_update(**kwargs):
        from services.generational_os.manifest import ProductionManifest

        m = ProductionManifest(project_id=kwargs["project_id"] if False else "turtle_202")
        # Call real update logic via constructing from kwargs
        from services.generational_os.manifest import update_manifest_from_export as real

        # Patch save to capture
        def _save(manifest):
            saved["manifest"] = manifest.to_dict()
            return tmp_path / "PRODUCTION_MANIFEST.json"

        monkeypatch.setattr("services.generational_os.manifest.save_manifest", _save)
        monkeypatch.setattr("services.generational_os.manifest.load_manifest", lambda pid: None)
        return real(
            "turtle_202",
            export_path=kwargs["export_path"],
            domain_folder=kwargs["domain_folder"],
            verification=kwargs["verification"],
            qc_score=kwargs.get("qc_score"),
            render_duration_sec=kwargs.get("render_duration_sec"),
            title=kwargs.get("title", ""),
            topic=kwargs.get("topic", ""),
            secondary_categories=kwargs.get("secondary_categories"),
            keywords=kwargs.get("keywords"),
            file_hash=kwargs.get("file_hash", ""),
            companion_path=kwargs.get("companion_path", ""),
            library_filename=kwargs.get("library_filename", ""),
            final_status=kwargs.get("final_status"),
            publishing_status=kwargs.get("publishing_status"),
            local_render_status=kwargs.get("local_render_status"),
        )

    # Simpler: patch update_manifest_from_export to capture verification
    captured = {}

    def capture_update(project_id, **kwargs):
        from services.generational_os.manifest import ProductionManifest, save_manifest

        captured["verification"] = kwargs["verification"]
        captured["final_status"] = kwargs.get("final_status")
        captured["publishing_status"] = kwargs.get("publishing_status")
        m = ProductionManifest(
            project_id=project_id,
            export_path=str(kwargs["export_path"]),
            publishing_status=kwargs.get("publishing_status") or "ready_for_review",
            local_render_status=kwargs.get("local_render_status") or "verified",
            final_status=kwargs.get("final_status") or "SUCCESS",
            verification=kwargs["verification"],
        )
        save_manifest(m) if False else None
        captured["manifest"] = m
        return m

    monkeypatch.setattr(export_mod, "update_manifest_from_export", capture_update)
    monkeypatch.setattr(export_mod, "save_manifest", lambda m: None)

    result = export_mod.export_verified_production(
        src,
        project_id="turtle_202",
        filename="Biology_001_202_Origin_of_Turtles.mp4",
        domain="Biology",
        title="The Origin of Turtles",
        series="001",
        episode="202",
        topic="Origin of Turtles",
        print_completion=False,
    )

    assert result["ok"] is True
    assert result["final_status"] in (FinalStatus.SUCCESS.value, FinalStatus.SUCCESS_WITH_WARNINGS.value)
    assert result["export_path"]
    assert Path(result["export_path"]).is_file()
    checks = captured["verification"]["checks"]
    assert checks["manifest_updated"] is True
    assert checks["library_index_updated"] is True
    assert captured["verification"]["ok"] is True
    assert captured["publishing_status"] == "ready_for_review"


def test_duplicate_filename_versioning(tmp_path):
    from services.media_production.verified_export import unique_export_path

    first = unique_export_path(tmp_path, "Biology_001_202_Origin_of_Turtles.mp4")
    first.write_bytes(b"a")
    second = unique_export_path(tmp_path, "Biology_001_202_Origin_of_Turtles.mp4")
    assert second.name.endswith("_v2.mp4")
