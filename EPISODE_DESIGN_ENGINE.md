# Retention & Episode Design Engine (Agent 25)

> **Numbering note:** The mission brief requested Agent 24. Agent 24 is already
> **Executive Intelligence** (`autonomous_executive`). This engine is registered
> as **Agent 25** with key `episode_design`.

The Director of Retention & Episode Design makes every educational episode more
engaging, memorable, and satisfying to finish. It does **not** animate or render.
It reviews completed scripts and designs *how* information should be presented.

## Pipeline position

```
Quality → Episode Design → AI Director → Creative Studio → …
```

First distribution stage after packaging. Writes `episode_design_package`;
downstream agents read it and keep their own slots.

## What it produces

| Output | Description |
|---|---|
| **Lesson Blueprint** | Canonical 7-beat timing structure (49s educational format) |
| **Retention Review** | 7 dimension scores + specific revision notes |
| **Series Design** | Mini-series / season sequencing, callbacks, continuity |
| **Strategic Answers** | Why care / surprise / first beat / reveal / pause / ending |
| **Episode Playbook** | Persistent patterns under `data/episode_design/` |

### Canonical blueprint beats

| Sec | Beat |
|---|---|
| 0–2 | Curiosity Hook |
| 2–7 | Interesting Question |
| 7–17 | Demonstration |
| 17–32 | Explanation (reveal + pause) |
| 32–42 | Real-world Application |
| 42–47 | Powerful Takeaway (reveal + pause) |
| 47–49 | Bridge to Next Lesson |

## Quick start

```python
import engines  # noqa: F401
from engines import registry
from services.orchestrator import Orchestrator

updates = registry.get_engine("episode_design").run({
    "unified_packages": [{"topic": "...", "script": "...", "hook": "..."}],
})

report = Orchestrator().run_episode_design_stage(context)
```

## Ownership

Writes only:

- `item["episode_design_package"]`
- `episode_design_summary`
- `episode_design_packages`

Reads (never mutates): script, hook, psychology, research, visual, quality,
and other upstream slots.

## Collaboration

Improves how Research, SEO, Psychology, Script, Animation, Quality, and
Publishing fit together into one complete episode — without duplicating them.

## Landing zone

- `engines/episode_design.py`
- `services/episode_design/`
- `tests/test_episode_design_engine.py`
- `EPISODE_DESIGN_ENGINE.md` (this file)
- `EPISODE_PLAYBOOK.md`

See also: `DATA_CONTRACTS.md`, `PIPELINE_SPEC.md`, `AI_DIRECTOR.md`.
