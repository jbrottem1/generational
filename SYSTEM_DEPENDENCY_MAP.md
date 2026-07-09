# Generational — System Dependency Map (v9.7)

Who may depend on whom, the full pipeline data flow, and the live engine
dependency graph. The machine-readable version of this document is
`engines.registry.dependency_graph()` and `engines.registry.capability_index()`;
`tests/test_architecture.py` keeps code and map consistent.

---

## 1. Layer diagram (allowed dependency directions)

Dependencies point downward only. A layer never imports anything above it.

```mermaid
graph TD
    UI["ui/ — Streamlit views (display only)"]
    ORCH["services/orchestrator/ — the kernel:<br/>stages, packager, hooks, ContentPackage"]
    SVC["services/* — domain services<br/>(trends, scripts, visual, audio, seo, publishing,<br/>analytics, learning, market_intelligence, creative_studio,<br/>asset_generation, post_production...)"]
    ENG["engines/ — registered plugins<br/>(one key each; never import each other)"]
    LIB["Shared foundation:<br/>engines/base·contracts·heuristics·analysis, core/*"]
    PROV["providers/ — vendor adapters<br/>(research, trends, creative, asset_generation,<br/>post_production, publishing...)"]

    UI --> ORCH
    ORCH --> ENG
    ENG --> SVC
    ENG --> LIB
    SVC --> LIB
    SVC --> PROV
    ORCH --> LIB
```

- The **orchestrator** discovers engines through the registry only.
- **Engines** never import engines (Architecture Directive #1). Sanctioned
  exception: `image`/`video` adapters fronting Agent 6's `engines/render/`.
- **Providers** are imported through interfaces only.

## 2. Pipeline data flow (stage → stage via ContentPackage/context)

```mermaid
graph LR
    CMD([User Command]) --> T[trend]
    T --> R[research+ideation]
    R --> P[psychology]
    P --> S[script]
    S --> A[attention]
    A --> V[visual]
    V --> AU[audio]
    AU --> REF[refinement]
    REF --> Q[quality gate]
    Q --> PROD[media production]
    PROD --> PKG[packaging]
    PKG --> C[creative]
    C --> CU[character_universe<br/>stub]
    CU --> AG[asset_generation]
    AG --> ANI[animation<br/>stub]
    ANI --> REN[render]
    REN --> PP[post_production]
    PP --> SEO[seo]
    SEO --> OPT[optimization<br/>stub]
    OPT --> PUB[publish]
    PUB --> AN[analytics]
    AN --> L[learning]
    L --> BM[brand mgmt<br/>stub]
    L -.feedback.-> T
```

Every arrow is the orchestrator handing context / ContentPackage to the
next stage — never a direct call. See `PIPELINE_SPEC.md` for the full
contract.

## 3. Live engine dependency graph (declared contracts)

| Engine | Declares dependencies on |
|---|---|
| `trend_forecasting` | `trend_discovery`, `opportunity_ranking` |
| `market_intelligence` | `trend_discovery`, `opportunity_ranking`, `trend_forecasting` |
| `creative_studio` | `quality` |
| `asset_generation` | (via package inputs — creative / quality) |
| `post_production` | (via package inputs — render) |
| `optimization_lab` (stub) | `quality` |
| `animation` (stub) | `quality` |
| `character_universe` (stub) | — (persistent registry) |
| `render` / `image` / `video` | `visual_intelligence`, `voice_audio`, `quality` |
| `seo_optimization` | `seo`, `quality` |
| `scheduler` | `publishing_queue` |
| `publishing` | `render`, `seo_optimization` (via packages) |
| `analytics` | `publishing` |
| `learning` | `analytics` |
| `brand_management` (stub) | `learning` |

## 4. Module boundary rules (summary)

| Boundary | Rule | Enforced by |
|---|---|---|
| engine ↔ engine | never import; coordinate via orchestrator + package | static AST test |
| engine ↔ registry | register/replace only, never fetch-and-run | static test |
| orchestrator ↔ engines | registry discovery only, no engine imports | static test |
| package fields | additive-only, own-slot writes | `CONTENT_PACKAGE_FIELDS` + tests |
| stages/workflows ↔ registry | every referenced key must be registered | consistency test |
| declared dependencies | must reference registered engines | consistency test |
| vendors | behind `providers/` interfaces only | review (Directive #2 candidate) |
