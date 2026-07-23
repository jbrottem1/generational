# Executive Orchestrator

**Status:** Production  
**Engine key:** `executive_orchestrator`  
**Service:** `services/executive_orchestrator/`  
**Workflow:** `executive`

Single entry point for the Generational AI Media Operating System — one instruction, full studio coordination.

```python
from services.executive_orchestrator import create_video

result = create_video(
    "Create a 60 second YouTube Short explaining why cameras can see infrared."
)
```

---

## Workflow

1. Understand request (topic · platforms · runtime · format)  
2. Discovery (Google Trends · News · YouTube · Search Intelligence)  
3. Rank opportunities → Script  
4. Evidence · Visuals · Cinematography/Animation · Voice · Assembly  
5. Production QA  
6. Auto-revision to owning engines until pass (or block)  
7. Export MP4 · Thumbnail · Captions · Description · SEO metadata  
8. Save artifacts · Queue publishing  

---

## Live dashboard stages

Discovery · Research · Script · Evidence · Visuals · Animation · Voice · Assembly · QA · Export · Publishing  

Each stage: `pending` | `running` | `completed` | `failed` | `skipped` + ETA remaining.

Studio → **Dashboard** shows the live board. Create tab uses **Executive Orchestrator** by default.

---

## Parallel runs

```python
orch = get_executive_orchestrator(max_parallel=2)
orch.submit_video("Create a TikTok about tides")
orch.submit_video("Create a Short about coral")
```

Resource limit via `ParallelProductionPool` (default 2 workers). Individual engine failures degrade non-critical stages instead of crashing the studio.

---

## Logging

Every run is stored under `data/generational_os/executive_runs/` with:

topic · runtime · engines used · generation time · QA score · export size · output paths · publish status  

---

## CLI

```bash
./venv/bin/python scripts/verify_executive_orchestrator.py
./venv/bin/python -c "from services.executive_orchestrator import create_video; print(create_video('Create a Short about gravity', plan_only=True)['id'])"
./venv/bin/python -m pytest tests/test_executive_orchestrator.py -q
```

`plan_only=True` rehearses the full stage board without invoking every heavy engine (CI / smoke).
