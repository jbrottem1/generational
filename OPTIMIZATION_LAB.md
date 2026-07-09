# Generational — Experimentation & Optimization Laboratory (Agent 13)

The company's optimization and experimentation department. The laboratory
generates no content of its own — it maximizes the quality and predicted
performance of every future piece of content by generating alternatives,
predicting performance, ranking competing strategies, and recommending the
strongest version to the Production Pipeline.

**Mission:** evolve Generational from *"generating content"* to
*"selecting the strongest version of every piece of content before it is
published."*

- Engine: `optimization_lab` (`engines/optimization_lab.py`)
- Logic: `services/optimization/`
- Stage: `optimization` (on demand always; scheduled after the quality
  gate via `enable_optimization_stage()`)
- Contracts: `DATA_CONTRACTS.md` §8.2 (`services/optimization/models.py`
  field tuples are the testable contract)
- Tests: `tests/test_optimization_lab.py`

---

## 1. Boundaries (non-negotiable)

The laboratory MUST NOT directly modify the Psychology, Script, Visual
Intelligence, Creative Studio, Voice & Audio, Render, SEO, Publishing, or
Analytics engines. It **consumes their outputs** (scores, script variants,
optimized titles, thumbnail concepts) and **returns structured
recommendations only**. No engine-to-engine communication — everything
flows:

```
Pipeline Orchestrator
   ↓
Engine Registry (key: optimization_lab)
   ↓
ContentPackage / ProductionPackage (`optimization_package` slot)
```

