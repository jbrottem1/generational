"""Configuration for the Character & Universe Engine.

One dataclass, one accessor, one override hook — the same pattern other
departments use. Everything a studio might tune (limits, strictness,
memory size, versioning/archiving policy) lives here instead of being
scattered through the subsystems.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class CharacterUniverseConfig:
    # Hard limits (0 = unlimited).
    max_characters: int = 0
    max_universes: int = 0

    # Memory system: max entries kept per memory category per character.
    memory_size: int = 200

    # Continuity: "strict" escalates warnings to errors; "relaxed" reports
    # only errors; "standard" reports both as detected.
    continuity_strictness: str = "standard"

    # Duplicate detection: name similarity ratio (0-1) above which two
    # characters in the same universe are flagged.
    duplicate_name_threshold: float = 0.92

    # Versioning / archiving policy.
    versioning_enabled: bool = True
    archive_instead_of_delete: bool = True

    # Brand / lore rule packs applied by the continuity validators.
    brand_rules: list = field(default_factory=list)
    lore_rules: list = field(default_factory=list)
    universe_rules: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


_config = CharacterUniverseConfig()


def get_character_universe_config() -> CharacterUniverseConfig:
    return _config


def set_character_universe_config(config: CharacterUniverseConfig) -> CharacterUniverseConfig:
    """Replace the active configuration (tests and future settings UI)."""
    global _config
    _config = config
    return _config
