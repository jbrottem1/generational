# Generational V1.0 RC1 — Open Issues

**Date:** 2026-07-14  
Issues remaining after safe fixes (`SAFE_FIXES.md`). Do not treat “ops finished” as “shippable” until Critical items close.

---

## Critical

### OI-C1 — Production MP4 materialization rate near zero

| Field | Value |
|-------|-------|
| **Title** | Production exports rarely produce a playable MP4 |
| **Description** | Ops soft-continues and packages metadata while `export.video_exists` stays false for nearly all historical runs |
| **Evidence** | 0 / 93 ops statuses with `video_exists=true`; 78× `mp4_not_yet_materialized` |
| **Risk** | Ship non-videos; train learning loops on fake success |
| **Impact** | Blocks V1.0 factory claim |
| **Estimated effort** | 2–4 days |
| **Priority** | Critical |
| **Recommendation** | In production mode, drive existing ffmpeg/studio export until file verifies (reuse GenOS verified_export helpers); keep smoke opt-in via `allow_missing_mp4` |
| **Status** | Open (truth flag fixed in SF-05; materialization not) |

### OI-C2 — Historical studio_render TypeError class

| Field | Value |
|-------|-------|
| **Title** | `studio_render: 'str' object has no attribute 'get'` |
| **Description** | Prior runs failed render after retries when nested packages/candidates were strings |
| **Evidence** | 50 ops error occurrences; partial coercions exist in `studio_render/director.py` + engine |
| **Risk** | Intermittent render failure under degraded upstream shapes |
| **Impact** | High on deliverable rate |
| **Estimated effort** | 0.5–1.5 days (regression harness + remaining call sites) |
| **Priority** | Critical |
| **Recommendation** | Add fixture reproducing string nested packages; harden remaining `.get` call sites without changing creative logic |
| **Status** | Partially mitigated in code; reopen if new runs reproduce |

### OI-C3 — Ops resume does not skip completed stages

| Field | Value |
|-------|-------|
| **Title** | `resume=True` performs full re-run |
| **Description** | Queue recovery passes resume IDs, but orchestrator only annotates notes |
| **Evidence** | `orchestrator.py` resume notes; no `load_ops_status` skip loop |
| **Risk** | Double API spend; cannot recover mid-pipeline cheaply |
| **Impact** | Continuous operation cost/reliability |
| **Estimated effort** | 1–2 days |
| **Priority** | Critical |
| **Recommendation** | Load prior status; skip `succeeded` stages; reuse artifacts in context (workflow_executor already has a pattern to mirror, not replace ops) |
| **Status** | Open (SF-08 documents honesty only) |

---

## High

### OI-H1 — Provider health before batch drain

| Field | Value |
|-------|-------|
| **Title** | Batches start despite dead models / quota |
| **Description** | Anthropic/OpenAI failures discovered mid-run |
| **Evidence** | Prior 404/429 logs; pin fixed (SF-03) but no preflight |
| **Risk** | Wasted cycles; weak SEO packages |
| **Impact** | High on packaging quality |
| **Estimated effort** | 0.5–1 day |
| **Priority** | High |
| **Recommendation** | Soft probe into GenOS `SYSTEM_HEALTH` before queue drain |
| **Status** | Open |

### OI-H4 — Animation unavailable on all sampled ops

| Field | Value |
|-------|-------|
| **Title** | Animation always soft-skipped |
| **Description** | Warning on 100% of sampled statuses; motion scores can remain high |
| **Evidence** | 93 / 93 `animation unavailable — continued` |
| **Risk** | False cinematic excellence |
| **Impact** | Creative optimization misleads |
| **Estimated effort** | 0.5 day |
| **Priority** | High |
| **Recommendation** | Cap motion/cinematic dims when animation skipped; do not add animation engine |
| **Status** | Open |

### OI-H5 — Production queue JSON lacks file locking

| Field | Value |
|-------|-------|
| **Title** | Race on `PRODUCTION_QUEUE.json` |
| **Description** | Read-modify-write without lock |
| **Evidence** | `services/production_operations/queue.py` |
| **Risk** | Lost jobs under concurrent CLI/UI |
| **Impact** | Operational correctness |
| **Estimated effort** | 0.5 day |
| **Priority** | High |
| **Recommendation** | Atomic replace + exclusive lock |
| **Status** | Open |

### OI-H8 — Thumbnail / packaging quality floor

| Field | Value |
|-------|-------|
| **Title** | Weak thumbnail appeal in Validation Program |
| **Description** | Mean thumbnail ~55 across early library |
| **Evidence** | Validation executive dashboard P0 |
| **Risk** | Distribution failure despite strong hooks |
| **Impact** | Growth |
| **Estimated effort** | 1–2 days |
| **Priority** | High |
| **Recommendation** | Tune existing Publishing Intelligence / director thumbnail inputs; measure via validation batches |
| **Status** | Open |

### OI-H9 — Validation success must require deliverable

| Field | Value |
|-------|-------|
| **Title** | Validation Program can report 100% success without MP4 |
| **Description** | Scorecards treated soft ops success as program success |
| **Evidence** | Prior validation dashboard vs export reality |
| **Risk** | False progress to 100-video goal |
| **Impact** | High on V1.0 proof |
| **Estimated effort** | 0.5 day |
| **Priority** | High |
| **Recommendation** | Gate `success` on `video_exists` / packaged export bytes in production mode |
| **Status** | Open |

---

## Medium

### OI-M1 — Document single supported production path
### OI-M2 — Root docs for Research / Psychology / Script / Scene
### OI-M3 — Scene-stage regression tests
### OI-M4 — Channel dual-store doctor CLI
### OI-M5 — Label score scales (98 vs 70) in executive reports
### OI-M6 — Voice cache on resume/retry
### OI-M7 — Archive historical root markdown
### OI-M8 — Relative paths in channel production index

_(Each: effort ≤ 1 day; see prior LOW_PRIORITY_FIXES.md for detail.)_

---

## Low

### OI-L1 — Estimated revenue placeholder labeling on Channel dashboard
### OI-L2 — Opportunistic dead Cloud string cleanup during path work

---

## Closed in this RC1 pass

| ID | Via |
|----|-----|
| Circular AI Director import | SF-01 |
| Pytest integration mark warning | SF-02 |
| Stale Anthropic model pin | SF-03 |
| Videos path spelling split (resolver) | SF-04 |
| Always-true ops success without MP4 | SF-05 |
| String candidate crash in export step | SF-06 |
| Plaintext channel credentials persist | SF-07 |
| Misleading resume silence | SF-08 |
