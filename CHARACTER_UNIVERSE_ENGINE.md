# Character, Universe & Intellectual Property Engine — Agent 15

The permanent creative memory of Generational. Every recurring character,
fictional world, educational host, mascot, AI avatar, location,
organization, timeline, and franchise originates here. This engine never
generates media, never writes scripts, and never renders — it maintains
persistent IP and publishes structured context for every other department.

> **"Generational evolves from creating individual videos to building
> enduring franchises and intellectual property."**

---

## 1. Where it sits

```
services/character_universe/     models, registry, continuity, memory,
        ↓                        relationships, franchise, bible, integrations
engines/character_universe.py    thin pipeline adapter (key: character_universe)
        ↓
shared context keys              consumed by Script Generation, Creative
                                 Studio, Universal Asset Generation (Agent 14),
                                 and Optimization Laboratory
```

Pipeline position (runnable standalone today; scheduled ahead of script
generation when Agent 1 wires the full pipeline):

```
character_universe → script_generation → visual_intelligence → …
```

All communication flows Orchestrator → Engine Registry → shared context.
No engine imports another engine (Architecture Directive #1, enforced by
`tests/test_architecture.py`).

---

## 2. Character system

Unlimited persistent characters. Each record is a JSON-safe dict built by
`build_character()` with every field in `CHARACTER_FIELDS`:

| Group | Fields |
|---|---|
| Identity | `character_id`, `name`, `nicknames`, `aliases`, `biography`, `age`, `species`, `gender`, `occupation`, `role` |
| Psychology | `goals`, `motivations`, `strengths`, `weaknesses`, `personality_traits`, `speech_style`, `voice_style`, `vocabulary`, `humor_style`, `catchphrases`, `emotional_state` |
| Story | `backstory`, `growth_arc`, `current_arc`, `status`, `relationship_ids` |
| Metrics | `popularity_score`, `brand_importance` |
| Profiles | `visual_profile` (`VISUAL_PROFILE_FIELDS`), `voice_profile` (`VOICE_PROFILE_FIELDS`), `memory` (`CHARACTER_MEMORY_FIELDS`) |
| Scope | `universe_id`, `brand_id`, `usage_rights`, `version`, `created_at`, `updated_at` |

The house cast (`services/character_universe/seed.py`) seeds idempotently on
first run: The Narrator, Nova (AI presenter), Gen (mascot), Professor Atlas
(educational host) inside **The Generational Universe**.

---

## 3. Universe & location system

Universe records (`UNIVERSE_FIELDS`) carry timeline, history, cultures,
technology, magic rules, economy, politics, conflicts, lore, canon events,
story hooks, and rule packs. Locations (`LOCATION_FIELDS`) support countries,
cities, buildings, rooms, landmarks, vehicles, and regions with environment
rules, lighting profiles, weather, and architecture.

Organizations (`ORGANIZATION_FIELDS`) track teams, member lists, leaders,
goals, and rivals. Brand identities (`BRAND_IDENTITY_FIELDS`) store
guidelines, mascots, approved colors, typography, and marketing rules.
Style packs (`STYLE_PACK_FIELDS`) bundle art/animation style, color
palette, prompt fragments, and consistency rules for Agent 14.

---

## 4. Relationship engine

`RelationshipEngine` (`services/character_universe/relationships.py`) maintains
a social graph as first-class persisted records:

- Types: family, friend, enemy, rival, mentor, student, romantic, teammate,
  member_of, historical
- Strength (0–100) with auditable history
- `relationship_context()` produces human-readable summaries for script
  integration payloads

---

## 5. Memory system

`CharacterMemorySystem` (`services/character_universe/memory.py`) appends
into per-character memory categories: events, relationships, achievements,
failures, goals, knowledge, personality evolution, growth log. When a
category exceeds `memory_size` (configurable), oldest entries compact into
a summary — long-term growth is preserved, detail is bounded.

---

## 6. Continuity engine

