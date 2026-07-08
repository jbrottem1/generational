"""Engine registry — the single place engines plug into the system."""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.base import Engine

logger = get_logger(__name__)

_engines: dict = {}


def register(engine: Engine) -> Engine:
    """Register (or replace) an engine under its key."""
    _engines[engine.key] = engine
    log_event(logger, "engine.registered", key=engine.key, ready=engine.is_ready(), version=engine.version)
    return engine


def get_engine(key: str) -> "Engine | None":
    return _engines.get(key)


def all_engines() -> list:
    return list(_engines.values())


def ready_engines() -> list:
    return [engine for engine in _engines.values() if engine.is_ready()]


def engine_keys() -> list:
    return list(_engines.keys())
