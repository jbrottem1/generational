"""Backward-compatible shim — heuristics live in ``core.heuristics``.

Prefer ``from core.heuristics import …`` in new services code to avoid
pulling the full ``engines`` package during import (circular-import risk).
"""

from __future__ import annotations

from core.heuristics import *  # noqa: F403
from core import heuristics as _core_heuristics

__all__ = [name for name in dir(_core_heuristics) if not name.startswith("_")]
