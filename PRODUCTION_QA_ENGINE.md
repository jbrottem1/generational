# Production Quality Assurance (PQA) Engine

**Status:** Production  
**Engine key:** `production_qa`  
**Service:** `services/production_qa/`

Final editor-in-chief of the Generational AI Media Operating System.  
**Nothing reaches export or Publishing without PQA `APPROVE`.**

---

## Decisions

| Decision | Meaning |
|----------|---------|
| `APPROVE` | Overall ≥ 90 and every category ≥ 90 |
| `REQUEST_REVISION` | One or more categories below 90 — route fixes to owning engines |
| `BLOCK_EXPORT` | Critical failure (accuracy/evidence/visuals/education critically low, or hard fails) |

---

## Pipeline position

```
… → threat_detection → quality → … → video → production_qa → publishing
```

Also:
- `intelligence` — ends with `production_qa` (after `quality`)
- `media_production` — `render_package` → `production_qa` → `publishing_queue`

A `PrePublishGate` (`production_qa`) blocks live publish jobs that are not approved when `enforce_pqa` is set or a failing report is attached.

---

## Categories (0–100)

1. Research Accuracy  
2. Evidence (real image %, AI %, missing evidence)  
3. Visuals  
4. Typography  
5. Annotations (narration-tied only)  
6. Cinematography  
7. Audio  
8. Narration  
9. Synchronization  
10. Educational Value  
11. Psychology (predicted CTR, retention, shareability, …)  
12. SEO  
13. Platform Compliance → ready matrix (YouTube, Shorts, TikTok, Reels, Facebook, Pinterest, LinkedIn, X)

---

## Auto-revision

Any category &lt; 90 emits structured `revision_requests` mapped to engines, e.g.:

- Evidence → `evidence_intelligence`, `visual_intelligence`  
- Cinematography → `cinematography`, `animation`  
- Narration → `script_generation`, `narration`  
- SEO → `seo`

`publishable` is forced `False` unless decision is `APPROVE`.

---

## Learning

Reports are stored under `data/generational_os/pqa_reports/`.  
After publish, call `record_performance_feedback(idea_id, actual_metrics)` to compare predicted vs actual CTR / watch time / shares and calibrate future scoring.

---

## Usage

```python
from services.production_qa import inspect_production

report = inspect_production(idea, context)
print(report.decision, report.overall_score)
print(report.to_dict()["report_markdown"])
```

```bash
./venv/bin/python scripts/verify_production_qa.py
./venv/bin/python -m pytest tests/test_production_qa.py -q
```
