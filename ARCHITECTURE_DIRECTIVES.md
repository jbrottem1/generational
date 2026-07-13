# Generational — Architecture Directives

Mandatory engineering rules for every agent (human or AI) working on this
codebase. Directives are numbered, permanent, and enforced by automated
tests in `tests/test_architecture.py`. Only Agent 1 (Chief Systems
Architect) may add or amend directives.

---

## Architecture Directive #1 — Orchestrator-Only Communication

**NO ENGINE IS ALLOWED TO DIRECTLY CALL ANOTHER ENGINE.**

Prohibited (examples):

- Trend Discovery → Script Engine
- Psychology → Visual Intelligence
- Visual → Voice
- Voice → Render
- Render → Publishing
- Publishing → Analytics
- Analytics → Learning

All coordination flows exactly one way:

```
Pipeline Orchestrator  (services/orchestrator/)
        ↓
ContentPackage / shared context
        ↓
Next Engine
```

Every engine knows only: **"my input"** and **"my output"** — declared as
`input_contract` / `output_contract` on `ContractEngine`. Nothing else.

### 1.1 What the Orchestrator owns (and nothing else does)

Engine discovery (via the Engine Registry), execution order, dependency
resolution, passing ContentPackage objects, retries, diagnostics, logging,
execution timing, and — in the future — scheduling, distributed execution,
and cloud execution. Execution chains are never hardcoded: the plan derives
from `WORKFLOWS` plus `register_stage()` plugins at call time.

### 1.2 What an engine module may import

| Allowed | Why |
|---|---|
| `engines.base`, `engines.contracts` | The engine interface itself |
| `engines.heuristics`, `engines.analysis` | Shared pure-function libraries (word banks, scorers, critique) — data/analysis, not engines |
| `engines.registry` | Registration only — never for fetching and calling another engine |
| Its **own** subsystem package internals | e.g. `engines/render/engine.py` importing `engines/render/timeline.py`; the `image`/`video` stage adapters importing the render subsystem they front |
| `core.*`, `services.*`, `providers.*` | Foundation, services, and provider interfaces |

Everything else — importing another engine's module, calling
`registry.get_engine(...).run(...)` from inside an engine, reading another
engine's internals — is a directive violation and will fail the
architecture tests.

### 1.3 Shared logic protocol

If two engines need the same function, that function is not engine logic —
move it to `engines/analysis.py` (text analysis) or `engines/heuristics.py`
(word banks / math helpers), and have both engines import the library.
Precedent: the 18-dimension psychology scorer and the script critique both
live in `engines/analysis.py`; the Psychology and Critic engines re-export
them for backward compatibility, and the Attention Graph, Revision, and
citation service consume them without touching any engine.

### 1.4 ContentPackage rules (restated from DATA_CONTRACTS.md)

The ContentPackage (alias `ProductionPackage`) is the ONLY object exchanged
between engines. Every engine may append data, update fields it owns, and
add diagnostics/metadata. No engine may remove, rename, or repurpose
another engine's data. All evolution is backwards compatible.

### 1.5 Replaceability rule

Every engine and provider must be replaceable in under one hour: swap an
LLM/image/render/publishing/voice/analytics provider by registering a new
implementation behind the same interface — zero architecture changes.
Registering an engine under an existing key replaces it atomically; vendor
SDKs live behind `providers/` interfaces only.

### 1.6 Enforcement

- `tests/test_architecture.py` statically scans every engine module's
  imports and fails on prohibited engine-to-engine dependencies, and
  verifies at runtime that the orchestrator controls execution, packages
  flow, missing engines degrade gracefully, and diagnostics work.
- Exceptions require an explicit entry in the test's documented allowlist
  **and** Agent 1 review — silent exceptions are not possible.

---

*Directive #2 is not yet issued. Candidates under consideration: canonical
persistence & project store contract, provider-interface completeness
(every external I/O behind a provider), and per-brand execution isolation.*
