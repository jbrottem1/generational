"""Local-first execution — Mac workstation production only.

Generational renders, verifies, and exports exclusively on the user's local Mac.
There is no Cursor Cloud (or remote VM) production execution path.

Canonical export root:
  ~/Desktop/AI Start-Up/Videos/
"""

from __future__ import annotations

import json
import os
import platform
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from core.env import project_root


# Permanent Generational Media Library (user Mac Desktop)
# Prefer existing on-disk spelling; default create uses AI Start-UP (workspace parent).
CANONICAL_EXPORT_PARTS = (
    "Desktop",
    "AI Start-UP",
    "Videos",
)

_AI_STARTUP_SPELLINGS = ("AI Start-UP", "AI Start-Up", "AI Start-up")


def resolve_ai_startup_root() -> Path:
    """Return existing Desktop brand folder, else preferred AI Start-UP spelling."""
    desktop = Path.home() / "Desktop"
    for name in _AI_STARTUP_SPELLINGS:
        path = desktop / name
        if path.is_dir():
            return path
    return desktop / "AI Start-UP"


class ExecutionMode(str, Enum):
    """Production always runs locally. Enum retained for JSON compatibility."""

    LOCAL = "local"


@dataclass(frozen=True)
class ExecutionContext:
    mode: ExecutionMode
    platform: str
    home: str
    canonical_export_dir: str
    can_render_media: bool
    can_claim_export_success: bool
    signals: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["mode"] = self.mode.value
        return d


def _env_truthy(name: str) -> bool:
    return str(os.environ.get(name) or "").strip().lower() in ("1", "true", "yes", "on")


def canonical_export_dir(*, create: bool = False) -> Path:
    """Resolved ~/Desktop/{AI Start-UP|AI Start-Up}/Videos/ (whichever exists)."""
    path = resolve_ai_startup_root() / "Videos"
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def desktop_library_reachable() -> bool:
    """True when the user's Desktop media library root is present (or creatable on Mac)."""
    desktop = Path.home() / "Desktop"
    if any((desktop / name).exists() for name in _AI_STARTUP_SPELLINGS):
        return True
    # Fresh Mac installs may not have the folder yet — Darwin can create it on export
    return platform.system() == "Darwin"


def detect_execution_mode() -> ExecutionMode:
    """Always local. Production never runs on Cursor Cloud."""
    return ExecutionMode.LOCAL


def get_execution_context() -> ExecutionContext:
    """Local Mac production context. Render/export are always authorized on this machine."""
    export = canonical_export_dir()
    reachable = desktop_library_reachable()
    # Local-first: this workstation owns render + verified Desktop export
    can_render = True
    can_claim = reachable or platform.system() == "Darwin"
    return ExecutionContext(
        mode=ExecutionMode.LOCAL,
        platform=platform.system(),
        home=str(Path.home()),
        canonical_export_dir=str(export),
        can_render_media=can_render,
        can_claim_export_success=can_claim,
        signals={
            "local_first": True,
            "desktop_library_reachable": reachable,
            "python": platform.python_version(),
        },
    )


def should_render_media(*, allow_cloud_smoke: bool = False) -> bool:
    """True — production always renders locally.

    ``allow_cloud_smoke`` is accepted for call-site compatibility and ignored.
    """
    _ = allow_cloud_smoke
    return get_execution_context().can_render_media


def local_status_message() -> str:
    return f"Local render authorized. Export to {canonical_export_dir()}/."


# Backward-compatible alias — cloud handoff messaging removed
def cloud_status_message() -> str:
    return local_status_message()


def local_success_requires_verified_export(export_path: Path) -> bool:
    """Final SUCCESS is allowed only when verified MP4 exists under the media library."""
    ctx = get_execution_context()
    if not ctx.can_claim_export_success:
        return False
    canonical = canonical_export_dir()
    try:
        resolved = export_path.resolve()
        canonical_resolved = canonical.resolve()
    except OSError:
        return False
    if not export_path.is_file() or export_path.stat().st_size <= 0:
        return False
    return str(resolved).startswith(str(canonical_resolved))


def write_execution_snapshot(path: Path | None = None) -> Path:
    """Persist local execution context for audits."""
    out = path or (project_root() / "data" / "productions" / "execution_context.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 2,
        "policy": "local_first",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        **get_execution_context().to_dict(),
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out
