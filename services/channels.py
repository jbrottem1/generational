"""Channel Manager — multiple brands/accounts, each with its own identity.

A channel is one faceless brand (e.g. a psychology shorts account) with its
niche, brand voice, platform targets, posting schedule, credentials, status,
and performance metrics. Future engines (publishing, analytics, learning)
operate per-channel; this service is their source of truth.

Channels are persisted locally under data/channels/ via the generic JSON
collection store. Note: credentials are stored as-is in local JSON for now —
move to a secrets manager before any multi-user deployment.
"""

from __future__ import annotations

import os

from core.log import get_logger, log_event
from core.storage.json_collection import JsonCollectionStore

logger = get_logger(__name__)

_DEFAULT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "channels"
)


class ChannelStatus:
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


def build_channel(
    name: str,
    niche: str,
    brand_voice: str = "",
    platforms: "list | None" = None,
    posting_schedule: "dict | None" = None,
    credentials: "dict | None" = None,
) -> dict:
    return {
        "name": name.strip(),
        "niche": niche,
        "brand_voice": brand_voice,
        "platforms": platforms or [],
        # e.g. {"youtube": "daily 18:00", "tiktok": "mon/wed/fri 12:00"}
        "posting_schedule": posting_schedule or {},
        "credentials": credentials or {},
        "status": ChannelStatus.ACTIVE,
        "metrics": {"videos_published": 0, "total_views": 0, "followers": 0},
    }


class ChannelManager:
    def __init__(self, directory: str = _DEFAULT_DIR) -> None:
        self._store = JsonCollectionStore(directory)

    def create_channel(self, name: str, niche: str, **kwargs) -> dict:
        if self._store.load(name):
            raise ValueError(f"Channel '{name}' already exists.")
        channel = build_channel(name, niche, **kwargs)
        self._store.save(channel)
        log_event(logger, "channel.created", name=name, niche=niche)
        return channel

    def get_channel(self, name: str) -> "dict | None":
        return self._store.load(name)

    def list_channels(self, status: "str | None" = None) -> list:
        channels = self._store.list_all()
        if status:
            channels = [channel for channel in channels if channel.get("status") == status]
        return channels

    def update_channel(self, name: str, **updates) -> dict:
        channel = self._store.load(name)
        if channel is None:
            raise ValueError(f"Channel '{name}' does not exist.")
        updates.pop("name", None)  # renames would orphan the record file
        channel.update(updates)
        self._store.save(channel)
        log_event(logger, "channel.updated", name=name, fields=",".join(updates.keys()))
        return channel

    def set_status(self, name: str, status: str) -> dict:
        return self.update_channel(name, status=status)

    def record_metrics(self, name: str, **metrics) -> dict:
        """Merge new metric values into the channel's performance metrics."""
        channel = self._store.load(name)
        if channel is None:
            raise ValueError(f"Channel '{name}' does not exist.")
        channel.setdefault("metrics", {}).update(metrics)
        self._store.save(channel)
        log_event(logger, "channel.metrics_recorded", name=name, metrics=",".join(metrics.keys()))
        return channel

    def delete_channel(self, name: str) -> bool:
        deleted = self._store.delete(name)
        if deleted:
            log_event(logger, "channel.deleted", name=name)
        return deleted

    def channel_count(self) -> int:
        return self._store.count()


_manager = ChannelManager()


def get_channel_manager() -> ChannelManager:
    """The app-wide channel manager singleton."""
    return _manager
