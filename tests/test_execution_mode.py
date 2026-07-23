"""Tests for local-first execution helpers."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def _load_execution_mode():
    path = ROOT / "services/media_production/execution_mode.py"
    name = "execution_mode_under_test"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


em = _load_execution_mode()


def test_always_local_mode():
    assert em.detect_execution_mode() == em.ExecutionMode.LOCAL
    with mock.patch.dict("os.environ", {"GENERATIONAL_EXECUTION_MODE": "cloud", "CURSOR_CLOUD_AGENT": "1"}, clear=False):
        # Cloud env vars must not resurrect a cloud production mode
        assert em.detect_execution_mode() == em.ExecutionMode.LOCAL


def test_should_render_media_always_true():
    assert em.should_render_media() is True
    assert em.should_render_media(allow_cloud_smoke=True) is True


def test_local_status_message():
    assert "Local render authorized" in em.local_status_message()


def test_canonical_export_dir_uses_home():
    path = em.canonical_export_dir()
    assert path.name == "Videos"
    # Either historical spelling is valid; resolver prefers an existing Desktop folder
    assert "AI Start-Up" in str(path) or "AI Start-UP" in str(path)
    assert str(path).startswith(str(Path.home()))


def test_context_is_local_first():
    ctx = em.get_execution_context()
    assert ctx.mode == em.ExecutionMode.LOCAL
    assert ctx.can_render_media is True
    assert ctx.signals.get("local_first") is True
