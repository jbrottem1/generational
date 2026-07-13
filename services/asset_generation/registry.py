"""Asset Registry — every generated asset, versioned, forever.

JSON store (`data/asset_generation/registry.json`, same convention as the
analytics store and creative memory) holding:

- **Assets** — one entry per asset_id with full metadata and an
  append-only version history (`ASSET_VERSION_FIELDS`): regenerating an
  asset appends a version, never overwrites one.
- **Generation history** — every generation job (`GENERATION_JOB_FIELDS`),
  append-only, so every asset is auditable back to the provider, prompt,
  and attempt chain that produced it.
- **Collections** — named groups of asset_ids (brand libraries, character
  packs, reusable backgrounds) shareable across productions.
- **Fingerprint index** — content-address → asset_id, powering the cache
  (`cache.py`) and duplicate detection.

Tests isolate by constructing with `directory=` (or by swapping the
module `_DEFAULT_DIR`, mirroring services/analytics/store.py).
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

from core.log import get_logger, log_event

logger = get_logger(__name__)

_DEFAULT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "asset_generation",
)

_REGISTRY_FILE = "registry.json"

_EMPTY = {"assets": {}, "jobs": [], "collections": {}, "fingerprints": {}}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AssetRegistry:
    """Versioned JSON store for generated assets + generation history."""

    def __init__(self, directory: str = "") -> None:
        self.directory = directory or _DEFAULT_DIR

    # ------------------------------------------------------------ plumbing

    def _path(self) -> str:
        return os.path.join(self.directory, _REGISTRY_FILE)

    def _read(self) -> dict:
        path = self._path()
        if not os.path.exists(path):
            return json.loads(json.dumps(_EMPTY))
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
            for key, default in _EMPTY.items():
                data.setdefault(key, json.loads(json.dumps(default)))
            return data
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to read asset registry: %s", exc)
            return json.loads(json.dumps(_EMPTY))

    def _write(self, data: dict) -> None:
        os.makedirs(self.directory, exist_ok=True)
        with open(self._path(), "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

    # -------------------------------------------------------------- assets

    def register_asset(self, asset: dict) -> dict:
        """Store (or version) one ASSET_FIELDS dict.

        A new asset_id creates the entry at version 1; an existing
        asset_id with a NEW fingerprint appends the next version (history
        is never overwritten); re-registering the same fingerprint is a
        no-op returning the stored entry.
        """
        data = self._read()
        asset_id = str(asset.get("asset_id", "")) or f"asset_{uuid.uuid4().hex[:10]}"
        fingerprint = str(asset.get("fingerprint", ""))
        entry = data["assets"].get(asset_id)

        if entry is None:
            stored = dict(asset)
            stored["asset_id"] = asset_id
            stored["version"] = 1
            stored["versions"] = [_version_entry(stored)]
            data["assets"][asset_id] = stored
        else:
            known = {v.get("fingerprint") for v in entry.get("versions", [])}
            if fingerprint and fingerprint in known:
                return entry
            stored = dict(entry)
            stored.update(asset)
            stored["asset_id"] = asset_id
            stored["version"] = int(entry.get("version", 1)) + 1
            stored["versions"] = list(entry.get("versions", [])) + [_version_entry(stored)]
            data["assets"][asset_id] = stored

        if fingerprint:
            data["fingerprints"][fingerprint] = asset_id
        self._write(data)
        return data["assets"][asset_id]

    def get_asset(self, asset_id: str) -> "dict | None":
        return self._read()["assets"].get(str(asset_id))

    def find_by_fingerprint(self, fingerprint: str) -> "dict | None":
        """The registered asset matching one content-address (cache hit)."""
        data = self._read()
        asset_id = data["fingerprints"].get(str(fingerprint))
        return data["assets"].get(asset_id) if asset_id else None

    def asset_count(self) -> int:
        return len(self._read()["assets"])

    # ---------------------------------------------------------------- jobs

    def record_job(self, job: dict) -> dict:
        """Append one GENERATION_JOB_FIELDS dict to the history."""
        data = self._read()
        stored = dict(job)
        stored.setdefault("job_id", f"genjob_{uuid.uuid4().hex[:10]}")
        stored.setdefault("created_at", _now_iso())
        data["jobs"].append(stored)
        self._write(data)
        return stored

    def history(self, asset_id: str = "", limit: "int | None" = None) -> list:
        """Generation jobs newest-first, optionally for one asset."""
        jobs = list(reversed(self._read()["jobs"]))
        if asset_id:
            jobs = [job for job in jobs if job.get("asset_id") == asset_id]
        return jobs[:limit] if limit else jobs

    # ---------------------------------------------------------- collections

    def add_to_collection(self, collection_id: str, asset_ids: "list[str]") -> list:
        """Append asset ids to a named collection (created on first use)."""
        data = self._read()
        existing = data["collections"].setdefault(str(collection_id), [])
        for asset_id in asset_ids:
            if asset_id not in existing:
                existing.append(str(asset_id))
        self._write(data)
        return list(existing)

    def get_collection(self, collection_id: str) -> list:
        return list(self._read()["collections"].get(str(collection_id), []))

    def collections(self) -> "dict[str, list]":
        return dict(self._read()["collections"])


def _version_entry(asset: dict) -> dict:
    return {
        "version": int(asset.get("version", 1)),
        "fingerprint": str(asset.get("fingerprint", "")),
        "uri": str(asset.get("uri", "")),
        "provider": str(asset.get("provider", "")),
        "status": str(asset.get("status", "")),
        "created_at": str(asset.get("created_at", "")) or _now_iso(),
    }


def get_asset_registry() -> AssetRegistry:
    """A registry bound to the current default directory (test-swappable)."""
    return AssetRegistry()
