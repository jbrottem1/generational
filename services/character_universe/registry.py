"""Character & Universe registry — the single write path for all IP entities.

Every persistent character, universe, location, organization, canon event,
franchise, brand identity, and style pack is created, updated, versioned,
and archived here. Subsystems (relationships, memory, continuity,
franchise, integrations) read through this registry; nothing else writes
the store directly.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from services.character_universe.config import get_character_universe_config
from services.character_universe.models import (
    CharacterStatus,
    build_canon_event,
    build_character,
)
from services.character_universe.store import get_store
from services.character_universe.world_models import (
    build_brand_identity,
    build_franchise,
    build_location,
    build_organization,
    build_style_pack,
    build_universe,
)

logger = get_logger(__name__)

_BUILDERS = {
    "characters": (build_character, "character_id"),
    "universes": (build_universe, "universe_id"),
    "locations": (build_location, "location_id"),
    "organizations": (build_organization, "organization_id"),
    "canon_events": (build_canon_event, "event_id"),
    "franchises": (build_franchise, "franchise_id"),
    "brand_identities": (build_brand_identity, "brand_identity_id"),
    "style_packs": (build_style_pack, "style_pack_id"),
}

_LIMITS = {"characters": "max_characters", "universes": "max_universes"}


class CharacterUniverseRegistry:
    def __init__(self, store=None) -> None:
        self.store = store or get_store()

    # ------------------------------------------------------------ generic

    def id_field(self, kind: str) -> str:
        return _BUILDERS[kind][1]

    def create(self, kind: str, spec: dict) -> dict:
        builder, id_field = _BUILDERS[kind]
        config = get_character_universe_config()
        limit_name = _LIMITS.get(kind)
        if limit_name:
            limit = getattr(config, limit_name)
            if limit and self.store.count(kind) >= limit:
                raise ValueError(f"{kind} limit reached ({limit}) — raise {limit_name} or archive entities")

        record = builder(spec)
        self.store.save(kind, record, record[id_field])
        log_event(logger, "character_universe.created", kind=kind, entity=record[id_field])
        return record

    def get(self, kind: str, entity_id: str) -> "dict | None":
        return self.store.load(kind, entity_id)

    def list(self, kind: str, **filters) -> list:
        records = self.store.list_all(kind)
        for key, value in filters.items():
            records = [record for record in records if record.get(key) == value]
        return records

    def update(self, kind: str, entity_id: str, changes: dict) -> "dict | None":
        """Merge changes into an entity, bumping its version when enabled."""
        _builder, id_field = _BUILDERS[kind]
        record = self.store.load(kind, entity_id)
        if record is None:
            return None
        record.update({key: value for key, value in changes.items() if key != id_field})
        if get_character_universe_config().versioning_enabled and "version" in record:
            record["version"] = int(record.get("version") or 1) + 1
        self.store.save(kind, record, entity_id)
        return record

    def archive(self, kind: str, entity_id: str) -> bool:
        """Archive (default) or hard-delete an entity per configuration."""
        config = get_character_universe_config()
        if config.archive_instead_of_delete:
            record = self.store.load(kind, entity_id)
            if record is None:
                return False
            record["status"] = CharacterStatus.ARCHIVED
            self.store.save(kind, record, entity_id)
            return True
        return self.store.delete(kind, entity_id)

    # ------------------------------------------------- convenience surface

    def create_character(self, spec: dict) -> dict:
        return self.create("characters", spec)

    def create_universe(self, spec: dict) -> dict:
        return self.create("universes", spec)

    def create_location(self, spec: dict) -> dict:
        location = self.create("locations", spec)
        self._attach_to_universe(location.get("universe_id"), "location_ids", location["location_id"])
        return location

    def create_organization(self, spec: dict) -> dict:
        organization = self.create("organizations", spec)
        self._attach_to_universe(
            organization.get("universe_id"), "organization_ids", organization["organization_id"]
        )
        return organization

    def create_canon_event(self, spec: dict) -> dict:
        event = self.create("canon_events", spec)
        self._attach_to_universe(event.get("universe_id"), "canon_event_ids", event["event_id"])
        return event

    def characters_in_universe(self, universe_id: str) -> list:
        return self.list("characters", universe_id=universe_id)

    def active_characters(self) -> list:
        return self.list("characters", status=CharacterStatus.ACTIVE)

    def canon_events_for(self, universe_id: str) -> list:
        events = self.list("canon_events", universe_id=universe_id)
        events.sort(key=lambda event: (event.get("sequence", 0), event.get("occurred_at", "")))
        return events

    def _attach_to_universe(self, universe_id: "str | None", field: str, entity_id: str) -> None:
        if not universe_id:
            return
        universe = self.store.load("universes", universe_id)
        if universe is None:
            return
        ids = universe.setdefault(field, [])
        if entity_id not in ids:
            ids.append(entity_id)
            self.store.save("universes", universe, universe_id)


_registry: "CharacterUniverseRegistry | None" = None


def get_character_universe_registry() -> CharacterUniverseRegistry:
    global _registry
    store = get_store()
    if _registry is None or _registry.store is not store:
        _registry = CharacterUniverseRegistry(store)
    return _registry