Write zone: the `optimization_package` slot plus the
`optimization_report` / `optimization_recommendations` context keys.
Every other field is read, never mutated. Enforced by
`tests/test_architecture.py` (Architecture Directive #1).

---

## 2. Experiment architecture

```
run_optimization(context)                       ← engine.run() / stage
   │
   ├─ collect items (unified_packages → ideas → selected_ideas → candidates)
   │
   └─ for each item × active experiment type:
        1. generate_variants()      control + upstream + heuristic variants
        2. validate                 duplicates, empty content, group size
        3. create_experiment()      DRAFT → (SCHEDULED) → RUNNING
        4. rank_variants()          weighted scoring + historical priors
        5. evaluate()               Welch's z-test → ExperimentResult
        6. build_recommendation()   winner → structured recommendation
        7. resolve_conflicts()      one recommendation per target slot
   │
   ├─ item["optimization_package"]              per-item slot
   ├─ context["optimization_report"]            the Optimization Report
   └─ context["optimization_recommendations"]   experiment_type → winner
```

### Core objects (`services/optimization/models.py`)

| Object | Field tuple | Meaning |
|---|---|---|
| Variant | `VARIANT_FIELDS` | one competing alternative: unique id, version, content, metadata, generation source, confidence, score + breakdown, rank |
| VariantGroup | `VARIANT_GROUP_FIELDS` | variants competing for one decision + validation warnings |
| Experiment | `LAB_EXPERIMENT_FIELDS` | type, mode, status, variant group, runs, result, platform/region/brand routing, provider, confidence floor |
| ExperimentRun | `EXPERIMENT_RUN_FIELDS` | one execution: variant_id → score, warnings, timing |
| ExperimentResult | `EXPERIMENT_RESULT_FIELDS` | winner, losers, ranked, confidence, expected lift, method (predicted / observed) |
| Recommendation | `OPTIMIZATION_RECOMMENDATION_FIELDS` | winning content, target slot, alternatives, confidence, lift, warnings |
| Report | `OPTIMIZATION_REPORT_FIELDS` | the per-run Optimization Report |

### Experiment types (19 built-in + future)

hook · title · description · thumbnail · caption · narration_style ·
animation_style · visual_pacing · scene_ordering · music_style ·
sound_design · cta_placement · publishing_time · publishing_schedule ·
localization · language · brand_style · character_style ·
platform_formatting

Future types need **no code**: `configure(extra_experiment_types=["x"])`
registers them everywhere types are validated.

### Test modes (`EXPERIMENT_MODES`)

`ab` · `multivariate` · `sequential` · `platform` · `regional` · `brand`
· `lifecycle` — all prepared in the data model and the provider
interface. Until platform APIs support real split tests, every experiment
runs as a *predicted* (pre-publish) comparison; observed results enter via
`record_observed_scores()`.

### Concurrency & scheduling

`ExperimentScheduler` keeps running experiments inside
`max_concurrent_experiments`; overflow experiments defer to SCHEDULED and
release oldest-first through `run_due_experiments()` when capacity frees
up. `ExperimentHistory` persists everything to
`data/optimization/experiments.json` — concluded experiments are the
laboratory's institutional memory.

---

## 3. Variant lifecycle

```
generated (control | upstream | heuristic | provider | manual)
   → validated   (duplicates dropped, empty content flagged)
   → scored      (14-input weighted composite + breakdown)
   → ranked      (best-first, history-aware, deterministic tie-breaks)
   → concluded   (winner | loser in an ExperimentResult)
   → remembered  (winners → Agent 9 long-term memory → future priors)
```

Every variant carries: unique `variant_id`, `version`, `metadata`,
`generation_source`, and generation `confidence`. Upstream work is never
redone — script variants, SEO optimized titles, and thumbnail concepts
join the pool as `upstream` variants and compete on equal terms.

---

## 4. Scoring model

`score_variant()` blends fourteen inputs (`SCORING_INPUTS`) through the
shared `weighted_blend` formula:

| Input | Source |
|---|---|
| psychology / virality / seo / trend | upstream scores already on the item (read-only) |
| historical_performance | priors from the learning bridge (neutral 50 without history) |
| brand_fit / audience_match | brand vocabulary + keyword overlap heuristics |
| retention / ctr / engagement predictions | the active `PredictionModel` |
| revenue_prediction | explicit placeholder (neutral 50) until monetization lands |
| confidence | the variant's generation confidence |
| platform_suitability / localization_suitability | platform fit + translatability heuristics |

Weights live in `OptimizationConfig.scoring_weights` — **data, not code**.
The Learning Engine (or an operator) retunes them via `configure()`
without touching scoring logic. Ranking strategy is also configurable:
`"score"` (composite only) or `"score_with_history"` (composite blended
with historical priors by `history_influence`).

Prediction models are pluggable: subclass `PredictionModel`, call
`register_prediction_model()`, activate with
`configure(prediction_model="<key>")`. The default heuristic model is
deterministic — same input, same numbers, no API keys.

---

## 5. Recommendation engine

Only winners with a usable result become recommendations. Each carries the
winning content, the ContentPackage `target_slot` it improves, up to three
ranked alternatives, statistical confidence, expected lift, and explicit
warnings (low confidence, group validation findings, conflicts).
`resolve_conflicts()` guarantees one recommendation per target slot — the
higher-confidence winner stands, the superseded one is preserved as a
flagged signal.

### Pipeline query surface

```python
from services.optimization import get_optimization_lab

lab = get_optimization_lab()
lab.best_hook()               # freshest high-confidence hook winner
lab.best_title()              # … title
lab.best_thumbnail()          # … thumbnail
lab.best_caption()            # … caption
lab.best_narration_style()    # … narration style
lab.best_cta()                # … CTA placement
lab.best_publishing_window()  # … publishing time
lab.best_content_package()    # experiment_type → best of everything
```

All answers come from concluded experiment history — structured
recommendations only, never engine calls. Empty history returns
`None` / `{}`; callers never need special cases.

---

## 6. Learning loop

Integration with Analytics & Continuous Learning (Agent 9) is
bidirectional and store-mediated (never engine-to-engine):

1. **History in:** `historical_priors()` mines the cumulative analytics
   store (the same `mine_patterns()` insight math the Learning Engine
   trusts) into value → prior-score maps per experiment type;
   `experiment_winner_priors()` adds concluded laboratory winners
   (winning confidence as a boost, confirmed losers as a penalty).
   `combined_priors()` overlays both — experiment outcomes win.
2. **Priors → rankings:** priors feed the `historical_performance`
   scoring input and (under `score_with_history`) the ranking blend, so
   historical winners rise in every future ranking.
3. **Outcomes out:** COMPLETED experiments are remembered in Agent 9's
   append-only long-term memory (`EXPERIMENT_OUTCOMES` category) — every
   other consumer of that memory benefits.

Cold start: below `min_history_samples` records, priors are empty and
rankings rest purely on predictions — the laboratory degrades, never
blocks.

---

## 7. Optimization Report

Every run emits one report (`OPTIMIZATION_REPORT_FIELDS`):

- winning variants + losing variants (with experiment attribution)
- confidence scores (per recommendation + run average)
- expected performance lift (per experiment + run average)
- experiment summary (per-type counts and outcomes)
- historical trends (top insights from the learning bridge)
- every recommendation issued + all degradation warnings

`render_report_text(report)` renders it for humans.

---

## 8. Quality & graceful degradation

| Condition | Behavior |
|---|---|
| duplicate variants | deduped at creation; flagged in group warnings |
| invalid experiment type/mode | `ValueError` at creation; the stage catches it and degrades to a warning |
| missing assets / empty content | variants excluded; flagged in warnings |
| low confidence winner | recommendation still issued, explicitly flagged; experiment status LOW_CONFIDENCE |
| insufficient variants/samples | experiment status INSUFFICIENT_DATA — no recommendation |
| insufficient history | priors empty; predictions carry the ranking |
| conflicting recommendations | resolved by confidence; conflicts recorded in warnings |
| provider failure | experiment FAILED with diagnostics; other experiments unaffected |
| prediction model failure | per-type warning; other types complete (`partial` status) |
| empty context | `no_items` report — never a failure |

The stage never crashes the pipeline.

---

## 9. Configuration

Everything tunable is data (`services/optimization/config.py`), loaded
from `data/optimization/config.json` or set via `configure(**overrides)`:

| Knob | Default |
|---|---|
| `variant_counts` / `default_variant_count` / `max_variants_per_type` | 20 hooks, 15 titles, 25 thumbnails, 8 captions, 5 narration styles, 10 CTAs · 6 · 50 |
| `duplicate_similarity` | 0.9 |
| `scoring_weights` | see `DEFAULT_SCORING_WEIGHTS` |
| `ranking_strategy` / `history_influence` | `score_with_history` / 0.15 |
| `prediction_model` | `heuristic` |
| `min_winner_confidence` / `low_confidence_threshold` | 60 / 40 |
| `min_history_samples` | 3 |
| `max_concurrent_experiments` / `max_experiments_per_run` | 10 / 40 |
| `active_experiment_types` | hook, title, thumbnail, caption, narration_style, cta_placement, publishing_time |
| `extra_experiment_types` | [] (future types register here) |
| `enabled_providers` / `disabled_providers` | all / none |

---

## 10. Extension guide

- **New experiment type:** `configure(extra_experiment_types=["my_type"])`.
  Optionally add heuristic templates in
  `services/optimization/variants.py` and a slot mapping in
  `TARGET_SLOTS` — without them the type still runs with minimal option
  variants.
- **New scoring input:** append to `SCORING_INPUTS` +
  `DEFAULT_SCORING_WEIGHTS` (additive-only), compute it in
  `scoring.score_variant()`.
- **New prediction model:** subclass `PredictionModel`, register, activate
  via config. ML models drop in with zero scoring-engine changes.
- **New A/B platform backend:** subclass `ExperimentProvider`
  (`start_experiment` / `fetch_results`, declare `platforms` + `modes`),
  register with `register_experiment_provider()`; feed observed results
  through `ExperimentManager.record_observed_scores()`.
- **New ranking logic:** add a strategy branch in
  `scoring.rank_variants()` and select it via
  `configure(ranking_strategy=...)`.
- **Scheduling the stage:** `enable_optimization_stage(after="quality")`
  (idempotent); `disable_optimization_stage()` removes it while keeping
  on-demand runs available.

Contract rules: everything is additive-only from v1.0 — append fields,
never remove, rename, or repurpose (see `DATA_CONTRACTS.md` §9).
