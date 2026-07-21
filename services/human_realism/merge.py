"""Deep-merge helpers for Human Realism inheritance."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def deep_merge(base: Any, override: Any) -> Any:
    """Recursively merge override onto a deep copy of base.

    - dicts merge key-wise
    - lists in override replace base lists (identity lists stay character-specific)
    - scalars in override win
    """
    if override is None:
        return deepcopy(base)
    if not isinstance(base, dict) or not isinstance(override, dict):
        return deepcopy(override)
    out = deepcopy(base)
    for key, value in override.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = deepcopy(value)
    return out
