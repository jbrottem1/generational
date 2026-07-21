# Autonomous Optimization & Experimentation Engine (Version 4.0)

## Purpose

Never settle for the first acceptable video.

Every production is an **experiment**: generate multiple candidates, score them, self-critique, revise the winner, predict performance, store lessons, and make the next production smarter.

## Engine key

`optimization_lab` · version `4.0.0`  
(Graduates the Agent 13 FutureEngine stub into a live self-improving studio.)

## Modules

| # | Module | Role |
|---|--------|------|
| 1 | Multi-Version Generation | Variants A–E varying hook, narration, scene order, visuals, music, camera, captions, thumbnail, title, SEO |
| 2 | Automatic Comparison | 10-metric scoring + ranked leaderboard |
| 3 | Self-Critic | Weak scenes, pacing, narration, SEO, missed opportunities |
| 4 | Revision Loop | Auto-revise until score ≥ **98** or max rounds (default 4) |
| 5 | Performance Predictor | CTR, AVD, completion, share/like/comment/sub + CI + reasons |
| 6 | Knowledge Database | Best hooks, pacing, cameras, narration, thumbnails, captions, palettes |
| 7 | Experiment History | Searchable runs: topic, winner, rejects, lessons |
| 8 | Human Review Mode | Optional approve / reject / edit before publish |
| 9 | Executive Dashboard | Studio board: optimized videos, CTR, retention, topics, hooks |
| 10 | Continuous Improvement | Persist winning patterns; measurable early vs recent lift |

## Pipeline integration (backward compatible)

- `intelligence` / `full_content` / `media_production`: after `studio_render`, before `production_qa`
- Executive Orchestrator **export** stage: `optimization_lab`
- Classic orchestrator stage `optimization` already pointed at this key
- Additive context fields only

### Context fields written

- `optimization_package`
- `optimization_score` / `optimization_passed`
- `optimization_winner`
- `optimized_hook` / `optimized_title` / preferred style axes
- Context summary: `optimization_report`, `optimization_recommendations`, `optimization_dashboard`

## Production QA

New category: **`optimization`** (weight 1.05).

Revision owners: `optimization_lab`, `ranking`, `critic`, `revision`.

Legacy productions without a package fall back to psychology / SEO / retention / render scores.

## Persistence

| File | Contents |
|------|----------|
| `data/analytics/optimization_patterns.json` | Winning craft patterns |
| `data/analytics/optimization_experiments.json` | Experiment history |

## Human review

Set `require_human_review=True` in context to keep status `pending_review` instead of `auto_approved`.

## Tests

```bash
./venv/bin/python -m pytest tests/test_optimization_lab.py -q
./venv/bin/python scripts/verify_optimization_lab_e2e.py
```

Reports: `data/productions/_validation/optimization_lab/`

## Success criteria

The OS functions as a **self-improving creative studio**: each production leaves ranked variants, a critique, a revised winner ≥98, predictions, and stored lessons that bias the next run — without manual prompt changes.
