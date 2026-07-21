# Generational V1 — High Priority Fixes (Critical + High)

**Audit date:** 2026-07-14  
**Scope:** Changes that materially unblock RC1 → V1.0 production  
**Out of scope:** New engines, new stages, architecture redesign

Each item: Problem · Evidence · Fix (within frozen architecture) · Priority · Effort · Impact · Risk if ignored

---

## Critical

### C1 — Make ops success equal “playable MP4 exists”

| | |
|--|--|
| **Problem** | Pipeline reports success / approve while `export.video_exists` is false |
| **Evidence** | 0 / 93 ops with `video_exists=true`; 78× `mp4_not_yet_materialized` |
| **Fix** | In `export_and_validate` + final ops status: hard-set `success=False` (and block publish recommendation) when no MP4; distinguish `mode=smoke|plan|production` explicitly in status |
| **Effort** | 0.5–1 day |
| **Impact** | Restores truthful dashboards, validation, channel metrics |
| **Risk if ignored** | Entire V1.0 ships on fake green lights |

### C2 — Fix `studio_render` TypeError (`str` has no `.get`)

| | |
|--|--|
| **Problem** | Render stage fails after retries with `'str' object has no attribute 'get'` |
| **Evidence** | 50 ops errors; pairs with “studio_render failed after retries — production continued” |
| **Fix** | Trace call site in studio_render/resilience bridge; coerce candidate items to dict before `.get`; add regression test with string candidate |
| **Effort** | 0.5–1.5 days |
| **Impact** | Unblocks majority of failed render attempts |
| **Risk if ignored** | Deliverable path stays dead for half+ of runs |

### C3 — Implement real ops stage resume

| | |
|--|--|
| **Problem** | `run_studio_ops(resume=True)` only adds a note, then re-runs all stages |
| **Evidence** | `orchestrator.py` lines 96–98; queue passes `resume_production_id` assuming skip semantics |
| **Fix** | Load prior `PRODUCTION_OPS_STATUS.json`; skip stages with `status=succeeded`; reuse artifact paths in context; align with queue `recover_failed_jobs` |
| **Effort** | 1–2 days |
| **Impact** | True recovery from interrupted jobs; lower API spend |
| **Risk if ignored** | Continuous operation burns money and cannot recover mid-pipeline |

### C4 — Resolve AI Director circular import

| | |
|--|--|
| **Problem** | Import cycle prevents loading AI Director and breaks pytest collection |
| **Evidence** | `engines.ai_director` ↔ `services.ai_director.package` ↔ `blueprint` ↔ `engines` |
| **Fix** | Move shared helpers or lazy-import `engines.heuristics.clamp` inside functions; break `engines/__init__.py` eager import of AiDirectorEngine if needed |
| **Effort** | 0.5–1 day |
| **Impact** | Restores director usability + full test collection |
| **Risk if ignored** | Core cinematic/director path is untested and unloadable in some entrypoints |

---

## High

### H1 — Align provider model configuration with live APIs

| | |
|--|--|
| **Problem** | Provider runtime pins dead Anthropic model; fallbacks hit empty model / quota errors |
| **Evidence** | `config.json` → `claude-3-5-sonnet-20241022` 404; OpenAI 429; “you must provide a model parameter” |
| **Fix** | Update pin to supported model; ensure every fallback path sets model; fail fast with clear provider health in GenOS SYSTEM_HEALTH |
| **Effort** | 0.5 day |
| **Impact** | SEO/metadata and LLM stages stop wasting retries |
| **Risk if ignored** | Packaging/SEO remains weak; cost without quality |

### H2 — Unify Videos root path casing

| | |
|--|--|
| **Problem** | `AI Start-Up` vs `AI Start-UP` splits the media library |
| **Evidence** | GenOS `media_library.py` / `execution_mode.py` vs Channel OS `library.py` and real Desktop path |
| **Fix** | Single resolver: prefer existing dir, else create `AI Start-UP/Videos`; migrate helpers to shared function; no new engine |
| **Effort** | 0.5–1 day |
| **Impact** | Exports and channel packages land in one tree |
| **Risk if ignored** | “Missing video” hunts across two directories forever |

