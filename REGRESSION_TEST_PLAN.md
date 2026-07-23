# Regression Test Plan

**Owner:** Agent 28 · **Policy:** fail closed on new regressions

---

## Objectives

Ensure new improvements never break:

- Animation / Foundation performer path  
- Lip-sync QC floors  
- Rendering / FFmpeg export  
- Publishing dry-run  
- Asset loading (Atlas, Reality)  
- Real image retrieval and panel compositing  
- Desktop MP4 exports  
- Video quality gates  
- UI / architecture import rules  

---

## Tier 1 — Release blockers (must pass)

| Suite | Command | Baseline |
|-------|---------|----------|
| Full unit/integration | `python3 -m pytest tests/ -q` | **933 pass**, 13 known fail |
| Architecture | `python3 -m pytest tests/test_architecture.py -q` | All pass |
| Foundation gate | `python3 -m pytest tests/test_foundation_gate.py -q` | All pass |
| Knowledge Atlas | `python3 tests/test_knowledge_atlas.py` | OK |
| Knowledge standards | `python3 -m pytest tests/test_knowledge_standards.py -q` | All pass |

---

## Tier 2 — Foundation production smoke

| Test | Command | Expected |
|------|---------|----------|
| Reality QC | `python3 -c "from services.reality.qc import evaluate_reality_export, collect_demo_image_ids; print(evaluate_reality_export(image_ids=collect_demo_image_ids('foundation_batesian_101')).passed)"` | `True` |
| Atlas planner | `python3 -c "from services.knowledge_atlas import plan_visual_evidence; print(bool(plan_visual_evidence(main_concept='Batesian mimicry', demo_id='foundation_batesian_101')['panels']))"` | `True` |
| Smoke render (optional) | `python3 scripts/biology_batesian_mimicry_series.py --only batesian_101 --smoke` | ok=True, MP4 playable |

---

## Tier 3 — Known failures (fix before RC3)

Track until green:

1. `tests/test_render_engine.py` (4 failures)  
2. `tests/test_research_engine.py` (4 failures — NameError)  
3. `tests/test_engines.py` (2 failures)  
4. `tests/test_workflows.py::test_unready_engines_are_skipped`  
5. `tests/test_project_open_state.py`  
6. `tests/test_project_workspace.py`  

**Rule:** No **new** failures beyond this list. Any new failure blocks merge.

---

## End-to-end workflow regression matrix

| Stage | Automated | Manual |
|-------|-----------|--------|
| Idea → research | Partial (research tests failing) | — |
| Script | `test_script_generation.py` | — |
| Visual planning | `test_visual_intelligence.py` | — |
| Atlas evidence | `test_knowledge_atlas.py` | — |
| Animation | `test_foundation_studio.py` | Visual review |
| Voice | provider tests (mock) | OPENAI key smoke |
| FFmpeg export | smoke render script | ffprobe |
| QC gates | foundation_gate + reality_qc | — |
| Desktop export | verify_mp4 in producer | Open file |

---

## CI recommendation (local-first)

```bash
# Pre-commit / pre-release (local workstation)
pip install -r requirements.txt
python3 -m pytest tests/test_architecture.py tests/test_foundation_gate.py -q
python3 tests/test_knowledge_atlas.py
python3 -m pytest tests/ -q --tb=no | tail -5
python3 -c "from services.integration_release import run_integration_audit; run_integration_audit()"
```

Local Mac: run Tier 1 + local render/export verification. Cursor Cloud is not used for production execution.

---

## Sign-off

| Role | Responsibility |
|------|----------------|
| Agent 28 | Regression budget enforcement |
| Agent 1 | Architecture test failures |
| Agent 0 | Ship decision when Tier 1 + Foundation smoke pass |
