# Generational — Architecture Review (v9.6, 2026-07-09)

Comprehensive audit by Agent 1 covering Agents 1-11 (shipped on this
branch) and readiness for Agents 12-30. Verified against the live registry
(**37 engines**, **36 ready**, **49 capability tags**) and the full test
suite on `feature/market-intelligence` (excluding unmerged Agent 12
creative-studio files present only locally).

---

## 1. Current Architecture Score: 88 / 100

| Dimension | Score | Evidence |
|---|---|---|
| Loose coupling | 95 | Directive #1 statically enforced; zero engine-to-engine imports; orchestrator engine-agnostic (tested) |
| Clear ownership | 90 | Every engine key has one owner; landing zones + ownership rows; one gap found and fixed this review (see §2) |
| Provider abstraction | 85 | 10+ provider interfaces, per-file adapter swap; not yet machine-enforced (Directive #2 candidate) |
| Pipeline consistency | 90 | One plan source (`WORKFLOWS` + stage registry); stage/registry/dependency consistency now tested |
| Backward compatibility | 90 | Additive-only package fields; unknown fields survive via `extras`; re-export shims preserved every refactor |
| Graceful degradation | 95 | Every stage: empty input → no-items summary; failure → WARNING with diagnostics; missing engine → skip |
| Scalability to 100+ engines | 80 | Registration is O(1) per engine but `engines/__init__.py` is a single append-point contention file; execution is sequential in-process |
| Version compatibility | 75 | Engines declare `version` but nothing checks contract-version compatibility between producers and consumers |

## 2. Findings from this review

1. **Creative Studio integration gap (Agent 12, pending merge):** the engine
   is built on `feature/creative-studio` but not yet merged into
   `feature/market-intelligence`. Locally it can be wired (register +
   `creative` stage in `DISTRIBUTION_STAGES`) — that wiring is documented in
   `INTEGRATION_CHECKLIST.md` step 9 and blocked until Agent 12's branch
   merges. *Do not register `creative_studio` without its module on the
   branch — `engines/__init__.py` import will fail.*
2. **Machine-readable capability/dependency views** — added
   `registry.describe_all()`, `registry.capability_index()`,
   `registry.dependency_graph()` + 4 consistency tests (staged keys must be
   registered; declared dependencies must exist; index complete/uniform).
3. **Registry docs drifted** — `ENGINE_REGISTRY.md`, `PIPELINE_SPEC.md`,
   `DATA_CONTRACTS.md`, `AGENT_WORKFLOW.md` reconciled with the code.
4. **New governance artifacts** — `AGENT_REGISTRY.md`,
   `SYSTEM_DEPENDENCY_MAP.md`, `CAPABILITY_MATRIX.md`,
   `ENGINE_CAPABILITY_INDEX.md`, rewritten `INTEGRATION_CHECKLIST.md`.

## 3. Technical debt

| Item | Severity | Owner |
|---|---|---|
| `render` façade engine registered but unstaged (stage runs `image`+`video` adapters over the same code) — consolidate to one entry point | medium | Agent 6 + Agent 1 |
| Dual naming: `platforms`/`target_platforms`, `language`/`target_language`, `analytics_placeholder`/`analytics_package` (additive-rule artifacts) | low | documented, permanent |
| `services/ideation.py` UI adapter reshapes PipelineResult → legacy dict; UI should eventually consume PipelineResult directly | low | Agent 1 |
| Classic engines (pre-contract) don't declare input/output contracts — only ContractEngine subclasses do | medium | migrate opportunistically |
| Simulated data behind mocks (render, publishing, analytics metrics) — fine by design, but learning loops train on synthetic signals until real providers land | medium | Agents 6/7/10 |
| `.worktrees/` appearing untracked in the repo — should be gitignored | low | Agent 1 |

## 4. Architecture risks

1. **Single append-point contention:** every agent edits
   `engines/__init__.py` and `STAGE_GROUPS`. At 100+ engines this becomes a
   merge hotspot → move to auto-discovery (scan `engines/` for
   ContractEngine subclasses) in a future version.
2. **Sequential in-process execution:** one slow engine stalls the run; no
   per-stage timeout/retry policy yet. The orchestrator's interface already
   permits a distributed backend — implement behind it, not around it.
3. **No contract-version negotiation:** if Agent 8 changes what
   `seo_package` contains, Agent 7 finds out at runtime. Consider declared
   contract versions checked at registration.
4. **Learning-loop feedback authority:** `learning_recommendations` adjust
   upstream weights; there is no bounded-authority rule yet (how much a
   recommendation may move a weight without human sign-off).
5. **Provider abstraction is convention, not law** (see Directive #2).

## 5. Duplicate responsibilities audit

- `seo` (refinement metadata packaging) vs `seo_optimization` (global
  optimization) — **intentional separation**, documented; not duplication.
- `render_package` (media-production planning) vs `render` stage (Agent 6
  execution) — planning vs execution; acceptable, names are confusable —
  documented in the dependency map.
- `image`/`video`/`render` triple-entry into one render subsystem — flagged
  as debt (§3), not a correctness issue.
- No other overlaps found across 38 engines / 58 capability tags.

## 6. Missing contracts & interfaces

| Missing | Recommendation |
|---|---|
| Provider-interface directive (vendor imports outside `providers/` are possible today) | **Architecture Directive #2** — statically enforce like Directive #1 |
| Contract versioning between producer/consumer engines | add `contract_version` to ContractEngine; registry warns on mismatch |
| Bounded learning authority | Directive #3 candidate: weight-change caps + audit log |
| Persistence contract (project store, analytics store, memory store each roll their own) | one `StorageProvider` interface before Agent 20 |
| Scheduler/executor interface for autonomous runs | exists as job queue + hooks; formalize before Agent 20 |

## 7. Suggested refactors (priority order)

1. Engine auto-discovery to retire the `engines/__init__.py` append point.
2. Consolidate the render stage to a single engine entry (`render`) with
   `image`/`video` as internal capabilities.
3. Migrate high-traffic classic engines (psychology, script_generation,
   visual_intelligence, voice_audio, quality) to ContractEngine so the
   dependency graph covers the intelligence pipeline too.
4. UI consumes `PipelineResult` directly; retire the ideation reshaping.

## 8. Future Readiness Score: 90 / 100

Agents 13-20 each have: a reserved engine key, a defined integration seam
(package slot or hook), a checklist, and enforcement tests. The three
deductions: no auto-discovery yet (registration contention), no contract
versioning, and no compute/distribution layer for heavy media generation.

## 9. Recommendations for Agents 16-30

- **16 (Animation) / 17 (Post-Production):** extend `creative_package` and
  `render_package` additively; register as stages between `creative` and
  `publish`; all asset generation behind `providers/creative/`.
- **18 (AI Director):** consumes every package, writes direction notes only
  (own slot); must not mutate other engines' outputs — enforce via tests.
- **19 (BI & Monetization):** builds on `analytics_package`; add revenue
  fields additively; no new pipeline stage needed initially.
- **20 (Autonomous Executive):** integrate ONLY via `OrchestratorHook` +
  the job queue (`ORCHESTRATOR_JOB_TYPE`); ship Directive #3 (bounded
  authority + human-approval gates) BEFORE it can initiate runs.
- **21-30 (divisions):** follow `AGENT_REGISTRY.md` §4 — every division
  maps onto existing seams; if a division seems to need a new seam, that's
  an Agent 1 review, not a workaround.

---

*Next review due when Agent 13 or 14 lands, or before Agent 20 begins —
whichever comes first.*
