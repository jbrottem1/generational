# Executive Release Dashboard

**Owner:** Agent 28 · **For:** Agent 0  
**Updated:** 2026-07-12 · **Refresh:** `python3 -c "from services.integration_release import run_integration_audit; run_integration_audit()"`

---

## Overall readiness

| Metric | Value |
|--------|-------|
| **Overall readiness score** | **87 / 100** |
| **Band** | Production candidate (Foundation track) |
| **RC1 platform score** | 91 / 100 (orchestrator dry-run) |
| **Test pass rate** | 98.6% (933 / 946) |

---

## Department readiness

| Department | Score | Status |
|------------|-------|--------|
| Executive | 100% | ✅ |
| Animation (Foundation) | 100% | ✅ |
| Character Systems | 100% | ✅ |
| Visual Intelligence + Atlas | 100% | ✅ |
| Knowledge Standards | 100% | ✅ |
| Render / FFmpeg | 100% | ✅ Path verified |
| Engineering / Orchestrator | 75% | ⚠️ 13 test failures |
| Publishing | 50% | ⚠️ OAuth blocked |
| Studio UI | 75% | ⚠️ Atlas browser pending |

---

## Critical blockers

| # | Blocker | Owner | ETA |
|---|---------|-------|-----|
| 1 | 13 pytest failures (render, research, workspace) | Agent 1 | RC3 |
| 2 | Live OAuth / API keys | Operator | On config |
| 3 | Phoneme lip-sync stub | Agent 16 | Post-80 quality |
| 4 | Atlas UI browser | Agent 20 | Platform sprint |

---

## Production capacity

| Track | Capacity | Notes |
|-------|----------|-------|
| Foundation Shorts | **High** | Local render ~40s/ep smoke |
| Batesian + Reality + Atlas | **3/3 shipped** | Q≈77.6 |
| Full 23-stage pipeline | **Medium** | Dry-run only |
| Live publish | **Low** | Credentials required |

---

## Failed tests (baseline — do not increase)

```
tests/test_engines.py (2)
tests/test_render_engine.py (4)
tests/test_research_engine.py (4)
tests/test_workflows.py (1)
tests/test_project_open_state.py (1)
tests/test_project_workspace.py (1)
```

---

## Upcoming releases

| Release | Scope | Gate |
|---------|-------|------|
| **1.0.0-rc3** | Agent 28 + Reality + Atlas integration | Tier 1 tests + Foundation smoke |
| **1.0.0-ga** | Live OAuth + test debt cleared | Full pytest green |

---

## Technical debt summary

**8 prioritized items** — see [`TECHNICAL_DEBT_REPORT.md`](TECHNICAL_DEBT_REPORT.md)

Top paydown: test failures → Atlas series rollout → lip-sync → Atlas UI

---

## Performance trends

| Metric | Trend |
|--------|-------|
| Foundation Q score | Stable ~77–79 |
| Test pass count | 933 (baseline) |
| Atlas assets | 6 → growing |
| Integration agents | +Agent 28 |

---

## Agent 0 decision matrix

| Question | Answer |
|----------|--------|
| Ship Foundation Shorts locally? | **Yes** |
| Ship RC3 tag? | **Yes** after test debt review |
| Ship public GA? | **No** — OAuth + full green tests |
| Delegate next? | Agent 1 fix TD-01; Agent 3 port series to Atlas |

---

## Machine-readable snapshot

`data/integration_release/dashboard.json` — updated by `run_integration_audit()`
