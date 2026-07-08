"""Provider interfaces — swappable backends for every external capability.

Business logic and engines depend only on these interfaces, never on OpenAI
or any single vendor. Implement a provider, register it in the matching
factory module, and every engine that uses that capability picks it up.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Provider(ABC):
    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """Whether this provider can serve requests right now."""
