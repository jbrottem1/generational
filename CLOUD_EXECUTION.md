# Cloud Execution — Planning & Packaging Only

**Mode:** `ExecutionMode.CLOUD`  
**Detection:** Cursor cloud agent, CI, Linux VM (default), or `GENERATIONAL_EXECUTION_MODE=cloud`

---

## Cloud is responsible for

- Planning and architecture
- Coding, refactoring, documentation
- Research and agent collaboration
- SEO analysis
- Script generation, storyboards, shot lists
- **Render plans** (`LOCAL_RENDER_JOB.json`)
- Code review and integration audits

---

## Cloud must NOT

- Claim `"Video exported."` for user Desktop delivery
- Assume `Path.home()/Desktop` on a cloud VM equals the user's Mac Finder
- Report production SUCCESS without a verified MP4 on the **user's Mac**

---

## Cloud production workflow

1. Author or update lesson script + demo_id + assets list
2. Run production script (e.g. `foundation_v2_turtles.py`) — gate stops render
3. Script writes **`LOCAL_RENDER_JOB.json`** containing:
   - Script + timing beats
   - Asset URLs and catalog image IDs
   - Narration provider settings
   - Animation demo_id and renderer path
   - Export filename and Desktop destination
   - Local command to execute
4. Return status:

```json
{
  "ok": true,
  "status": "awaiting_local_render",
  "message": "Production package prepared. Awaiting local render.",
  "job_path": "/path/to/LOCAL_RENDER_JOB.json",
  "local_command": "python3 scripts/run_local_render_job.py --job LOCAL_RENDER_JOB.json"
}
```

5. Commit the job JSON + code changes; open PR
6. User runs local render on Mac (see [LOCAL_EXECUTION.md](./LOCAL_EXECUTION.md))

---

## Snapshot

Each gated run writes:

`data/productions/execution_context.json`

Use this in audits to prove which mode executed.

---

## Smoke / CI on cloud

Cloud CI may run unit tests and **plan-only** production scripts.

Optional `GENERATIONAL_CLOUD_SMOKE_TEST=1` allows render-to-workspace for engineering validation — output still **must not** be reported as user Desktop SUCCESS.

---

## Failure policy (cloud)

| Wrong | Right |
|-------|-------|
| "Exported Biology_202_Origin_of_Turtles.mp4 to Desktop" | "Production package prepared. Awaiting local render." |
| `ok: true` with cloud VM export path as final | `status: awaiting_local_render` + job path |
| Skip job JSON | Always write `LOCAL_RENDER_JOB.json` when render blocked |
