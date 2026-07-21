# Generational RC1 — Safe Fixes Applied

**Date:** 2026-07-14  
**Policy:** Low risk · backwards compatible · clearly correct · no architecture redesign

---

## SF-01 — Break AI Director / scripts / engines circular import

| | |
|--|--|
| **Changed files** | `core/heuristics.py` (new); `engines/heuristics.py` (shim); `engines/ai_director.py`; `engines/optimization_lab.py`; `engines/script_generation.py`; `services/scripts/__init__.py`; `services/scripts/hooks.py`; `services/scripts/generator.py`; all `services/**` former `engines.heuristics` imports → `core.heuristics`; `services/ai_director/blueprint.py` |
| **Reason** | `from services.ai_director import …` and `tests/test_ai_director.py` collection failed with circular import |
| **Expected improvement** | Full pytest collection succeeds; AI Director importable |
| **Regression risk** | Low — heuristics moved verbatim to `core`; `engines.heuristics` re-exports |

**Status:** Done

---

## SF-02 — Register pytest markers

| | |
|--|--|
| **Changed files** | `pytest.ini` |
| **Reason** | `PytestUnknownMarkWarning` for `@pytest.mark.integration` |
| **Expected improvement** | Cleaner CI logs; marks documented |
| **Regression risk** | None |

**Status:** Done

---

## SF-03 — Align Anthropic provider model pin

| | |
|--|--|
| **Changed files** | `data/provider_runtime/config.json` |
| **Reason** | Stale `claude-3-5-sonnet-20241022` → live 404s; code uses Haiku |
| **Expected improvement** | SEO/metadata LLM path stops retrying a dead model |
| **Regression risk** | Low — matches `services/anthropic_client.DEFAULT_MODEL` |

**Status:** Done

---

## SF-04 — Unify Videos root path spelling

| | |
|--|--|
| **Changed files** | `services/media_production/execution_mode.py`; `services/generational_os/media_library.py`; `services/channel_os/library.py` |
| **Reason** | `AI Start-Up` vs `AI Start-UP` split libraries |
| **Expected improvement** | GenOS + Channel OS resolve the same existing Desktop folder |
| **Regression risk** | Low — prefers any existing spelling before create |

**Status:** Done

---

## SF-05 — Deliverable-truth final ops success

| | |
|--|--|
| **Changed files** | `services/production_operations/orchestrator.py`; `services/production_operations/services_steps.py` |
| **Reason** | Ops reported success with `video_exists=false` (0/93 historical) |
| **Expected improvement** | `success` / `succeeded` false unless MP4 exists (unless smoke/plan / `allow_missing_mp4`) |
| **Regression risk** | Medium-low — call sites that treated any finished run as success must read `status.success`; soft-continue of stages unchanged |

**Status:** Done

---

## SF-06 — Defensive candidate access in export step

| | |
|--|--|
| **Changed files** | `services/production_operations/services_steps.py` |
| **Reason** | `((candidates)[0] or {}).get(...)` crashes when first candidate is a string |
| **Expected improvement** | Export validation tolerates degraded candidate shapes |
| **Regression risk** | None |

**Status:** Done

---

## SF-07 — Never persist plaintext channel credentials

| | |
|--|--|
| **Changed files** | `services/channels.py`; `services/channel_os/store.py` |
| **Reason** | Schema allowed secrets in local JSON |
| **Expected improvement** | Credentials stripped on create/update/save |
| **Regression risk** | None — empty credentials were the only safe state |

**Status:** Done

---

## SF-08 — Honest resume note (full re-run)

| | |
|--|--|
| **Changed files** | `services/production_operations/orchestrator.py` |
| **Reason** | `resume=True` did not skip stages but looked like checkpoint resume |
| **Expected improvement** | Status notes state `resume_mode=full_rerun` until real resume lands |
| **Regression risk** | None |

**Status:** Done

---

## Not auto-fixed (see OPEN_ISSUES.md)

- Real stage-skip resume (OI-C3)
- ffmpeg MP4 materialization rate (OI-C1 residual — truth flag fixed; encoder path still weak)
- Animation always unavailable (OI-H4)
- JSON queue file locking (OI-H5)
- Thumbnail packaging quality (OI-H8)
