# Generational V1 Validation Program

**Status:** Active — Validation & Optimization phase  
**Package:** `services/validation_program/`  
**CLI:** `scripts/validation_program.py`

Architecture is **frozen**. This program measures real pipeline outputs — it does not add engines or redesign the system.

Composes: Production Operations · Creative Excellence · Audience Intelligence · existing `production_validation` evaluators · GenOS reports.

---

## Goal

Prove Generational can repeatedly produce high-quality educational Shorts using the current stack.

Success = consistency, reliability, quality — not more software surface area.

---

## 100-video test suite

10 categories × 10 topics:

Biology · Physics · Astronomy · Medicine · Psychology · Technology · Artificial Intelligence · History · Engineering · Nature

```bash
python scripts/validation_program.py catalog
python scripts/validation_program.py run --limit 1
python scripts/validation_program.py run --categories biology physics --limit 4
# Resume-friendly: skips validation_ids already in the library
python scripts/validation_program.py run --limit 10 --offset 5
```

Publishing remains **disabled** during validation runs.

---

## Measurements (every production)

Research Accuracy · Psychology Effectiveness · Hook Strength · Story Flow · Educational Clarity · World Continuity · Visual Quality · Cinematic Quality · Narration Quality · Caption Accuracy · Audio Mix · Thumbnail Appeal · Packaging · Overall Professionalism

Scores compose Creative Excellence, Audience Intelligence, and ops reports — no duplicate scorers.

---

## Validation Library

`data/productions/_validation/validation_program/`

Per run folder:

- `Production_Report.json`
- `Creative_Director_Review.md`
- `Audience_Intelligence_Review.md`
- `Failure_Log.json`
- `Optimization_Suggestions.json`
- `Production_Metrics.json`

Searchable index: `VALIDATION_LIBRARY.db` + `VALIDATION_LIBRARY.json`

```bash
python scripts/validation_program.py library --query octopus
python scripts/validation_program.py ingest ops_18fff5d4bd --category biology
```

---

## Bottlenecks & recommendations

```bash
python scripts/validation_program.py bottlenecks
```

Detects slowest modules, weakest creative dims, failure hotspots, common render/visual/narration/script/research issues.

Every recommendation includes:

| Field | Meaning |
|-------|---------|
| Problem | What failed |
| Evidence | Measured signal |
| Expected Improvement | Outcome if tuned |
| Priority | P0 / P1 / P2 |
| Estimated Impact | Relative weight |

**`architecture_change_allowed: false` always.**

---

## Executive dashboard

```bash
python scripts/validation_program.py dashboard
```

Writes `VALIDATION_EXECUTIVE_DASHBOARD.md` and `EXECUTIVE_VALIDATION_DASHBOARD.json` with:

Videos produced · creative/program averages · production & render times · viewer/opportunity/hook averages · success/failure rates · top/weak categories · highest-priority improvement

---

## Relation to Production Validation Suite

The earlier 10-domain suite (`services/production_validation`, `scripts/run_content_validation.py`) remains the smoke suite.

This V1 Validation Program scales that approach to **100 topics**, persistent library, bottleneck analytics, and the executive board — still using `run_studio_ops` only.

---

## Begin here

1. Ingest known good ops runs  
2. Run small batches (`--limit 1` … `--limit 5`)  
3. Review dashboard + bottlenecks after each batch  
4. Continue until library hits 100 and quality is consistent  

```bash
./venv/bin/python -m pytest tests/test_validation_program.py -q
```
