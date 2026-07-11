# Generational — Executive Operating System

**Owner:** Agent 0 — Chief of Staff / Executive OS  
**Mission:** Build the world's best autonomous AI media operating system.  
**Company mode:** Operator-led company; Agent 0 is the primary interface to all departments.  
**Last updated:** 2026-07-10  
**Branch:** `release/1.0.0-rc2`

Companions: `AGENT_REGISTRY.md` · `GENERATIONAL_VISUAL_UNIVERSE.md` · `PRODUCTION_READINESS_REPORT.md` · `RELEASE_CANDIDATE_1.0.md`

**Permanent dual P0:** (A) Production + live distribution · (B) Generational Visual Universe

---

## Decision protocol (mandatory)

When an objective arrives, Agent 0 does **not** immediately delegate. Sequence:

1. Understand the business objective  
2. Estimate impact  
3. Estimate effort  
4. Identify dependencies  
5. Determine ROI  
6. Decide whether it should be done now  
7. Break into milestones  
8. Assign departments  
9. Assign specialist agents  
10. Track completion  

---

## Executive departments

Every specialist agent belongs to exactly one primary department.  
Executive Owner = accountable for department outcomes; specialists execute.

| Department | Executive Owner | Specialist agents | Charter |
|---|---|---|---|
| **Executive Office** | Agent 0 | Agent 22 (planned) | Strategy, prioritization, coordination, roadmap |
| **Engineering** | Agent 1 | 1, 9, 21 | Architecture, orchestrator, contracts, pipeline, workflow |
| **Platform** | Agent 20 | 19, 20, 21 | Studio UI, provider runtime, operator control plane |
| **Creative Department (Visual Universe)** | Agent 18 | 3, 4, 12, 14, **15**, **16**, 17, 18 | Visual identity, world building, characters, animation language, brand consistency |
| **Creative Studio** (engine ops) | Agent 12 | 12 | Styles, color, lighting, creative memory (reports to Creative Dept) |
| **Research** | Agent 11 | 2, 11 | Psychology, market intelligence, forecasting |
| **Media Production** | Agent 9 | 5, 6, 14, 17 | Voice, render, assets, post (15/16 primary home = Creative Dept) |
| **Publishing** | Agent 7 | 7, 8 | Distribution, scheduling, SEO/packaging for platforms |
| **Growth** | Agent 8 | 8 (+ future growth agents) | Distribution growth, SEO, channel expansion |
| **Marketing** | *Unstaffed* | Reserved 23+ | Brand narrative, positioning, go-to-market |
| **Analytics** | Agent 10 | 10, 13* | Performance measurement, learning loop, optlab* |
| **Infrastructure** | Agent 19 | 19, 21 | Providers, runtime, jobs, scale path |
| **Quality Assurance** | Agent 17 | 17 (+ Agent 1 architecture tests) | QC gates, integrity, production readiness evidence |
| **Security** | *Unstaffed* | Reserved | Secrets, OAuth hardening, threat model |
| **Finance** | *Unstaffed* | Reserved | Cost/token budgets, unit economics |
| **Legal** | *Unstaffed* | Reserved | IP, platform ToS, disclosure, rights |
| **Customer Success** | *Unstaffed* | Reserved | Operator support, runbooks, onboarding |
| **Operations** | Agent 0 | 9, 21 | Sprint cadence, release ops, dependency resolution |

\* Agent 13 (optlab) remains parked unless promoted. Agents 15/16 are **promoted** onto the Visual Universe track (`GENERATIONAL_VISUAL_UNIVERSE.md`).

### Agent → department map (primary)

| Agent | Name | Department |
|---|---|---|
| 0 | Chief of Staff / Executive OS | Executive Office |
| 1 | Master Architecture | Engineering |
| 2 | Psychology | Research |
| 3 | Script Generation | Creative Studio |
| 4 | Visual Intelligence | Creative Studio |
| 5 | Voice & Audio | Media Production |
| 6 | Render Engine | Media Production |
| 7 | Publishing & Distribution | Publishing |
| 8 | SEO / Content Optimization | Growth |
| 9 | Production Pipeline | Media Production |
| 10 | Analytics & Learning | Analytics |
| 11 | Market Intelligence | Research |
| 12 | Creative Studio Engine | Creative Studio |
| 13 | Optimization Laboratory | Analytics (stub) |
| 14 | Asset Generation | Creative Department / Media Production |
| 15 | Character / Universe / IP | Creative Department (**Visual Universe active**) |
| 16 | Animation & Cinematics | Creative Department (**Visual Universe active**) |
| 17 | Post-Production | Media Production / QA / VU-GATE |
| 18 | AI Director / Creative Director | Creative Department |
| 19 | Provider Runtime | Infrastructure / Platform |
| 20 | Studio UI | Platform |
| 21 | Workflow Executor | Engineering / Infrastructure |
| 22 | Autonomous Executive | Executive Office (planned) |

---

## Live company dashboards

### Company Health — **YELLOW / assembly_ready**

| Signal | Status |
|---|---|
| Can produce real Shorts (MP4 + voice + QC) | YES — 5 RC1 certified, `mock_render=false` |
| Can publish live to YouTube | NO — OAuth missing |
| Closed-loop dry-run OS | YES |
| Public GA | NO-GO |

### Engineering Health — **GREEN**

