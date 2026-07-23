# Production Acceptance Testing System (V1.0)

Prove — do not improve — that Generational is production-ready after every major update.

Treat every change as if the platform serves millions of creators.

## Quick start

```bash
# CI / every update (smoke)
python scripts/verify_production_acceptance.py --mode smoke

# Pre-release gate
python scripts/verify_production_acceptance.py --mode full

# Capacity / nightlies
python scripts/verify_production_acceptance.py --mode stress

# Pytest entry (smoke integrity + fast subset)
python -m pytest tests/test_production_acceptance.py -q
```

```python
from services.production_acceptance import run_acceptance_suite

result = run_acceptance_suite(mode="smoke")
assert result["passed"]
```

## Test categories

| # | Category | What it proves |
|---|---|---|
| 1 | Pipeline Integrity | Engines load, imports, workflows, stage order, config |
| 2 | Video Generation | Multi-category productions (10 niches) |
| 3 | Duration | 10s→5min timing accuracy |
| 4 | Platform | Shorts/TikTok/Reels/X/Long-form contracts |
| 5 | Stress | 1/5/20 videos, 50 queued jobs, resources, recovery |
| 6 | Quality | Hook→SEO + retention/CTR/completion + overall |
| 7 | Recovery | Missing media, timeout, LLM fail, disk, corrupt, renderer |
| 8 | Output Validation | Report, SEO, captions, thumbnail, MP4/metadata package |

## Modes

- **smoke** — bounded samples for every PR / deploy gate  
- **full** — complete category × duration × platform matrix  
- **stress** — full + capacity (20 videos, 50 queue jobs)

## Dashboard

`data/productions/_acceptance/ACCEPTANCE_DASHBOARD.json`

- Pass % / Failure %  
- Average quality  
- Average / fastest / slowest render  
- Common failures  
- Recovery success  
- Historical trends + improvement deltas  

## History

Every run is stored:

- `data/productions/_acceptance/runs/{run_id}.json`  
- `data/productions/_acceptance/ACCEPTANCE_HISTORY.json`  

Trends show readiness improving or regressing over time.

## Success criteria

The suite automatically proves production readiness **without manual inspection**.

Gate rule: `run_acceptance_suite(...); assert result["passed"]`

## Package

```
services/production_acceptance/
  catalog.py      # categories, platforms, modes
  models.py       # results + history persistence
  integrity.py    # category 1
  generation.py   # categories 2–4
  stress.py       # category 5
  quality.py      # category 6
  recovery.py     # category 7
  output.py       # category 8
  dashboard.py
  runner.py
```
