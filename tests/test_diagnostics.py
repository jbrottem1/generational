from core.diagnostics import run_diagnostics

EXPECTED_CHECKS = {
    "AI Provider",
    "Project Storage",
    "Engines",
    "Job Queue",
    "Channel Manager",
    "Knowledge Base",
}


def test_diagnostics_cover_all_services():
    checks = run_diagnostics()
    assert {check["name"] for check in checks} == EXPECTED_CHECKS


def test_diagnostics_never_error_in_clean_environment():
    for check in run_diagnostics():
        assert check["status"] in ("ok", "warn")
        assert check["detail"]
