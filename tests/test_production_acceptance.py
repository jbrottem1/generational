"""Pytest entry for Production Acceptance (smoke-oriented)."""

from __future__ import annotations

from pathlib import Path

from services.production_acceptance import run_acceptance_suite
from services.production_acceptance.catalog import EXPECTED_OPS_STAGE_ORDER, REQUIRED_ENGINES
from services.production_acceptance.integrity import run_pipeline_integrity
from services.production_acceptance.models import DASHBOARD_PATH, HISTORY_PATH
from services.production_acceptance.recovery import run_recovery_tests


def test_pipeline_integrity_category():
    results = run_pipeline_integrity()
    assert results
    failed = [r for r in results if not r.passed]
    assert not failed, [f"{r.name}:{r.message}" for r in failed]


def test_required_engines_list_nonempty():
    assert "production_operations" in REQUIRED_ENGINES
    assert len(EXPECTED_OPS_STAGE_ORDER) == 16


def test_recovery_simulations_fast_subset():
    # Exclude live ops probes for unit speed — call API timeout / corrupt only
    from services.production_acceptance.recovery import _api_timeout, _corrupted_asset, _disk_full, _renderer_failure

    for fn in (_api_timeout, _disk_full, _corrupted_asset, _renderer_failure):
        ok, message, _metrics = fn()
        assert ok, message


def test_smoke_acceptance_suite_passes():
    """Full smoke gate — may take ~1–2 minutes."""
    result = run_acceptance_suite(mode="smoke")
    assert result["run_id"]
    assert Path(result["run_path"]).exists()
    assert DASHBOARD_PATH.exists() or result.get("dashboard")
    assert HISTORY_PATH.exists()
    assert result["summary"]["total"] >= 10
    # Allow soft warnings but require pass
    assert result["passed"] is True, result["summary"]
