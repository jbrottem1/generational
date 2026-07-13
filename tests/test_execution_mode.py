"""Tests for local-first execution mode detection."""

from __future__ import annotations

import os
import sys
import importlib.util
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _load_execution_mode():
    path = ROOT / "services/media_production/execution_mode.py"
    name = "execution_mode_under_test"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


em = _load_execution_mode()


def test_cloud_detection_linux():
    with mock.patch.dict(os.environ, {"GENERATIONAL_EXECUTION_MODE": "cloud"}, clear=False):
        assert em.detect_execution_mode() == em.ExecutionMode.CLOUD


def test_local_detection_forced():
    with mock.patch.dict(os.environ, {"GENERATIONAL_EXECUTION_MODE": "local"}, clear=False):
        assert em.detect_execution_mode() == em.ExecutionMode.LOCAL


def test_canonical_export_path():
    path = em.canonical_export_dir()
    assert path.name == "Videos"
    assert "AI Start-Up" in str(path)


def test_cloud_status_message():
    assert "Awaiting local render" in em.cloud_status_message()


if __name__ == "__main__":
    test_cloud_detection_linux()
    test_local_detection_forced()
    test_canonical_export_path()
    test_cloud_status_message()
    print("all execution mode tests passed")
