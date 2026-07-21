# Viewer Retention & Cinematic Excellence Engine (Version 2.0)

## Purpose

Shift Generational from “produce a video” to “produce a video people finish, share, and trust as professional educational media.”

This engine improves every stage **before export** by unifying ten modules into one package, then auto-polishing until the overall production score reaches **≥ 98**.

Quality always wins over speed.

## Engine key

`viewer_retention` · version `2.0.0`

## Modules

| # | Module | Responsibility |
|---|--------|----------------|
| 1 | Hook Engine | ≥5 hook styles (question, shock statistic, contradiction, visual mystery, impossible statement, common myth, immediate payoff, open loop); score; pick best |
| 2 | Visual Pacing | Cut duration from attention, density, movement, importance; 2s/3s/montage/pause/zoom/motion rhythms |
| 3 | Cinematic Camera | Narration-matched motions (slow push, macro, orbit, parallax, whip pan, rack focus, crash zoom, dolly, tilt, reveal, tracking, drone, Ken Burns, handheld) — never random |
| 4 | Narration | Educator cadence, pauses, emphasis, varied speaking rate |
| 5 | Sound Design | Ambience, music intensity curve, whooshes, risers, impacts, intentional silence, ducking |
| 6 | Captions | Dynamic sizing, keyword highlight, safe zones, 9:16 + 16:9 |
| 7 | Visual Intelligence 2.0 | Prefer NASA/NOAA/ESA/USGS/NIH/gov/museum; rank educational value, beauty, relevance, emotion, composition, color, confidence |
| 8 | Retention Analyzer | Drop-off at 3 / 10 / 20 / 40 / ending; revise weak sections |
| 9 | Production Polish | Detect awkward cuts, flat pacing, weak narration, audio imbalance, caption overlap, weak assets; auto-fix |
| 10 | Quality Report | Hook/visuals/narration/psychology/retention/sound/captions/animation/education/entertainment/SEO + CTR, AVD, completion, share, subscribe |

## Pipeline integration (backward compatible)

- Registered in `engines/__init__.py`
- Inserted **after** `cinematography` and **before** `voice_audio` in `intelligence` and `full_content` workflows
- Executive Orchestrator `animation` stage: `cinematography` → `viewer_retention` → `animation`
- Existing engines and context keys unchanged; V2 fields are **additive**

### Context fields written

- `viewer_retention_package`
- `viewer_retention_score` / `cinematic_excellence_score`
- `viewer_retention_passed`
- `retention_predictions`
- `v2_selected_hook` / may upgrade `hook` when stronger
- Enriches `cinematography_plan` with `v2_motion` metadata
- Adds `visual_package.caption_plan_v2` and `pacing_plan_v2`

## Production QA

New category: **`retention`** (weighted 1.1 in overall).

Revision owners route failures to `viewer_retention` (also listed on cinematography, narration, audio, psychology).

## Continuous Learning

`viewer_retention` included in learning consult engine guidance and dimension targets (hook, camera, length, psychology).

## Threshold

`EXCELLENCE_PASS_THRESHOLD = 98` with up to `MAX_POLISH_ROUNDS = 4` automatic polish passes.

## Tests

```bash
./venv/bin/python -m pytest tests/test_viewer_retention.py -q
./venv/bin/python scripts/verify_viewer_retention_e2e.py
```

Reports land in `data/productions/_validation/viewer_retention/`.

## Design rules

1. Never optimize for speed if quality suffers.
2. Camera movement must support narration.
3. Prefer authentic scientific / government imagery.
4. Silence and sound are intentional story tools.
5. Auto-revise weak retention sections before export.
