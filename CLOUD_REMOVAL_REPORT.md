# CLOUD REMOVAL REPORT

**Mission:** Remove Cursor Cloud execution from the Generational project  
**Date:** 2026-07-12  
**Policy:** Local-First — local Python, FFmpeg, filesystem, render, test, and export only

---

## Confirmation

**The project is now Local-First for production execution.**

- There is no `ExecutionMode.CLOUD`
- Renders always authorize locally (`should_render_media()` → `True`)
- Exports always target `~/Desktop/AI Start-Up/Videos/{Category}/` via the media library classifier
- `gate_production()` / `prepare_production()` always return `proceed: true` / `ready_to_render`
- Cursor Cloud env signals (`CURSOR_CLOUD_AGENT`, `GENERATIONAL_CLOUD_MODE`, etc.) no longer divert production

Cloud may still be used **manually** for brainstorming/architecture when explicitly requested — never for rendering, exporting, or production execution.

---

## Files changed

### Core runtime

| File | Change |
|------|--------|
| `services/media_production/execution_mode.py` | Collapsed to local-only; removed CLOUD enum/detection/env gates |
| `services/media_production/local_first.py` | Always proceed to local render; no handoff branch |
| `services/media_production/local_render_job.py` | Status `ready_to_render`; `execution_mode: local` |
| `services/media_production/verified_export.py` | Removed cloud early-return; Desktop library reachability check |
| `services/generational_os/orchestrator.py` | Always local proceed |
| `services/generational_os/export.py` | Removed `awaiting_local_render` cloud return |
| `services/generational_os/render_package.py` | `ready_to_render`; local status message |
| `services/generational_os/layers.py` | Intelligence + Pre-Production `runs_on: local` |
| `services/generational_os/dashboard.py` | Local-first health; legacy awaiting bucket only for history |
| `services/generational_os/improvement.py` | Backlog wording updated for local queue |

### Scripts

| File | Change |
|------|--------|
| `scripts/foundation_v2_turtles.py` | Removed `--allow-cloud-smoke` / awaiting-local success exit |
| `scripts/run_local_render_job.py` | Removed “CLOUD mode” refusal message |
| `scripts/verify_local_export.py` | Library reachability instead of mode enum check |
| `scripts/benchmark_export_reliability_turtles.py` | Local Desktop check only |
| `scripts/biology_batesian_mimicry_series.py` | Ignored cloud smoke; no awaiting-local branch |
| `scripts/project_foundation_benchmarks.py` | Same |

### Docs / standards

| File | Change |
|------|--------|
| `CLOUD_EXECUTION.md` | **Deleted** |
| `EXECUTION_MODE.md` | Rewritten local-only |
| `LOCAL_EXECUTION.md` | Rewritten; no cloud handoff |
| `GENERATIONAL_OS_V2_5.md` | Compliance + layout updated; CLOUD_EXECUTION link removed |
| `MEDIA_LIBRARY.md` | Local-only wording |
| `PERFORMANCE_BASELINE.md` | Local Mac / local CI |
| `data/knowledge_standards/PRODUCTION_STANDARDS.md` | Locked local-first standards |
| `data/integration_release/registry.json` | GATE-EXECUTION → local-only |
| `AGENT_28.md` | GATE-EXECUTION wording |
| `REGRESSION_TEST_PLAN.md` | Local Mac guidance |

### Tests

| File | Change |
|------|--------|
| `tests/test_execution_mode.py` | Asserts always-local; cloud env vars cannot resurrect CLOUD mode |

---

## Cloud references removed

| Reference | Disposition |
|-----------|-------------|
| `ExecutionMode.CLOUD` | Removed |
| `CURSOR_CLOUD_AGENT` / `CURSOR_AGENT` detection | Removed |
| `GENERATIONAL_CLOUD_MODE` | Removed |
| `GENERATIONAL_EXECUTION_MODE=cloud` force | Ignored (always local) |
| `GENERATIONAL_CLOUD_SMOKE_TEST` | Removed |
| `GENERATIONAL_FORCE_LOCAL` | Removed (no longer needed) |
| `cloud_status_message()` handoff copy | Replaced by `local_status_message()` (compat alias remains) |
| `awaiting_local_render` production path | Retired (`ready_to_render`) |
| `--allow-cloud-smoke` CLI | Removed from turtles; ignored elsewhere |
| `CLOUD_EXECUTION.md` | Deleted |
| Dual “cloud plans → Mac renders” architecture | Replaced by single local pipeline |
| Automatic “Run in Cloud” assumptions | Removed |
| Cloud synchronization / job handoff requirement | Removed |

---

## Remaining cloud-related items (intentional)

These are **not** Cursor Cloud production execution:

| Item | Why kept |
|------|----------|
| `stale_cloud_path` hard-fail (`/home/ubuntu/`, `/workspace/`) | Safety: reject remote VM paths as Desktop SUCCESS |
| Third-party APIs (OpenAI TTS, YouTube publish, Wikimedia fetch) | Product features, not Cursor Cloud agents |
| Historical JSON with `awaiting_local_render` / old cloud paths | Artifacts only; dashboard counts them as legacy queue |
| `allow_cloud_smoke=` kwargs (ignored) | Call-site compatibility; no behavior |
| `cloud_status_message()` alias | Points at local message for old imports |
| Word “cloud” in science content (Oort cloud, dust clouds) | Unrelated |
| Mentions in `FINAL_STATUS_SPEC.md` / `EXPORT_RELIABILITY_REPORT.md` of stale cloud paths | Path safety documentation |
| Optional manual Cursor Cloud brainstorming | Allowed only when user explicitly requests; never render/export |

---

## Local-First guarantees

| Requirement | Status |
|-------------|--------|
| Remove cloud-only execution paths | Done |
| Remove cloud-specific prompts/instructions/config | Done (`CLOUD_EXECUTION.md` deleted; standards rewritten) |
| Every render on local Mac | Done (`should_render_media` always true) |
| Every export to `~/Desktop/AI Start-Up/Videos/` via classifier | Unchanged / enforced |
| No automatic “Run in Cloud” assumptions | Done |
| No cloud synchronization requirements | Done |
| Future development assumes local Python/FFmpeg/FS/render/test/export | Documented in `EXECUTION_MODE.md` |

---

## Suggested operator cleanup (optional)

Historical artifacts may still contain old handoff fields; regenerate when convenient:

- Root `LOCAL_RENDER_JOB.json` / `RENDER_PACKAGE.json`
- `data/productions/execution_context.json`
- `data/generational_os/dashboard.json`
- Per-project `RENDER_PACKAGE.json` files with `awaiting_local_render`

These do not restore cloud execution; they are stale status strings only.
