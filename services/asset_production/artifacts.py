"""Artifact I/O for per-asset productions under data/productions/{asset_id}/."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PRODUCTIONS_ROOT = ROOT / "data" / "productions"


def production_dir(asset_id: str) -> Path:
    path = PRODUCTIONS_ROOT / _safe(asset_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in (value or "asset"))[:80] or "asset"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def write_json(asset_id: str, name: str, payload: Any) -> str:
    path = production_dir(asset_id) / name
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return rel(path)


def write_text(asset_id: str, name: str, content: str) -> str:
    path = production_dir(asset_id) / name
    path.write_text(content or "", encoding="utf-8")
    return rel(path)


def copy_into(asset_id: str, source: str, name: str) -> str:
    if not source:
        return ""
    src = Path(source)
    if not src.is_absolute():
        src = ROOT / source
    if not src.exists():
        return ""
    dest = production_dir(asset_id) / name
    shutil.copy2(src, dest)
    return rel(dest)


def list_artifacts(asset_id: str) -> list[str]:
    folder = production_dir(asset_id)
    return [rel(p) for p in sorted(folder.iterdir()) if p.is_file()]
