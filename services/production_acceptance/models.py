"""Acceptance result models + persistence helpers."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ACCEPTANCE_ROOT = ROOT / "data" / "productions" / "_acceptance"
HISTORY_PATH = ACCEPTANCE_ROOT / "ACCEPTANCE_HISTORY.json"
DASHBOARD_PATH = ACCEPTANCE_ROOT / "ACCEPTANCE_DASHBOARD.json"
RUNS_DIR = ACCEPTANCE_ROOT / "runs"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TestResult:
    category: str
    name: str
    passed: bool
    duration_ms: int = 0
    message: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AcceptanceRun:
    run_id: str
    mode: str
    started_at: str
    finished_at: str = ""
    results: list[TestResult] = field(default_factory=list)
    version: str = "1.0.0"

    def add(self, result: TestResult) -> None:
        self.results.append(result)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def pass_pct(self) -> float:
        return round(100.0 * self.passed / self.total, 1) if self.total else 0.0

    def summary(self) -> dict[str, Any]:
        qualities = [
            float(r.metrics.get("overall_quality") or r.metrics.get("quality_score") or 0)
            for r in self.results
            if r.metrics.get("overall_quality") or r.metrics.get("quality_score")
        ]
        renders = [
            int(r.metrics.get("render_time_ms") or r.duration_ms or 0)
            for r in self.results
            if r.category in ("video_generation", "duration", "platform", "stress", "quality")
        ]
        recoveries = [r for r in self.results if r.category == "recovery"]
        recovery_ok = sum(1 for r in recoveries if r.passed)
        common_failures: dict[str, int] = {}
        for r in self.results:
            if not r.passed:
                key = f"{r.category}:{r.name}"
                common_failures[key] = common_failures.get(key, 0) + 1
        return {
            "run_id": self.run_id,
            "mode": self.mode,
            "version": self.version,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "pass_pct": self.pass_pct,
            "failure_pct": round(100.0 - self.pass_pct, 1) if self.total else 0.0,
            "average_quality": round(sum(qualities) / len(qualities), 1) if qualities else 0.0,
            "average_render_time_ms": int(sum(renders) / len(renders)) if renders else 0,
            "fastest_render_ms": min(renders) if renders else 0,
            "slowest_render_ms": max(renders) if renders else 0,
            "common_failures": sorted(common_failures.items(), key=lambda x: -x[1])[:20],
            "recovery_success_pct": round(100.0 * recovery_ok / len(recoveries), 1) if recoveries else 100.0,
            "ok": self.failed == 0,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.summary(),
            "results": [r.to_dict() for r in self.results],
        }


def new_run(mode: str, version: str = "1.0.0") -> AcceptanceRun:
    return AcceptanceRun(
        run_id=f"acc_{uuid.uuid4().hex[:10]}",
        mode=mode,
        started_at=_now(),
        version=version,
    )


def persist_run(run: AcceptanceRun) -> Path:
    ACCEPTANCE_ROOT.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run.finished_at = _now()
    payload = run.to_dict()
    path = RUNS_DIR / f"{run.run_id}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    history = {"runs": [], "updated_at": _now()}
    if HISTORY_PATH.exists():
        try:
            history = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            history = {"runs": []}
    runs = list(history.get("runs") or [])
    runs.append(run.summary())
    history["runs"] = runs[-200:]
    history["updated_at"] = _now()
    HISTORY_PATH.write_text(json.dumps(history, indent=2), encoding="utf-8")
    return path


def load_history(limit: int = 50) -> list[dict]:
    if not HISTORY_PATH.exists():
        return []
    try:
        data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        return list(reversed(list(data.get("runs") or [])[-limit:]))
    except Exception:  # noqa: BLE001
        return []
