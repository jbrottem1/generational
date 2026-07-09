"""JSON persistence for ProductionJob (Agent 23)."""

from __future__ import annotations

import json
import threading
from pathlib import Path

from services.autonomous_production.models import Checkpoint, ProductionJob

_DEFAULT_DIR = Path(__file__).resolve().parents[2] / "data" / "production_jobs"


class ProductionJobStore:
    """File-backed store for durable autonomous production jobs."""

    def __init__(self, directory: "str | Path | None" = None) -> None:
        self._dir = Path(directory) if directory else _DEFAULT_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._checkpoints = self._dir / "checkpoints"
        self._checkpoints.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    @property
    def directory(self) -> Path:
        return self._dir

    def save(self, job: ProductionJob) -> Path:
        path = self._dir / f"{job.job_id}.json"
        payload = json.dumps(job.to_dict(), indent=2)
        with self._lock:
            path.write_text(payload, encoding="utf-8")
            if job.checkpoint:
                ckpt_path = self._checkpoints / f"{job.job_id}.json"
                ckpt_path.write_text(
                    json.dumps(job.checkpoint.to_dict(), indent=2),
                    encoding="utf-8",
                )
        return path

    def load(self, job_id: str) -> "ProductionJob | None":
        path = self._dir / f"{job_id}.json"
        if not path.exists():
            return None
        try:
            return ProductionJob.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            return None

    def list_jobs(self, state: str = "") -> list[dict]:
        jobs = []
        for path in sorted(self._dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            if path.parent.name == "checkpoints":
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if "job_id" not in data:
                continue
            if state and data.get("state") != state:
                continue
            jobs.append(
                {
                    "job_id": data.get("job_id"),
                    "command": data.get("command", ""),
                    "state": data.get("state"),
                    "production_mode": data.get("production_mode"),
                    "progress_pct": data.get("progress_pct", 0),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                    "workflow_run_id": data.get("workflow_run_id", ""),
                }
            )
        return jobs

    def save_checkpoint(self, checkpoint: Checkpoint) -> Path:
        path = self._checkpoints / f"{checkpoint.job_id}.json"
        with self._lock:
            path.write_text(json.dumps(checkpoint.to_dict(), indent=2), encoding="utf-8")
        return path

    def load_checkpoint(self, job_id: str) -> "Checkpoint | None":
        path = self._checkpoints / f"{job_id}.json"
        if not path.exists():
            return None
        try:
            return Checkpoint.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            return None

    def delete(self, job_id: str) -> bool:
        removed = False
        with self._lock:
            job_path = self._dir / f"{job_id}.json"
            ckpt_path = self._checkpoints / f"{job_id}.json"
            if job_path.exists():
                job_path.unlink()
                removed = True
            if ckpt_path.exists():
                ckpt_path.unlink()
                removed = True
        return removed


_store: "ProductionJobStore | None" = None


def get_production_store(directory: "str | Path | None" = None) -> ProductionJobStore:
    global _store
    if directory is not None:
        return ProductionJobStore(directory)
    if _store is None:
        _store = ProductionJobStore()
    return _store


def reset_production_store() -> None:
    global _store
    _store = None
