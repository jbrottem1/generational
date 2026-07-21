# Generational Operating System (GenOS)

**Status:** Production  
**Package:** `services/generational_os/`  
**CLI:** `scripts/genos.py`

GenOS is Agent 0’s executive layer — it orchestrates every existing Generational department as a company, without new production engines or pipeline redesign.

---

## What GenOS decides

- What to create (Trend & Opportunity Intelligence)
- When / which job runs next (scheduler)
- Which account/platform (brief + Publishing Intelligence when enabled)
- Priority, retries, escalation
- Which lessons improve future scores

Existing modules remain the departments. GenOS only coordinates.

---

## Operating loop

```
Trend Intelligence → Select opportunity → Production Brief
→ Research → Psychology → Script → World → Scenes
→ Visual Asset Director → Cinematic → Voice → Render
→ Creative QA → Package → Publish (if enabled)
→ Analytics → Audience Review → Opportunity Library → Lessons → Repeat
```

Execution of the studio path is delegated to **`run_studio_ops`** (Production Operations). Trend selection uses **`run_trend_opportunity`**.

---

## Job scheduler

Façade over `core.jobs` + `production_operations.enqueue_production`:

- Queue / prioritize / sequential `run_next`
- Retries with error classification
- Resume interrupted productions
- Duplicate topic/platform prevention
- Tracks: Job ID · Priority · Status · Creation/Completion · Current Stage · ETA

Artifact: `data/generational_os/PRODUCTION_QUEUE.json`

---

## Operations dashboard

`build_genos_dashboard()` / `build_operating_dashboard()["genos"]`:

Current / Queued / Completed / Failed jobs · Trending opportunities · Publishing queue · Platform & provider status · Analytics · Creative Excellence average · System health · Throughput · Resources

---

## Reports

| File | Location |
|------|----------|
| `DAILY_REPORT.md` | `data/generational_os/` |
| `WEEKLY_REPORT.md` | same |
| `MONTHLY_REPORT.md` | same |
| `SYSTEM_HEALTH.md` | same |
| `SYSTEM_STATE.json` | same |
| `PRODUCTION_QUEUE.json` | same |

---

## CLI

```bash
python scripts/genos.py dashboard
python scripts/genos.py reports
python scripts/genos.py cycle --category science --queue 5 --no-execute
python scripts/genos.py selftest                  # full day sim (runs one production)
python scripts/genos.py selftest --no-execute     # discover + queue + reports only
python scripts/genos.py run-next
```

Publishing stays **disabled** unless `--publish` is passed.

---

## Self-test (simulated operating day)

1. Discover opportunities  
2. Queue five productions  
3. Execute one complete production via Production Operations  
4. Creative QA + audience hooks (inside ops)  
5. Package outputs  
6. Generate operations reports  

```bash
./venv/bin/python -m pytest tests/test_genos.py -q
python scripts/genos.py selftest --no-execute   # CI-friendly
```
