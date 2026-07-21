# Generational Version 1 Launch Program

**Role:** Chief Operating Officer operations  
**Architecture:** Frozen — no new engines  
**CLI:** `scripts/v1_launch.py`  
**Package:** `services/v1_launch/`

Generational now operates as a production company. This program proves whether the existing stack can repeatedly produce publication-ready educational videos.

---

## Phases

### 1 — Production readiness
```bash
python scripts/v1_launch.py health
```
→ `V1_LAUNCH_READINESS.md`

### 2 — Pilot (25 videos)
Categories: Biology · AI · Space · Physics · Psychology · Medicine

```bash
python scripts/v1_launch.py pilot --limit 25
# resume-friendly
python scripts/v1_launch.py pilot --offset 10 --limit 5
```

Publishing stays **off**.

### 3 — Executive review
```bash
python scripts/v1_launch.py dashboard
```
→ `V1_LAUNCH_EXECUTIVE_DASHBOARD.md`

### 4 — Launch recommendation
```bash
python scripts/v1_launch.py recommend
```
→ `READY_FOR_LAUNCH` | `READY_WITH_MINOR_FIXES` | `NOT_READY`

### Full program
```bash
python scripts/v1_launch.py run-program --limit 25
```

---

## Decision thresholds

| Decision | Conditions |
|----------|------------|
| READY_FOR_LAUNCH | n≥20 · success≥90% · MP4≥90% · avg score≥80 |
| READY_WITH_MINOR_FIXES | n≥20 · success≥75% · MP4≥80% · avg score≥75 |
| NOT_READY | Otherwise (including MP4&lt;80%) |
