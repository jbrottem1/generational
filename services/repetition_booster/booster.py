"""Repetition Booster — stable fingerprints, cache reuse, incremental regen.

Wraps existing provider + asset-generation caches without replacing them.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "data" / "repetition_booster" / "registry.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fingerprint_inputs(payload: dict[str, Any], *, keys: tuple[str, ...] | None = None) -> str:
    """Stable SHA-256 over canonical JSON subset."""
    data = dict(payload or {})
    if keys:
        data = {k: data.get(k) for k in keys if k in data}
    blob = json.dumps(data, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def should_regenerate(
    *,
    fingerprint: str,
    approved: bool = False,
    force: bool = False,
    registry: dict[str, Any] | None = None,
) -> bool:
    """Never regenerate an unchanged approved asset unless forced."""
    if force:
        return True
    reg = registry if registry is not None else RepetitionBooster().load_registry()
    entry = (reg.get("assets") or {}).get(fingerprint)
    if not entry:
        return True
    if approved and entry.get("status") == "approved":
        return False
    return entry.get("fingerprint") != fingerprint


def asset_lineage(entry: dict[str, Any]) -> list[str]:
    """Return upstream fingerprints for an asset record."""
    lineage = entry.get("lineage") or entry.get("upstream") or []
    return list(lineage) if isinstance(lineage, list) else []


class RepetitionBooster:
    """Track fingerprints, reuse counts, and incremental invalidation."""

    def __init__(self, registry_path: Path | None = None):
        self.path = registry_path or REGISTRY_PATH

    def load_registry(self) -> dict[str, Any]:
        p = self.path
        if not p.exists():
            return {"version": 1, "assets": {}, "stats": {}}
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {"version": 1, "assets": {}, "stats": {}, "corrupt": True}

    @classmethod
    def load_global_registry(cls, path: Path | None = None) -> dict[str, Any]:
        return cls(path).load_registry()

    def save_registry(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data["updated_at"] = _now_iso()
        self.path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def record(
        self,
        *,
        fingerprint: str,
        asset_type: str,
        uri: str = "",
        approved: bool = False,
        upstream: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        reg = self.load_registry()
        assets = dict(reg.get("assets") or {})
        prev = assets.get(fingerprint) or {}
        reuse = int(prev.get("reuse_count") or 0)
        if prev.get("uri") == uri and uri:
            reuse += 1
        entry = {
            "fingerprint": fingerprint,
            "asset_type": asset_type,
            "uri": uri,
            "status": "approved" if approved else prev.get("status", "draft"),
            "reuse_count": reuse,
            "lineage": list(upstream or prev.get("lineage") or []),
            "metadata": dict(metadata or prev.get("metadata") or {}),
            "updated_at": _now_iso(),
        }
        assets[fingerprint] = entry
        reg["assets"] = assets
        stats = dict(reg.get("stats") or {})
        stats["total_assets"] = len(assets)
        stats["approved_assets"] = sum(1 for a in assets.values() if a.get("status") == "approved")
        stats["total_reuse"] = sum(int(a.get("reuse_count") or 0) for a in assets.values())
        reg["stats"] = stats
        self.save_registry(reg)
        return entry

    def lookup(self, fingerprint: str) -> dict[str, Any] | None:
        reg = self.load_registry()
        if reg.get("corrupt"):
            return None
        entry = (reg.get("assets") or {}).get(fingerprint)
        return dict(entry) if entry else None

    def stats(self) -> dict[str, Any]:
        reg = self.load_registry()
        return dict(reg.get("stats") or {})

    def invalidate_downstream(self, fingerprint: str) -> list[str]:
        """Mark assets that depend on fingerprint for regen."""
        reg = self.load_registry()
        assets = dict(reg.get("assets") or {})
        invalidated: list[str] = []
        for fp, entry in assets.items():
            if fingerprint in asset_lineage(entry):
                entry["status"] = "stale"
                entry["updated_at"] = _now_iso()
                invalidated.append(fp)
        if invalidated:
            reg["assets"] = assets
            self.save_registry(reg)
        return invalidated
