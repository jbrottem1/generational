"""Character, Universe & Intellectual Property department — Agent 15.

The permanent creative memory of the company: every persistent character,
universe, location, organization, relationship, canon event, franchise,
brand identity, and style pack originates here. This package never
generates media and never calls another engine — the
`character_universe` engine publishes its outputs on shared context keys
and the orchestrator routes them (Architecture Directive #1).

Public surface:
- get_character_universe_registry() — CRUD for every IP entity
- RelationshipEngine / CharacterMemorySystem / ContinuityEngine /
  FranchiseManager — the subsystems
- build_bible() — the on-demand Story Bible
- integrations — payload builders for Script, Creative Studio, Asset
  Generation (Agent 14), and the Optimization Laboratory
"""

from services.character_universe.bible import build_bible
from services.character_universe.config import (
    CharacterUniverseConfig,
    get_character_universe_config,
    set_character_universe_config,
)
from services.character_universe.continuity import ContinuityEngine
from services.character_universe.franchise import FranchiseManager
from services.character_universe.memory import CharacterMemorySystem
from services.character_universe.registry import (
    CharacterUniverseRegistry,
    get_character_universe_registry,
)
from services.character_universe.relationships import RelationshipEngine

__all__ = [
    "CharacterUniverseConfig",
    "CharacterUniverseRegistry",
    "CharacterMemorySystem",
    "ContinuityEngine",
    "FranchiseManager",
    "RelationshipEngine",
    "build_bible",
    "get_character_universe_config",
    "get_character_universe_registry",
    "set_character_universe_config",
]
