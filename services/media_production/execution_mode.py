"""Execution mode detection — cloud plans, local renders.

Cloud agents must never claim a finished MP4 exists on the user's Mac.
Local workstations execute FFmpeg, TTS, and verified Desktop export.
"""

from __future__ import annotations

import os
import platform
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from core.env import project_root


# Canonical Generational export folder (user Mac Desktop)
CANONICAL_EXPORT_PARTS = (
    "Desktop",
    "AI Start-up",
    "videos",
    "Test run 2 generational",
)


class ExecutionMode(str, Enum):
    CLOUD = "cloud"
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


def canonical_export_dir(*, create: bool = False) -> Path:
    """Resolved ~/Desktop/AI Start-up/videos/Test run 2 generational."""
    path = Path.home().joinpath(*CANONICAL_EXPORT_PARTS)
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def _env_truthy(name: str) -> bool:
    return str(os.environ.get(name) or "").strip().lower() in ("1", "true", "yes", "on")


def detect_execution_mode() -> ExecutionMode:
    """Return CLOUD or LOCAL for the current runtime."""
    forced = str(os.environ.get("GENERATIONAL_EXECUTION_MODE") or "").strip().lower()
    if forced == "local":
        return ExecutionMode.LOCAL
    if forced == "cloud":
        return ExecutionMode.CLOUD

    if _env_truthy("GENERATIONAL_FORCE_LOCAL"):
        return ExecutionMode.LOCAL

    # Cursor cloud-agent and CI are always cloud for media production
    cloud_signals = (
        _env_truthy("CURSOR_CLOUD_AGENT")
        or _env_truthy("CURSOR_AGENT")
        or _env_truthy("CI")
        or bool(os.environ.get("GITHUB_ACTIONS"))
        or _env_truthy("GENERATIONAL_CLOUD_MODE")
    )
    if cloud_signals:
        return ExecutionMode.CLOUD

    system = platform.system()
    if system == "Darwin":
        # macOS workstation — local production when Desktop tree is reachable
        startup = Path.home() / "Desktop" / "AI Start-up"
        if startup.exists() or _env_truthy("GENERATIONAL_LOCAL_MAC"):
            return ExecutionMode.LOCAL

    if system == "Linux":
        # Remote Linux VMs (cloud agents) are not the user's Mac
        return ExecutionMode.CLOUD

    # Windows / other dev machines — treat as local if operator opts in
    if _env_truthy("GENERATIONAL_LOCAL_MAC"):
        return ExecutionMode.LOCAL

    return ExecutionMode.LOCAL if system == "Darwin" else ExecutionMode.CLOUD


def get_execution_context() -> ExecutionContext:
    mode = detect_execution_mode()
    export = canonical_export_dir()
    can_render = mode == ExecutionMode.LOCAL
    return ExecutionContext(
        mode=mode,
        platform=platform.system(),
        home=str(Path.home()),
        canonical_export_dir=str(export),
        can_render_media=can_render,
        can_claim_export_success=can_render,
        signals={
            "CURSOR_CLOUD_AGENT": _env_truthy("CURSOR_CLOUD_AGENT"),
            "CI": _env_truthy("CI"),
            "GITHUB_ACTIONS": bool(os.environ.get("GITHUB_ACTIONS")),
            "GENERATIONAL_EXECUTION_MODE": os.environ.get("GENERATIONAL_EXECUTION_MODE"),
            "GENERATIONAL_FORCE_LOCAL": _env_truthy("GENERATIONAL_FORCE_LOCAL"),
            "desktop_startup_exists": (Path.home() / "Desktop" / "AI Start-up").exists(),
        },
    )


def should_render_media(*, allow_cloud_smoke: bool = False) -> bool:
    """True only when this machine may execute FFmpeg/TTS production."""
    ctx = get_execution_context()
    if ctx.can_render_media:
        return True
    return allow_cloud_smoke and _env_truthy("GENERATIONAL_CLOUD_SMOKE_TEST")


def cloud_status_message() -> str:
    return "Production package prepared. Awaiting local render."


def local_success_requires_verified_export(export_path: Path) -> bool:
    """Final SUCCESS is allowed only when verified MP4 exists at canonical export."""
    ctx = get_execution_context()
    if not ctx.can_claim_export_success:
        return False
    canonical = canonical_export_dir()
    try:
        export_path.resolve()
        canonical.resolve()
    except OSError:
        return False
    if not export_path.is_file() or export_path.stat().st_size <= 0:
        return False
    # Must live under canonical export directory
    return str(export_path.resolve()).startswith(str(canonical.resolve()))


def write_execution_snapshot(path: Path | None = None) -> Path:
    """Persist current execution context for agents and audits."""
    out = path or (project_root() / "data" / "productions" / "execution_context.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        **get_execution_context().to_dict(),
    }
    out.write_text(__import__("json").dumps(payload, indent=2), encoding="utf-8")
    return out
