# Release Readiness Checklist

**Owner:** Agent 28 · **Applies to:** every production release / RC tag  
**Fail closed:** any P0 item blocks ship

---

## 1. Tests

- [ ] `python3 -m pytest tests/` — **≥930 passed**, no **new** failures vs baseline (933/946 as of 2026-07-12)
- [ ] `tests/test_architecture.py` — engine import rules green
- [ ] `tests/test_foundation_gate.py` — Foundation floors enforced
- [ ] `tests/test_knowledge_atlas.py` — Atlas search/planner/QC green
- [ ] `python3 tests/test_knowledge_atlas.py` — standalone smoke (no pytest collection chain)

## 2. Dependencies

- [ ] `pip install -r requirements.txt` documented in release notes
- [ ] FFmpeg available on PATH (`find_ffmpeg()` succeeds)
- [ ] No new undeclared engine dependencies (`SYSTEM_DEPENDENCY_MAP.md` consistent)
- [ ] Provider runtime health check passes (or documented dry-run mode)

## 3. Foundation production path

- [ ] `foundation_gate.evaluate_foundation_export` — idle_ratio, lipsync, no wave
- [ ] `evaluate_reality_export` — licenses OK for all lesson assets
- [ ] `plan_visual_evidence()` runs before render on flagship series
- [ ] `record_lesson_visuals()` runs after export
- [ ] Desktop export path verified (playable MP4, audio + video tracks)

## 4. Documentation

- [ ] `AGENT_REGISTRY.md` updated for new agents
- [ ] `data/knowledge_standards/` synchronized (Agent 27)
- [ ] GCIS `lessons_learned.md` entry for release batch
- [ ] Experiment registry updated if applicable
- [ ] `RELEASE_NOTES.md` / RC doc updated

## 5. Character & visual consistency

- [ ] `CHAR-PROFESSOR-001` — attire `none`, no silent redesign (Agent 26)
- [ ] Curiosity Framework openings enforced (no Welcome-back)
- [ ] Knowledge Atlas assets QC-pass
- [ ] Attribution files current (`data/reality/ATTRIBUTION.md`)

## 6. Performance

- [ ] Foundation Short render < 90s per episode (local smoke)
- [ ] Studio UI loads without blocking on cloud sync
- [ ] No regression > 20% vs `PERFORMANCE_BASELINE.md`

## 7. Publishing (if live release)

- [ ] Target platform OAuth configured
- [ ] Dry-run publish SUCCESS before live
- [ ] Export manifest + captions generated

## 8. Executive

- [ ] `EXECUTIVE_RELEASE_DASHBOARD.md` reviewed by Agent 0
- [ ] Critical blockers resolved or explicitly accepted
- [ ] Rollback plan documented

---

## Quick release command sequence

```bash
pip install -r requirements.txt
python3 -m pytest tests/ -q
python3 scripts/sync_atlas_from_reality.py
python3 -c "from services.integration_release import run_integration_audit; print(run_integration_audit())"
# Optional flagship render (requires OPENAI_API_KEY):
python3 scripts/biology_batesian_mimicry_series.py --only batesian_101
```