Architecture intact; Orchestrator-only engines; RC2 media seams wired without redesign.

### Production Readiness — **88 / 100**

Band: `assembly_ready`. Evidence: `PRODUCTION_READINESS_REPORT.md` + 5 real exports.

### Publishing Status — **DRY-RUN ONLY**

Connectors code-ready; live OAuth not configured. Integrity gate blocks live mock publish.

### Growth Metrics — **PRE-REVENUE / PRE-DISTRIBUTION**

No live channel metrics yet. Analytics learning loop armed on dry-run data only.

### Agent Workload — **DUAL TRACK ACTIVE**

- Track A (Distribution): Agents 7, 19, 17 — live publish  
- Track B (Visual Universe): Agents 18, 15, 16, 12, 14 — style bible, characters, environments  
- Agent 13 remains parked (optlab) unless promoted  

### Visual Universe Health — **PROGRAM LAUNCHED**

Charter: `GENERATIONAL_VISUAL_UNIVERSE.md` · Library: `data/universe/` · Dashboard: `data/universe/dashboard.json`

### Technical Debt — **MEDIUM**

| Item | Severity |
|---|---|
| Stale readiness score in `MASTER_PRODUCTION_PIPELINE.md` (72 vs 88) | Low |
| Stub engines / 6 worktrees | Medium (scope risk) |
| Async video provider poll thin | Medium |
| Dual long-form controllers | Medium (documented) |
| JSON stores for multi-tenant | Future |

### Current Sprint — **Dual P0**

1. First live YouTube publish (Track A)  
2. Visual Universe Milestone A — Style Bible + registry + 15/16 merge plans (Track B)

### Roadmap — see below

### Revenue Opportunities — **LATENT**

| Opportunity | Gate |
|---|---|
| YouTube Shorts channel (ad/affiliate later) | Live publish |
| Multi-platform syndication | OAuth × N |
| Operator SaaS / API | Multi-tenant + auth |
| Brand / IP franchises | Character universe merge |

### Critical Risks

| ID | Risk | Severity |
|---|---|---|
| R1 | No live distribution → product unproven in market | **Critical** |
| R2 | Visual Universe scope vs throughput — mitigate via dual-track parallelization | High |
| R2b | Blind-merging 15/16 worktrees without Agent 1 review | High |
| R3 | Credential / OAuth friction delays learning loop | High |
| R4 | Doc score drift causes bad prioritization | Medium |

---

## Company roadmap

### Today
- PROJECT GENERATIONAL VISUAL UNIVERSE chartered
- Creative Department established (Owner: Agent 18)
- Dual track: live publish + Style Bible / universe scaffold

### This Week
- Track A: YouTube OAuth + first live Short
- Track B: GVU-001 Style Bible lock · GVU-005/006 merge plans for Agents 15 & 16
- Character + environment briefs (CHR-01/02, ENV-01..03)

### This Month
- First Universe Pack: 3 environments + 2 characters approved
- VU-GATE v1 in QC
- Flagship Short produced inside the universe
- Repeatable production cadence with rising asset reuse

### Next Quarter
- Operating studio: reuse ≥ 30%, animation language v1 default
- Multi-platform publish
- Brand recognition internal blind tests
- Agent 13 promote/defer; Agent 22 design

### Long-term Vision
- Generational Universe as recognizable educational animation IP
- Fully autonomous media company on top of a durable visual brand
- Every video enriches permanent company assets

---

## Sprint board (active)

| ID | Task | Dept | Owner | Priority | Status | Deps | Notes |
|---|---|---|---|---|---|---|---|
| EX-001 | Configure YouTube OAuth | Publishing / Platform | Agent 7 + 19 + Operator | P0 | Ready | Operator credentials | Track A |
| EX-002 | Live publish smoke (1 RC Short) | Publishing + QA | Agent 7 + 17 | P0 | Blocked | EX-001 | Track A |
| EX-003 | Stub freeze (13 only; 15/16 → Visual Universe) | Executive Office | Agent 0 | P0 | **Updated** | — | 15/16 active on GVU |
| GVU-001 | Style Bible v0.1 lock | Creative Dept | Agent 18 + 12 | P0 | Ready | Charter | Track B |
| GVU-002 | CHR-01/02 character briefs + registry | Creative Dept | Agent 15 | P0 | Ready | GVU-001 | Track B |
| GVU-003 | ENV-01..03 environment packs | Creative Dept | Agent 15 + 14 | P0 | Ready | GVU-001 | Track B |
| GVU-005 | character_universe merge plan | Engineering + Creative | Agent 1 + 15 | P0 | Ready | Charter | No blind merge |
| GVU-006 | animation-engine merge plan | Engineering + Creative | Agent 1 + 16 | P0 | Ready | Charter | No blind merge |
| EX-004 | Optional ElevenLabs | Media Production | Agent 5 + 19 | P1 | Backlog | API key | Quality |
| EX-005 | Align readiness docs | Engineering | Agent 1 | P2 | Backlog | — | Planning drift |

---

## How to brief Agent 0

Give a business objective. Expect:

- Impact / effort / ROI / go-now decision  
- Milestones + department + agent assignments  
- Single highest-impact next action when asked “what next?”  
- No specialist coding unless Executive Office authorizes it  


---

## Sprint log — 2026-07-10

**100-Minute Autonomous Content Production Sprint:** completed.
See .
