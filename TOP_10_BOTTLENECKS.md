# Generational V1 — Top 10 Bottlenecks

**Evidence:** 25 V1 Launch pilot runs (2026-07-14) + RC1 ops history where listed  
**Rule:** Only issues that **repeatedly** reduced reliability or quality. No speculative features.

Ranked by impact on **publication readiness**, then on **cycle time / honesty**.

---

### 1. MP4 never materializes (P0 — blocking)

| | |
|--|--|
| **Repeat rate** | **25 / 25** (`video_exists=false`) |
| **Impact** | Success rate 0%; cannot publish or claim media factory |
| **Evidence** | Launch pilot library; render stage avg ~4ms |
| **Action** | Fix existing export/ffmpeg materialization in production mode |

### 2. Animation unavailable on every run (P0 — quality honesty)

| | |
|--|--|
| **Repeat rate** | **25 / 25** warning |
| **Impact** | Cinematic/motion claims unreliable |
| **Evidence** | Failure logs in every pilot run folder |
| **Action** | Cap motion scores when animation skips; rely on existing motion-graphics path |

### 3. Render/export path is metadata-only (P0)

| | |
|--|--|
| **Repeat rate** | 25 / 25 (paired with #1) |
| **Impact** | “Rendering complete” without encode cost or file |
| **Evidence** | Avg render-related time ~9ms vs research/voice ~3–4s |
| **Action** | Ensure production mode invokes real encode, not smoke package |

### 4. Research latency (P1 — cycle time)

| | |
|--|--|
| **Repeat rate** | All 25 |
| **Impact** | Slowest stage avg **~3889 ms** |
| **Evidence** | Stage timing rollup |
| **Action** | Cache/reuse research within topic; timeouts — no new research engine |

### 5. Voice generation latency (P1 — cycle time / cost)

| | |
|--|--|
| **Repeat rate** | All 25 |
| **Impact** | Avg **~3733 ms**; API spend on restarts |
| **Evidence** | Stage timing |
| **Action** | Prefer existing narration cache on retries/resume |

### 6. Script generation latency (P1 — cycle time)

| | |
|--|--|
| **Repeat rate** | All 25 |
| **Impact** | Avg **~3568 ms** |
| **Evidence** | Stage timing |
| **Action** | Keep; optimize only if MP4 path fixed and batch SLA requires it |

### 7. SEO / packaging stage friction (P1)

| | |
|--|--|
| **Repeat rate** | High historically (provider 404/quota); pilot avg SEO **~2215 ms** |
| **Impact** | Packaging quality + wasted retries when providers fail |
| **Evidence** | RC1 live logs; pilot stage times |
| **Action** | Provider health preflight before batch (already partially pinned) |

### 8. World continuity soft floor (P1 — quality)

| | |
|--|--|
| **Repeat rate** | Mean **65** across 25 |
| **Impact** | Lowest creative dimension in pilot scorecard |
| **Evidence** | Launch executive / bottleneck recommendations |
| **Action** | Tune existing world_builder preferences — not a new world engine |

### 9. Ops resume is full re-run (P1 — recovery)

| | |
|--|--|
| **Repeat rate** | Design-level; not remediated |
| **Impact** | Recovery multiplies research/voice/script cost |
| **Evidence** | RC1 orchestrator analysis; pilot did not skip stages on resume |
| **Action** | Stage-skip resume from ops status checkpoints |

### 10. Soft-continue hides deliverable failure in older dashboards (P2 — ops honesty)

| | |
|--|--|
| **Repeat rate** | Historical ops “success” with no MP4 (93-sample RC1) |
| **Impact** | False greens before RC1 truth flag |
| **Evidence** | RC1 SYSTEM_AUDIT; mitigated for new ops `success` |
| **Action** | Align GenOS / Validation / Launch dashboards on `video_exists` |

---

## Not listed (intentionally)

- New engines, new stages, speculative UI, “nice to have” motion features  
- One-off quota glitches without pilot repetition  
- Category ranking fights (spreads were <0.4 points)

---

## Bottleneck summary for leadership

**Close #1–#3 first.** Items #4–#7 are optimization after videos exist. Items #8–#10 are quality/ops honesty. Nothing else on this list justifies architecture expansion.
