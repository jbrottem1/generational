# World Builder Troubleshooting

## Wrong world selected

- Prefer `--world-type` or `existing_world_id`
- Short tokens are whole-word matched (`ai` will not match `detail`)
- Re-seed library: `python scripts/world_builder.py seed`

## Validation fails: floating objects

Every prop needs `surface` and `anchored: true` (floor/desk/wall/ground/…).

## Validation fails: object moved without explanation

Use `apply_state_event(..., "object_moved", {object_id, position, reason})` before building the next Environment Package.

## Cinematic fields overwritten?

World attach **must not** clear existing `camera` / `lighting` when present. If you see prescriptions inside `environment_packages[].cinematic_prescriptions`, treat as a bug — must stay `null`.

## Missing assets

`asset_requirements.missing` is intentional handoff to Asset Intelligence / media pipeline — World Builder does not download or generate media.

## State feels stale

```bash
python scripts/world_builder.py reset-state --world-id WORLD-AI_LABORATORY --production-id your_id
```

## Pipeline regression

World Builder adds candidate fields only (`world_package`, `environment_packages`, per-scene `environment_package`). It does not register a new production stage or renderer.
