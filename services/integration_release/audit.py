"""Subsystem audit for Integration & Release."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

SUBSYSTEMS: list[dict[str, Any]] = [
    {
        "id": "executive_os",
        "name": "Executive Operating System",
        "owner": 0,
        "paths": ["EXECUTIVE_OS.md", "AGENT_REGISTRY.md"],
        "risk": "low",
    },
    {
        "id": "animation",
        "name": "Animation / Foundation Studio",
        "owner": 16,
        "paths": ["services/animation/", "PROJECT_FOUNDATION.md"],
        "tests": ["tests/test_foundation_studio.py", "tests/test_foundation_gate.py"],
        "risk": "medium",
    },
    {
        "id": "character_systems",
        "name": "Character Systems",
        "owner": 26,
        "paths": ["services/character_systems/", "data/character_systems/"],
        "tests": ["tests/test_character_systems.py"],
        "risk": "low",
    },
    {
        "id": "visual_intelligence",
        "name": "Visual Intelligence",
        "owner": 4,
        "paths": ["services/visual/", "engines/visual_intelligence.py"],
        "tests": ["tests/test_visual_intelligence.py"],
        "risk": "medium",
    },
    {
        "id": "knowledge_atlas",
        "name": "Knowledge Atlas",
        "owner": 4,
        "paths": ["services/knowledge_atlas/", "data/knowledge_atlas/"],
        "tests": ["tests/test_knowledge_atlas.py"],
        "risk": "low",
    },
    {
        "id": "project_reality",
        "name": "Real Image Integration",
        "owner": 4,
        "paths": ["services/reality/", "PROJECT_REALITY.md"],
        "tests": ["tests/test_reality_integration.py"],
        "risk": "low",
    },
    {
        "id": "knowledge_standards",
        "name": "Knowledge & Standards",
        "owner": 27,
        "paths": ["services/knowledge_standards/", "data/knowledge_standards/"],
        "tests": ["tests/test_knowledge_standards.py"],
        "risk": "low",
    },
    {
        "id": "orchestrator",
        "name": "Orchestrator / Pipeline",
        "owner": 1,
        "paths": ["services/orchestrator/", "engines/"],
        "tests": ["tests/test_orchestrator.py", "tests/test_architecture.py"],
        "risk": "high",
    },
    {
        "id": "provider_runtime",
        "name": "Provider Runtime",
        "owner": 19,
        "paths": ["services/provider_runtime/"],
        "tests": ["tests/test_provider_runtime.py"],
        "risk": "high",
    },
    {
        "id": "render_ffmpeg",
        "name": "Render / FFmpeg / Media Production",
        "owner": 6,
        "paths": ["services/media_production/", "services/animation/performer.py"],
        "tests": ["tests/test_media_production.py", "tests/test_render_engine.py"],
        "risk": "high",
    },
    {
        "id": "publishing",
        "name": "Publishing",
        "owner": 7,
        "paths": ["services/publishing/"],
        "tests": ["tests/test_publishing_engine.py"],
        "risk": "medium",
    },
    {
        "id": "studio_ui",
        "name": "Studio UI",
        "owner": 20,
        "paths": ["ui/", "services/studio/"],
        "tests": ["tests/test_studio.py"],
        "risk": "medium",
    },
]


def _run_pytest(paths: list[str], timeout: int = 120) -> dict[str, Any]:
    if not paths:
        return {"ran": False, "passed": None, "failed": None}
    cmd = [sys.executable, "-m", "pytest", *paths, "-q", "--tb=no"]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        out = proc.stdout + proc.stderr
        failed = out.count(" FAILED")
        # Parse "N passed" from tail
        passed = 0
        for line in out.splitlines():
            if " passed" in line and " in " in line:
                try:
                    passed = int(line.strip().split()[0])
                except ValueError:
                    pass
        return {
            "ran": True,
            "exit_code": proc.returncode,
            "passed": passed,
            "failed": failed or (1 if proc.returncode != 0 else 0),
            "ok": proc.returncode == 0,
        }
    except Exception as exc:  # noqa: BLE001
        return {"ran": True, "ok": False, "error": str(exc)}


def audit_subsystems(*, quick: bool = True) -> list[dict[str, Any]]:
    """Audit each major subsystem."""
    results: list[dict[str, Any]] = []
    for sub in SUBSYSTEMS:
        paths_exist = all((ROOT / p).exists() for p in sub.get("paths", [])[:1])
        test_result = (
            {"ran": False, "skipped": True}
            if quick or not sub.get("tests")
            else _run_pytest(sub["tests"])
        )
        production_ready = paths_exist and (
            test_result.get("ok") is True or test_result.get("skipped")
        )
        results.append(
            {
                **sub,
                "paths_exist": paths_exist,
                "test_result": test_result,
                "production_readiness": "ready" if production_ready else "review",
            }
        )
    return results


def run_integration_audit(*, write_dashboard: bool = True) -> dict[str, Any]:
    """Full audit + optional dashboard.json write."""
    from services.integration_release.readiness import build_release_dashboard

    dashboard = build_release_dashboard()
    if write_dashboard:
        out = ROOT / "data" / "integration_release" / "dashboard.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(dashboard, indent=2), encoding="utf-8")
    return dashboard
