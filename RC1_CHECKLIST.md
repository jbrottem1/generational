# Generational V1.0 — RC1 Checklist

**Date:** 2026-07-14  
**Use:** Gate review before declaring V1.0 production.

Legend: `[x]` done · `[~]` partial · `[ ]` open

---

## A. Freeze & scope

- [x] No new engines added in RC1 pass
- [x] No new architectural layers
- [x] No speculative feature expansion
- [x] Safe fixes limited to low-risk / BC / critical defects

## B. Import / test integrity

- [x] `from services.ai_director import …` succeeds
- [x] `pytest tests/ --collect-only` collects without ERROR (**1226**)
- [x] Critical suites green (`ai_director`, `script_generation`, `production_operations`, `channel_os`, `execution_mode`, …) — **94 passed**
- [x] `pytest.ini` markers registered

## C. Configuration & paths

- [x] Anthropic runtime pin matches supported model
- [x] Videos root resolver unifies Channel OS + GenOS / execution_mode
- [ ] Provider preflight health check before GenOS drain

## D. Production operations

- [x] Stage soft-continue never hard-aborts pipeline
- [x] Final `success` requires MP4 **or** explicit smoke/`allow_missing_mp4`
- [x] Resume notes declare `full_rerun` when flag set
- [ ] Stage-skip resume from checkpoints
- [ ] Production-mode MP4 materialization ≥ 95% on 20-run sample
- [ ] Queue JSON file locking

## E. Quality honesty

- [ ] Cap motion scores when animation unavailable
- [ ] Validation Program success tied to deliverable
- [ ] Thumbnail/packaging improvement measured in validation library

## F. Multi-channel & folders

- [x] Channel profiles + three sample brands validated earlier
- [x] Credentials never persisted in channel JSON
- [x] Channel library packaging folders exist
- [ ] Channel metrics truthful under new success semantics (re-run sample)

## G. Security

- [x] `.env` not committed
- [x] Channel credential strip
- [ ] Relative paths in production indexes (PII/portability)

## H. Documentation pack (RC1)

- [x] `SYSTEM_AUDIT.md`
- [x] `PRODUCTION_READINESS.md`
- [x] `TECHNICAL_DEBT.md`
- [x] `SAFE_FIXES.md`
- [x] `OPEN_ISSUES.md`
- [x] `RC1_CHECKLIST.md` (this file)

---

## RC1 exit criteria → V1.0

All must be `[x]`:

1. [ ] OI-C1 closed — 20 consecutive production runs with verified MP4  
2. [ ] OI-C3 closed — resume skips completed stages  
3. [ ] OI-H5 closed — queue lock  
4. [ ] OI-H9 closed — validation success = deliverable  
5. [ ] Critical test collection + production_ops suite green on CI  
6. [ ] Publishing remains manual until post-V1.0 auth review  

**Current RC1 status:** **NOT CLEARED** — overall score **61/100**.
