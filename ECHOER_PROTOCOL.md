# Echoer Communication Protocol (ECP v1)

**Owner:** Agent 0 · **Status:** REQUIRED for all sprint agents

Echoer is the executive coordination bus. Every agent sends and receives **structured JSON messages** — never unstructured prose for task handoffs.

## Message envelope

```json
{
  "msg_id": "ecp_abc123",
  "msg_type": "task|status|result|error|lesson|query",
  "from_agent": "0",
  "to_agent": "24",
  "project_id": "sprint6h30_cycle_03",
  "cycle_id": "03",
  "objective": "Review engagement for DNA Short",
  "payload": {},
  "context": {},
  "priority": "p2",
  "retry_count": 0,
  "max_retries": 2,
  "created_at": "ISO-8601"
}
```

## Response envelope

```json
{
  "msg_id": "ecp_reply_xyz",
  "in_reply_to": "ecp_abc123",
  "from_agent": "24",
  "status": "ok|partial|failed|blocked",
  "summary": "One-line outcome",
  "data": {},
  "evidence": {"export_path": "...", "scores": {}},
  "errors": [],
  "warnings": [],
  "cost_estimate_usd": 0.09,
  "duration_sec": 28.4,
  "completed_at": "ISO-8601"
}
```

## Rules

1. **Clarity** — `objective` is one imperative sentence; `payload` holds structured fields only.
2. **Parsing** — Use `parse_response()`; never assume free-text format.
3. **Errors** — Failed tasks set `status=failed`, populate `errors[]`, increment `retry_count`.
4. **Routing** — Agent 0 routes via `route_to_agent(task_kind)`; QC (Agent 17) never reviews its own output.
5. **Context** — Pass `cycle_id`, prior scores, and lessons in `context` — not in objective text.
6. **Lessons** — Validated improvements use `msg_type=lesson` → GCIS `lessons_learned.md`.
7. **Secrets** — Never include API keys, tokens, or raw credentials in messages.
8. **Status** — Long tasks emit `msg_type=status` at stage boundaries.

## Routing table

| Task kind | Agent |
|-----------|-------|
| research | 11 |
| seo | 8 |
| script | 3 |
| education | 24 |
| engagement | 24 |
| animation | 16 |
| voice | 5 |
| render | 6 |
| qc | 17 |
| publish | 7 |
| gcis | 0 |

## Implementation

`services/echoer/protocol.py` — `build_message`, `parse_response`, `EchoerMessage`, `EchoerResponse`

Sprint logs: `data/productions/_validation/sprint_6h30/echoer_log.jsonl`
