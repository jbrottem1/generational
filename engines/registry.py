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


# ---------------------------------------------------------------------------
# Architecture introspection (v9.6) — the machine-readable views behind the
# Engine Capability Index and System Dependency Map. Read-only; safe for any
# engine, dashboard, or future Autonomous Executive to consume.
# ---------------------------------------------------------------------------


def describe(engine: Engine) -> dict:
    """Uniform self-description for any engine (contract-first or classic)."""
    if hasattr(engine, "diagnostics"):
        info = engine.diagnostics()
    else:
        info = {
            "engine_id": engine.key,
            "name": engine.label or engine.key,
            "version": engine.version,
            "ready": engine.is_ready(),
            "input_contract": [],
            "output_contract": [],
            "dependencies": [],
            "capabilities": [],
        }
    info["description"] = engine.description
    return info


def describe_all() -> list:
    """Capability index source: one description dict per registered engine."""
    return [describe(engine) for engine in _engines.values()]


def capability_index() -> dict:
    """capability tag → sorted engine keys that declare it."""
    index: dict = {}
    for info in describe_all():
        for capability in info.get("capabilities", []):
            index.setdefault(capability, []).append(info["engine_id"])
    return {capability: sorted(keys) for capability, keys in sorted(index.items())}


def dependency_graph() -> dict:
    """engine key → declared upstream engine keys (contract engines only)."""
    return {
        info["engine_id"]: list(info.get("dependencies", []))
        for info in describe_all()
        if info.get("dependencies")
    }
