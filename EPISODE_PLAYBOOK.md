# Generational Episode Playbook

Long-term institutional memory for educational episode design patterns.
Owned by Agent 25 (Retention & Episode Design). Stored separately from
Analytics Memory and Executive Memory under `data/episode_design/`.

## Purpose

Every successful lesson strengthens the company's understanding of effective
educational storytelling:

- Reusable patterns (hooks, reveals, bridges)
- Common weaknesses
- Measurable improvement recommendations
- Niche-specific flows viewers recognize and return for

## API

```python
from services.episode_design import get_playbook

pb = get_playbook(data_dir="data/episode_design")
pid = pb.record_pattern(
    pattern_name="Curiosity Hook + Reveal",
    niche="Science",
    description="Counterintuitive question → demonstration → reveal",
    strengths=["high curiosity"],
    weaknesses=["needs strong visuals"],
)
pb.record_success(pid, project_id="abc123", retention_score=88)
print(pb.summary())
```

## Automatic learning

When `episode_design` scores a lesson ≥ 70, it records/updates a niche pattern
and appends a success metric. Override storage with context key
`episode_playbook_dir` (used by tests).

## Pattern fields

See `PLAYBOOK_FIELDS` in `services/episode_design/models.py`:
`pattern_id`, `pattern_name`, `description`, `niche`, `strengths`,
`weaknesses`, `successes`, `improvement_notes`, `times_used`,
`average_retention_score`, `last_updated`.
