# Performance Baseline

**Owner:** Agent 28 · **Environment:** Linux CI / cloud agent pod · **Updated:** 2026-07-12

Baselines are measured **locally** where possible. Cloud agents used for audit only.

---

## Test suite

| Metric | Baseline | Target | Notes |
|--------|----------|--------|-------|
| Full pytest duration | **261 s** | < 300 s | 946 tests collected |
| Tests passed | **933** | ≥ 930 | 13 known failures |
| Pass rate | **98.6%** | ≥ 98.5% | See `REGRESSION_TEST_PLAN.md` |
| Architecture tests | Pass | Pass | Import rules enforced |

---

## Foundation Short render (smoke, `--smoke` narration)

| Episode | Render time | Duration | Export size |
|---------|-------------|----------|-------------|
| Biology 101 Reality | ~37 s | ~50 s | ~1.0 MB |
| Biology 102 Reality | ~33 s | ~47 s | ~1.1 MB |
| Biology 103 Reality | ~37 s | ~52 s | ~1.2 MB |

*Production TTS (OpenAI) adds ~5–15 s depending on beat count.*

---

## Animation / performer QC (Foundation)

| Metric | Typical | Gate |
|--------|---------|------|
| Quality overall | 77–79 | Stretch ≥ 80 |
| idle_ratio | 0.26–0.38 | 0.22–0.55 |
| walk_ratio | < 0.20 | ≤ 0.20 |
| lipsync score | ≥ 70 | ≥ 70 |

---

## Asset loading

| Operation | Baseline | Notes |
|-----------|----------|-------|
| Atlas catalog load | < 50 ms | 6 assets, cached |
| Reality image cache (PIL) | First load ~100 ms/image | In-memory `_IMAGE_CACHE` |
| Wikimedia fetch (ingest) | ~1–2 s/asset | One-time; not render path |

---

## Pipeline / Studio (RC1 evidence)

| Metric | Score | Source |
|--------|-------|--------|
| Overall production readiness | 91/100 | `PRODUCTION_READINESS.md` (RC1) |
| Orchestrator dry-run E2E | Verified | RC1 report |
| Workflow Executor pause/resume | Verified | RC1 report |

---

## Memory / CPU (qualitative)

| Workload | Observation |
|----------|-------------|
| Single Foundation render | Moderate CPU; FFmpeg bound |
| Full pytest | ~4 min wall; parallelizable |
| Streamlit Studio | Not profiled this sprint — local-first recommended |

---

## Regression thresholds (Agent 28 policy)

| Metric | Alert if |
|--------|----------|
| pytest pass count | Drops below 930 |
| Foundation render | > 120 s per Short (smoke) |
| idle_ratio failures | Any Foundation export |
| New cloud-only blocking call in performer path | Code review reject |

---

## Re-measurement cadence

- **Every release:** full pytest + Foundation smoke render  
- **Monthly:** Studio startup + asset load profile (local workstation)  
- **After major integration:** update this file + `dashboard.json`
