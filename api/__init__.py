"""Internal production HTTP API (Agent 1 readiness).

Thin stdlib surface over Orchestrator / Workflow Executor / readiness —
not a public SaaS API. Start with `python -m api.server`.
"""

from api.server import create_handler, serve

__all__ = ["create_handler", "serve"]
