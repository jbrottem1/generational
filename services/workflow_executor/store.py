"""JSON persistence for ProjectRun / Checkpoint (Agent 21)."""

from __future__ import annotations

import json
import threading
from pathlib import Path

from services.workflow_executor.models import Checkpoint, ProjectRun

_DEFAULT_DIR = Path(__file__).resolve().parents[2] / "data" / "workflow_runs"


class WorkflowRunStore:
    """File-backed store for durable workflow runs and checkpoints."""

    def __init__(self, directory: "str | Path | None" = None) -> None:
        self._dir = Path(directory) if directory else _DEFAULT_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._checkpoints = self._dir / "checkpoints"
        self._checkpoints.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    @property
    def directory(self) -> Path:
        return self._dir

    def save(self, run: ProjectRun) -> Path:
        path = self._dir / f"{run.run_id}.json"
        payload = json.dumps(run.to_dict(), indent=2)
        with self._lock:
            path.write_text(payload, encoding="utf-8")
            if run.checkpoint:
                ckpt_path = self._checkpoints / f"{run.checkpoint.run_id}.json"
                ckpt_path.write_text(
                    json.dumps(run.checkpoint.to_dict(), indent=2),
                    encoding="utf-8",
                )
        return path

    def load(self, run_id: str) -> "ProjectRun | None":
        path = self._dir / f"{run_id}.json"
        if not path.exists():
            return None
        try:
            return ProjectRun.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            return None

    def list_runs(self, status: str = "") -> list[dict]:
        runs = []
        for path in sorted(self._dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            if path.parent.name == "checkpoints" or path.name.startswith("."):
                continue
            # Skip nested checkpoint files if any land in root.
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if "run_id" not in data:
                continue
            if status and data.get("status") != status:
                continue
            runs.append(
                {
                    "run_id": data.get("run_id"),
                    "command": data.get("command", ""),
                    "status": data.get("status"),
                    "production_type": data.get("production_type"),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                    "progress_pct": (data.get("workflow") or {}).get("progress_pct", 0),
                }
            )
        return runs

    def save_checkpoint(self, checkpoint: Checkpoint) -> Path:
        path = self._checkpoints / f"{checkpoint.run_id}.json"
        with self._lock:
            path.write_text(json.dumps(checkpoint.to_dict(), indent=2), encoding="utf-8")
        return path

    def load_checkpoint(self, run_id: str) -> "Checkpoint | None":
        path = self._checkpoints / f"{run_id}.json"
        if not path.exists():
            return None
        try:
            return Checkpoint.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            return None

    def delete(self, run_id: str) -> bool:
        removed = False
        with self._lock:
            run_path = self._dir / f"{run_id}.json"
            ckpt_path = self._checkpoints / f"{run_id}.json"
            if run_path.exists():
                run_path.unlink()
                removed = True
            if ckpt_path.exists():
                ckpt_path.unlink()
                removed = True
        return removed


_store: "WorkflowRunStore | None" = None


def get_workflow_store(directory: "str | Path | None" = None) -> WorkflowRunStore:
    global _store
    if directory is not None:
        return WorkflowRunStore(directory)
    if _store is None:
        _store = WorkflowRunStore()
    return _store


def reset_workflow_store() -> None:
    global _store
    _store = None
