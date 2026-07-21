# Generational V1.0 RC1 — Technical Debt Register

**Date:** 2026-07-14  
**Rule:** Material reliability / quality / maintainability only. No speculative features.

---

## Active debt

| ID | Title | Priority | Status |
|----|-------|----------|--------|
| D1 | Deliverable truth vs MP4 materialization | Critical | Partially mitigated (success flag); encoder rate open |
| D2 | Ops resume is full re-run | Critical | Honest note added; skip logic open |
| D3 | Circular imports engines↔services | High | **Mitigated** — heuristics → `core`; lazy engine imports |
| D4 | Provider / path config drift | High | **Mitigated** — Anthropic pin + Videos resolver |
| D5 | Parallel channel / validation / orchestrator stacks | High | Accepted under freeze; document supported path |
| D6 | Animation unavailable → inflated motion scores | High | Open |
| D7 | Credentials in channel JSON | Medium | **Mitigated** — strip on save |
| D8 | Doc sprawl + missing subsystem READMEs | Medium | Open |
| D9 | Unlocked production queue JSON | Medium | Open |
| D10 | Absolute paths in channel library | Low/Medium | Open |
| D11 | Thumbnail/packaging quality | Medium | Open (Validation Program) |

---

## Interest rate (cost of delay)

| Debt | 30-day cost if ignored |
|------|------------------------|
| D1 | Validation + Channel programs mint false greens |
| D2 | Continuous mode burns API budget on restarts |
| D5 | Hotfixes land on wrong stack |
| D6 | Creative lab “learns” non-existent motion quality |

---

## Accepted under architecture freeze

- Multiple orchestrators / render surfaces coexist until deliverables are green  
- Scene Builder remains a stage composite, not a new package  
- Cloud execution stays removed  

Do **not** “pay” debt by redesigning the pipeline.
