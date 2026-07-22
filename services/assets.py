"""Asset Manager — reusable asset registry across projects."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

from core.log import get_logger, log_event

logger = get_logger(__name__)

_DEFAULT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "assets"
)
_INDEX_FILE = "index.json"


class AssetManager:
    def __init__(self, directory: str = _DEFAULT_DIR) -> None:
        self.directory = directory

    def _ensure_dir(self) -> None:
        os.makedirs(self.directory, exist_ok=True)

    def _load_index(self) -> list:
        path = os.path.join(self.directory, _INDEX_FILE)
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    def _save_index(self, assets: list) -> None:
        self._ensure_dir()
        with open(os.path.join(self.directory, _INDEX_FILE), "w", encoding="utf-8") as f:
            json.dump(assets, f, indent=2)

    def register(self, asset: dict, niche: str = "") -> dict:
        asset.setdefault("asset_id", f"ast_{uuid.uuid4().hex[:10]}")
        asset["niche"] = niche
        asset["registered_at"] = datetime.now(timezone.utc).isoformat()
        assets = self._load_index()
        assets = [a for a in assets if a.get("asset_id") != asset["asset_id"]]
        assets.append(asset)
        self._save_index(assets)
        log_event(logger, "asset.registered", asset_id=asset["asset_id"], type=asset.get("asset_type"))
        return asset

    def list_assets(self, asset_type: str = "", niche: str = "") -> list:
        assets = self._load_index()
        if asset_type:
            assets = [a for a in assets if a.get("asset_type") == asset_type]
        if niche:
            assets = [a for a in assets if a.get("niche") == niche]
        return assets

    def count(self) -> int:
        return len(self._load_index())


class PublishingQueue:
    """In-memory + JSON persisted queue for render packages awaiting publish."""

    def __init__(self, directory: str = None) -> None:
        base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "publishing_queue")
        self.directory = directory or base
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        os.makedirs(self.directory, exist_ok=True)

    def _queue_path(self) -> str:
        return os.path.join(self.directory, "queue.json")

    def _load(self) -> list:
        path = self._queue_path()
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self, items: list) -> None:
        with open(self._queue_path(), "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)

    def enqueue(
        self,
        content_id: str,
        title: str,
        render_package: dict,
        niche: str,
        publish_score: int,
        *,
        status: str = "queued",
        hold_reason: str = "",
        autonomous_publishing_enabled: bool = False,
    ) -> dict:
        # Enqueue ≠ publish. Default path holds packages until autonomous
        # publishing is explicitly enabled AND every quality gate passes.
        entry = {
            "queue_id": f"q_{uuid.uuid4().hex[:10]}",
            "content_id": content_id,
            "title": title,
            "niche": niche,
            "publish_score": publish_score,
            "render_package_id": render_package.get("package_id", ""),
            "status": status,
            "hold_reason": hold_reason,
            "autonomous_publishing_enabled": bool(autonomous_publishing_enabled),
            "queued_at": datetime.now(timezone.utc).isoformat(),
        }
        items = self._load()
        items.append(entry)
        self._save(items)
        log_event(
            logger,
            "publishing_queue.enqueued",
            queue_id=entry["queue_id"],
            title=title[:40],
            status=status,
        )
        return entry

    def list_pending(self) -> list:
        return [i for i in self._load() if i.get("status") in {"queued", "held"}]

    def list_held(self) -> list:
        return [i for i in self._load() if i.get("status") == "held"]

    def count(self) -> int:
        return len(self.list_pending())


_asset_manager = AssetManager()
_publishing_queue = PublishingQueue()


def get_asset_manager() -> AssetManager:
    return _asset_manager


def get_publishing_queue() -> PublishingQueue:
    return _publishing_queue
