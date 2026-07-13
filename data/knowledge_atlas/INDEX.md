# Generational Knowledge Atlas — Index

**Project:** Visual Intelligence · **Updated:** via `scripts/sync_atlas_from_reality.py`

## Collections (seed)

| Domain | Focus |
|--------|--------|
| biology | Organisms, systems, specimens |
| evolution | Mimicry, adaptation, arms race |
| ecology | Populations, interactions |
| astronomy | *(planned)* |
| geology | *(planned)* |
| medicine | *(planned)* |

## Current assets (from Project Reality seed)

| asset_id | Topic | Type | License |
|----------|-------|------|---------|
| hoverfly_lateral | Hoverfly Batesian mimic | photograph | CC-BY-SA |
| wasp_lateral | German wasp warning model | photograph | CC-BY-SA |
| coral_snake | Eastern coral snake | photograph | CC-BY |
| scarlet_kingsnake | Scarlet kingsnake mimic | photograph | CC-BY-SA |
| monarch_adult | Monarch butterfly | photograph | CC-BY-SA |
| viceroy_adult | Viceroy butterfly | photograph | CC-BY-SA |

## Commands

```bash
python3 scripts/sync_atlas_from_reality.py     # import Reality catalog
python3 -c "from services.knowledge_atlas import search_visuals; print(search_visuals(query='mimicry'))"
```

See `PROJECT_VISUAL_INTELLIGENCE.md` for doctrine.