### H3 — Export gate must not approve smoke packages as production

| | |
|--|--|
| **Problem** | Metadata-only export path is counted as production success |
| **Evidence** | Warning text explicitly cites smoke/plan modes; still overall approve |
| **Fix** | Thread `execution_mode` into export validation; production mode requires ffmpeg-materialized MP4 + size/duration checks (reuse GenOS export verifier patterns already proven on turtle_202) |
| **Effort** | 1–2 days |
| **Impact** | Closes the largest reliability gap without new renderer architecture |
| **Risk if ignored** | C1 alone is incomplete if smoke path stays default |

### H4 — Animation unavailable: fail-soft with explicit quality floor

| | |
|--|--|
| **Problem** | Animation unavailable on 100% of sampled ops; motion scores still often high |
| **Evidence** | 93 / 93 warning; cinematic scores can remain ~98 in reports |
| **Fix** | When animation skips, cap motion/cinematic dimensions and surface `quality_floor_applied` on report; do not invent new animation engine |
| **Effort** | 0.5 day |
| **Impact** | Honest creative scores; prevents false Optimization Lab passes |
| **Risk if ignored** | Creative excellence learns the wrong baseline |

### H5 — JSON production queue file locking

| | |
|--|--|
| **Problem** | Concurrent queue writers can clobber `PRODUCTION_QUEUE.json` |
| **Evidence** | No lock in `queue.py` RMW; GenOS + CLI + Streamlit can race |
| **Fix** | `portalocker`/`fcntl` exclusive lock around load/save; or atomic temp write + replace |
| **Effort** | 0.5 day |
| **Impact** | Safe continuous operation |
| **Risk if ignored** | Silent job loss under multi-entry use |

### H6 — Channel credentials never persist secrets in plaintext JSON

| | |
|--|--|
| **Problem** | Schema encourages storing credentials beside brand identity |
| **Evidence** | `services/channels.py` docstring + `credentials` field on profiles |
| **Fix** | Reject non-empty credentials in save path; point to env/keychain only; document in CHANNEL_OS.md |
| **Effort** | 0.5 day |
| **Impact** | Prevents accidental secret sprawl |
| **Risk if ignored** | High-severity leak once monetization/OAuth is wired |

### H7 — Full-suite CI must fail on collection errors

| | |
|--|--|
| **Problem** | AI Director cycle causes collection ERROR; suites can appear “green” if subsetted |
| **Evidence** | `pytest tests/ --collect-only` interrupted; subset of 20 still passes |
| **Fix** | After C4, add CI step `pytest --collect-only` must exit 0; register `integration` mark |
| **Effort** | 0.25–0.5 day (plus C4) |
| **Impact** | Trustworthy release gate |
| **Risk if ignored** | Regressions ship unnoticed |

### H8 — Thumbnail / packaging quality (department tune, not redesign)

| | |
|--|--|
| **Problem** | Validation library average thumbnail appeal ≈ 55 |
| **Evidence** | Validation executive dashboard P0 recommendation |
| **Fix** | Tighten existing Publishing Intelligence / SEO thumbnail rules + director thumbnail strategy inputs; measure via Validation Program batches |
| **Effort** | 1–2 days |
| **Impact** | Higher CTR readiness on otherwise strong hooks (hook avg 100 in sample) |
| **Risk if ignored** | Strong scripts underperform distribution |

---

## Suggested Critical/High sequence (≈ 1–2 weeks)

1. **C4** circular import (unblocks tests)  
2. **C2** studio_render TypeError  
3. **H3 + C1** production export truth  
4. **C3** real resume  
5. **H1 + H2** config + paths  
6. **H5 + H6 + H7** ops hygiene  
7. **H4 + H8** score honesty + packaging  

Do **not** start parallel engine consolidation until deliverables are green.
