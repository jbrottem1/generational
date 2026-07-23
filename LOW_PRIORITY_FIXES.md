# Generational V1 — Low Priority Fixes (Medium + Low)

**Audit date:** 2026-07-14  
**Rule:** Worth doing after Critical/High deliverable fixes. Still reliability/maintainability only — no speculative features.

---

## Medium

### M1 — Document the single supported production path

| | |
|--|--|
| **Problem** | Multiple orchestrators confuse operators |
| **Fix** | One page (update `PIPELINE.md` or `PRODUCTION_OPERATIONS.md`) declaring supported path vs legacy; do not delete stacks under freeze |
| **Effort** | 0.5 day |
| **Impact** | Fewer wrong-entry bugs |
| **Risk if ignored** | Slow support / agent drift |

### M2 — Add thin root docs for Research / Psychology / Script / Scene

| | |
|--|--|
| **Problem** | Subsystems exist but lack operator-facing docs |
| **Fix** | Short READMEs pointing to packages + CLI + known soft-fail modes |
| **Effort** | 1 day |
| **Impact** | Faster onboarding; better audits |
| **Risk if ignored** | Knowledge concentrates in chat history |

### M3 — Scene-builder regression tests at stage level

| | |
|--|--|
| **Problem** | No dedicated tests for scene stage composite |
| **Fix** | Test `OPERATIONS_STAGES` scene step with fixtures; assert context keys, not new engine |
| **Effort** | 1 day |
| **Impact** | Catch planning regressions |
| **Risk if ignored** | Silent scene quality decay |

### M4 — Dual channel store consolidation (logical, not rewrite)

| | |
|--|--|
| **Problem** | `data/channels/` and `data/channel_os/` can diverge |
| **Fix** | Channel OS remains source of truth; legacy ChannelManager always synced (already partial); add `channel_os doctor` CLI to diff stores |
| **Effort** | 0.5–1 day |
| **Impact** | Brand metrics consistency |
| **Risk if ignored** | Wrong schedule/credentials surface |

### M5 — Cap / normalize conflicting score scales in reports

| | |
|--|--|
| **Problem** | 98 ops targets vs 70 publish vs CE 0–100 mixed messaging |
| **Fix** | Report layer labels scales explicitly (`gate_98`, `publish_70`); no formula redesign required |
| **Effort** | 0.5 day |
| **Impact** | Executive clarity |
| **Risk if ignored** | Bad go/no-go decisions |

### M6 — Voice generation caching for resume/retries

| | |
|--|--|
| **Problem** | Voice stage ~40s dominates cycle time; retries re-call ElevenLabs |
| **Fix** | Prefer existing hash-based narration cache (if present) on resume; skip TTS when audio artifact exists |
| **Effort** | 1 day |
| **Impact** | Faster recovery; lower voice cost |
| **Risk if ignored** | Expensive continuous runs |

### M7 — Reduce root markdown noise for operators

| | |
|--|--|
| **Problem** | ~138 root `.md` files bury current truth |
| **Fix** | Move historical AGENT_/SPRINT_/REPORT files under `docs/archive/` (no content rewrite); keep current system docs at root |
| **Effort** | 0.5–1 day |
| **Impact** | Maintainability |
| **Risk if ignored** | Stale instructions win |

### M8 — Absolute paths in channel production index

| | |
|--|--|
| **Problem** | SQLite/JSON stores machine-absolute `project_root` |
| **Fix** | Store path relative to Videos root + resolve at read time |
| **Effort** | 0.5 day |
| **Impact** | Portability / privacy |
| **Risk if ignored** | Broken links after machine move |

### M9 — Provider health probe on GenOS daily report

| | |
|--|--|
| **Problem** | Model/quota failures discovered mid-production |
| **Fix** | Soft probe (1 cheap call or model-list) into `SYSTEM_HEALTH.md` before queue drain |
| **Effort** | 0.5–1 day |
| **Impact** | Avoid doomed batches |
| **Risk if ignored** | Wasted continuous runs |

### M10 — Validation Program success definition tied to export

| | |
|--|--|
| **Problem** | Library can show 100% success without MP4 |
| **Fix** | Scorecard `success` requires `video_exists` or packaged export bytes > 0 when mode=production |
| **Effort** | 0.5 day |
| **Impact** | Validation becomes a real gate to V1.0 |
| **Risk if ignored** | 100-video program optimizes wrong outcomes |

---

## Low

### L1 — Register pytest `integration` mark

| | |
|--|--|
| **Fix** | Add to `pytest.ini` / `pyproject.toml` |
| **Effort** | 15 minutes |
| **Impact** | Cleaner CI logs |

### L2 — Narrator alias test matrix for Channel OS

| | |
|--|--|
| **Fix** | Parametrize profiles → Voice Studio resolve; already mostly covered |
| **Effort** | 0.5 day |
| **Impact** | Prevent brand voice silent fallback to professor |

### L3 — Queue UI badge for `resume_supported=true` only after C3

| | |
|--|--|
| **Fix** | Until C3 lands, dashboard should label resume as “full rerun” |
| **Effort** | 0.25 day |
| **Impact** | Operator honesty |

### L4 — Trim unused imports / dead Cloud strings as found

| | |
|--|--|
| **Fix** | Opportunistic cleanup during H2 path work only |
| **Effort** | Ongoing |
| **Impact** | Minor readability |

### L5 — Estimated revenue placeholder documentation

| | |
|--|--|
| **Fix** | Mark Channel dashboard revenue as non-operational until analytics providers live |
| **Effort** | 15 minutes |
| **Impact** | No executive misread |

---

## Explicitly not recommended (freeze)

- New animation engine to replace “animation unavailable”
- New renderer rewrite
- Merging all orchestrators into one mega-engine
- Cloud reintroduction
- Automatic architecture redesign from Validation recommendations

Those may be future product decisions; they are **out of scope** for RC1 stability.
