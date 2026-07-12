# Experiment Registry

**Owner:** Agent 27  
**Machine-readable:** [`experiments.json`](experiments.json)  
**API:** `services.knowledge_standards.capture.register_experiment` / `load_experiment_registry`

Register every material experiment so we do not re-run unknowns. Fields: `id`, `objective`, `method`, `variables`, `outcome`, `metrics`, `decision` (`keep` | `discard` | `iterate`), `lessons`, `date`.

---

## Known experiments

| ID | Title | Decision | Date |
|----|-------|----------|------|
| EXP-FLUID-MOTION | Project Fluid Motion | keep | 2026-07-10 |
| EXP-SPRINT-6H30 | Sprint 6h30 continuous improvement | iterate | 2026-07-11 |
| EXP-FOUNDATION | PROJECT FOUNDATION white studio | keep | 2026-07-11 |
| EXP-ES001 | Executive Sprint 001 quality lock | keep | 2026-07-11 |
| EXP-STICK-3 | Stick figure science experiments ×3 | iterate | 2026-07-10 |
| EXP-COAT-REV | Agent 26 Gen attire / coat gate | keep | 2026-07-11 |

See JSON for full method / metrics / lessons. Evidence paths are company artifacts — outcomes are not invented.
