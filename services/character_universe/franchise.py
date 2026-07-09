"""Franchise management — series, seasons, episodes, spin-offs, collections,
educational programs, channels, brand shows, and shared universes.

Seasons and episodes are nested inside the franchise record (they have no
life outside it); characters and universes stay referenced by id.
Performance metrics flow IN from Analytics/Optimization via the
orchestrator — this module only stores and serves them.
"""

from __future__ import annotations

from services.character_universe.registry import CharacterUniverseRegistry, get_character_universe_registry
from services.character_universe.world_models import build_episode, build_season


class FranchiseManager:
    def __init__(self, registry: "CharacterUniverseRegistry | None" = None) -> None:
        self.registry = registry or get_character_universe_registry()

    def create_franchise(self, spec: dict) -> dict:
        return self.registry.create("franchises", spec)

    def create_spinoff(self, parent_franchise_id: str, spec: dict) -> dict:
        spinoff = dict(spec)
        spinoff["spinoff_of"] = parent_franchise_id
        spinoff.setdefault("franchise_type", "spinoff")
        parent = self.registry.get("franchises", parent_franchise_id) or {}
        spinoff.setdefault("universe_id", parent.get("universe_id", ""))
        spinoff.setdefault("brand_id", parent.get("brand_id", ""))
        return self.registry.create("franchises", spinoff)

    def add_season(self, franchise_id: str, spec: "dict | None" = None) -> "dict | None":
        franchise = self.registry.get("franchises", franchise_id)
        if franchise is None:
            return None
        seasons = franchise.setdefault("seasons", [])
        season = build_season(
            {"franchise_id": franchise_id, "number": len(seasons) + 1, **(spec or {})}
        )
        seasons.append(season)
        self.registry.store.save("franchises", franchise, franchise_id)
        return season

    def add_episode(self, franchise_id: str, season_id: str, spec: "dict | None" = None) -> "dict | None":
        franchise = self.registry.get("franchises", franchise_id)
        if franchise is None:
            return None
        season = next(
            (season for season in franchise.get("seasons", []) if season["season_id"] == season_id),
            None,
        )
        if season is None:
            return None
        episode = build_episode(
            {
                "franchise_id": franchise_id, "season_id": season_id,
                "number": len(season.get("episodes", [])) + 1, **(spec or {}),
            }
        )
        season.setdefault("episodes", []).append(episode)
        for character_id in episode.get("character_ids", []):
            cast = franchise.setdefault("character_ids", [])
            if character_id not in cast:
                cast.append(character_id)
        self.registry.store.save("franchises", franchise, franchise_id)
        return episode

    def episodes(self, franchise_id: str) -> list:
        franchise = self.registry.get("franchises", franchise_id) or {}
        return [
            episode
            for season in franchise.get("seasons", [])
            for episode in season.get("episodes", [])
        ]

    def record_performance(self, franchise_id: str, metrics: dict) -> "dict | None":
        """Merge analytics-provided metrics into the franchise's performance
        slot (called by the engine with orchestrator-supplied data)."""
        franchise = self.registry.get("franchises", franchise_id)
        if franchise is None:
            return None
        franchise.setdefault("performance", {}).update(metrics)
        self.registry.store.save("franchises", franchise, franchise_id)
        return franchise

    def franchises_for_character(self, character_id: str) -> list:
        return [
            franchise
            for franchise in self.registry.list("franchises")
            if character_id in franchise.get("character_ids", [])
        ]
