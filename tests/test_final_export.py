"""Tests for ready-to-post Desktop export helpers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from services.asset_production.final_export import (
    build_export_filename,
    export_ready_to_post_mp4,
    sanitize_title,
    unique_export_path,
    verify_ready_to_post_mp4,
)


def test_sanitize_title_removes_invalid_chars():
    assert sanitize_title('Secrets of Bioluminescence: "Glow"') == "Secrets_of_Bioluminescence_Glow"
    assert "/" not in sanitize_title("a/b\\c")


def test_unique_export_path_versions(tmp_path):
    first = unique_export_path(tmp_path, "2026-07-10_11-20-45_Secrets")
    first.write_bytes(b"x")
    second = unique_export_path(tmp_path, "2026-07-10_11-20-45_Secrets")
    assert second.name.endswith("_v2.mp4")
    second.write_bytes(b"y")
    third = unique_export_path(tmp_path, "2026-07-10_11-20-45_Secrets")
    assert third.name.endswith("_v3.mp4")


def test_build_export_filename_format():
    name = build_export_filename("Black Holes Explained", when=datetime(2026, 7, 10, 11, 20, 45))
    assert name == "2026-07-10_11-20-45_Black_Holes_Explained"


def test_export_rejects_mock(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "services.asset_production.final_export.FINAL_EXPORT_DIR",
        tmp_path / "export",
    )
    monkeypatch.setattr(
        "services.asset_production.final_export.final_export_dir",
        lambda: (tmp_path / "export").mkdir(parents=True, exist_ok=True) or (tmp_path / "export"),
    )
    src = tmp_path / "render.mp4"
    src.write_bytes(b"\x00" * 1000)
    result = export_ready_to_post_mp4(
        src,
        title="Test",
        qc_passed=True,
        render_package={"mock": True},
    )
    assert result["ok"] is False
    assert "mock" in result["error"].lower()


def test_export_copies_when_verified(tmp_path, monkeypatch):
    export_dir = tmp_path / "AI Start-up" / "videos" / "test run generational"
    monkeypatch.setattr("services.asset_production.final_export.FINAL_EXPORT_DIR", export_dir)
    monkeypatch.setattr(
        "services.asset_production.final_export.final_export_dir",
        lambda: export_dir.mkdir(parents=True, exist_ok=True) or export_dir,
    )
    monkeypatch.setattr(
        "services.asset_production.final_export.verify_ready_to_post_mp4",
        lambda *a, **k: {
            "ok": True,
            "errors": [],
            "path": str(a[0]),
            "bytes": 1000,
            "has_video": True,
            "has_audio": True,
            "duration_sec": 12.0,
        },
    )
    src = tmp_path / "render.mp4"
    src.write_bytes(b"\x00" * 1000)
    result = export_ready_to_post_mp4(
        src,
        title="Secrets of Bioluminescence",
        qc_passed=True,
        render_package={"mock": False},
        when=datetime(2026, 7, 10, 11, 20, 45),
    )
    assert result["ok"] is True
    dest = Path(result["final_export_path"])
    assert dest.exists()
    assert dest.parent == export_dir
    assert dest.name == "2026-07-10_11-20-45_Secrets_of_Bioluminescence.mp4"
    assert result["message"] == "Ready-to-post video saved successfully."