`ContinuityEngine` (`services/character_universe/continuity.py`) is the
studio's contradiction detector:

1. **Appearance history** — every content appearance logs outfit, location,
   voice, visual signature, and emotional state.
2. **Catalog audit** — duplicate characters, missing references, timeline
   errors, relationship errors, lore violations, visual/voice/brand drift.

Findings are `ContinuityIssue` dicts (severity `error` or `warning`),
filtered by `continuity_strictness` (`strict` | `standard` | `relaxed`).

---

## 7. Franchise management

`FranchiseManager` (`services/character_universe/franchise.py`) supports
series, seasons, episodes, spin-offs, collections, educational programs,
channels, brand shows, and shared universes. Performance metrics flow IN from
Analytics/Optimization via the orchestrator — this module only stores and
serves them.

---

## 8. Story Bible

`build_bible()` (`services/character_universe/bible.py`) generates a
canonical snapshot: characters, relationships, locations, organizations,
canon events, franchises, style packs, and open continuity issues. The bible
is a **view**, never a second source of truth.

---

## 9. Integration payloads

| Builder | Context key | Consumer |
|---|---|---|
| `script_context_for()` | `character_script_contexts` | Script Generation |
| `creative_context_for()` | `character_creative_context` | Creative Studio |
| `asset_requests_for()` | `character_asset_requests` | Universal Asset Generation (Agent 14) |
| `optimization_payload()` | `character_performance_payload` | Optimization Laboratory |
| `continuity_report()` | `character_continuity_report` | QA / orchestrator |
| `build_bible()` | `story_bible` | any downstream stage |

Asset requests carry definitions, reference prompts, style packs, and
consistency rules — **never** generated media files.

---

## 10. Configuration

`CharacterUniverseConfig` (`services/character_universe/config.py`):

| Setting | Default | Purpose |
|---|---|---|
| `max_characters` / `max_universes` | 0 (unlimited) | Hard limits |
| `memory_size` | 200 | Per-category memory cap |
| `continuity_strictness` | `standard` | Error/warning policy |
| `duplicate_name_threshold` | 0.92 | Name similarity flag |
| `versioning_enabled` | true | Bump version on update |
| `archive_instead_of_delete` | true | Soft-delete policy |
| `brand_rules` / `lore_rules` / `universe_rules` | [] | Rule packs for validators |

---

## 11. Persistence

JSON collections under `data/character_universe/` — one directory per entity
kind (`characters`, `universes`, `relationships`, `locations`,
`organizations`, `canon_events`, `appearances`, `franchises`,
`brand_identities`, `style_packs`). Entity ids are file keys; display
`name` fields are never overwritten.

---

## 12. Extension guide

1. **New character fields** — append to `CHARACTER_FIELDS` and
   `_CHARACTER_DEFAULTS` in `models.py` (additive only).
2. **New world entity** — add `build_*` + `*_FIELDS` in `world_models.py`,
   register in `registry._BUILDERS`, add a collection in `store.COLLECTIONS`.
3. **New continuity check** — add a `_check_*` method in `continuity.py`
   and call it from `validate_all()`.
4. **New integration payload** — add a builder in `integrations.py` and
   append the key to `CharacterUniverseEngine.output_contract`.
5. **New provider** — never required for core IP; voice/asset providers
   consume this engine's payloads, not the other way around.

---

## 13. Tests

| File | Coverage |
|---|---|
| `tests/test_character_universe.py` | Service-level: CRUD, relationships, memory, continuity, franchise, bible, versioning |
| `tests/test_character_universe_engine.py` | Engine contracts, orchestrator stage, integration payloads, Directive #1 safety |

Run: `python3 -m pytest tests/test_character_universe.py tests/test_character_universe_engine.py`

---

## 14. Long-term vision

This engine should eventually enable Generational to build:

- Original animated series and children's franchises
- Educational mascots and recurring AI presenters
- Story universes, movies, games, books, merchandise
- Licensable intellectual property

The Character & Universe Engine is the permanent memory of the entire
creative company.
