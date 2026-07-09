# Generational — The AI Content Operating System (v8.1)

How the pieces form one operating system rather than a collection of
engines. Companion to `MASTER_ARCHITECTURE.md` (what exists),
`PIPELINE_SPEC.md` (execution order), `DATA_CONTRACTS.md` (shared shapes),
`ORCHESTRATOR.md` (the kernel API), and `AGENT_WORKFLOW.md` (who edits what).

## The OS metaphor

| OS concept | Generational implementation |
|---|---|
| Kernel | `services/orchestrator/` — schedules stages, isolates failures, reports status |
| Processes | Engines (`engines/`) — registered plugins, never call each other |
| Syscall interface | `ContractEngine` (`engines/contracts.py`) — declared inputs, outputs, dependencies, capabilities |
| Shared memory | `context` dict during a run; canonical `ContentPackage` as the durable artifact |
| Device drivers | Providers (`providers/`) — swappable vendor integrations behind interfaces |
| Daemons / services | `OrchestratorHook` autonomy hooks — scheduler, publisher, analytics, learning |
| Filesystem | Projects + Knowledge Base (`services/knowledge.py`, `data/`) |
| Users | Brands/channels (`services/channels.py`, expanding into `services/brands/` under Agent 10) |

## Boot sequence of a content run

1. A command enters `Orchestrator.run_full_pipeline()` (from the UI today;
   from the autonomous scheduler later).
2. The kernel derives the stage plan from `WORKFLOWS["intelligence"]` plus
   registered future stages, and executes each stage with timing, logging,
   and graceful failure (`StageReport` per stage).
3. The packager folds the final context into `ContentPackage` objects — the
   only artifact downstream stages (render, seo, publish) consume.
4. Autonomy hooks are notified with the `PipelineResult`.
5. Future: analytics and learning stages feed results back into trend
   weights, psychology profiles, and brand strategy — the self-improvement
   loop.

## Extension model (Agents 6-10)

Every future subsystem plugs in the same way:

1. Subclass `ContractEngine` in your landing zone (`engines/render/`,
   `engines/publishing/`, `engines/seo/`, `engines/analytics/`,
   `engines/brands/` — each has an ownership README).
2. Keep the engine key already reserved in `engines/future_stubs.py` or the
   planned stubs (`analytics`, `learning`, `brand_management`). Agent 6
   graduated `image` and `video` this way and added the `render` façade —
   the render stage is live with mock providers (see
   `engines/render/README.md`). Agent 8 graduated `seo_optimization` the
   same way — the seo stage is live (`engines/seo_optimization.py` +
   `services/seo/`, see `engines/seo/README.md`). Agent 7 graduated
   `publishing` and `scheduler` — the publish stage is live with mock
   platform adapters (`engines/publishing/` + `services/publishing/` +
   `providers/publishing/`, see `engines/publishing/README.md`).
3. Register in `engines/__init__.py` (append-only, Agent 1 review).
4. Fill your slot in the ContentPackage; never touch other slots.
5. Your stage is already wired in the orchestrator — when your engine
   reports ready, the stage lights up. No orchestration changes needed.

## Safety invariants

- Nothing publishes without passing the Quality Gate (`publish_ready`).
- A failing stage stops the run gracefully; a missing engine skips with
  diagnostics — the OS never crashes because a subsystem is absent.
- All contracts evolve additively; old packages always deserialize.
