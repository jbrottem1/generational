"""Future-roadmap extension points — clean interfaces, no implementations.

Everything here is deliberately a seam, not a feature:

- `PrePublishGate`      — approval workflows / human review before publish
- `PublishListener`     — analytics callbacks after every attempt
- `RollbackHandler`     — withdraw a published post on failure/policy
- `RegionalScheduleRule` — per-region scheduling policy overrides

The PublishingManager already calls the gate and listener hooks, so real
implementations (approval UIs, analytics ingestion, platform delete APIs)
plug in with `register_*()` — zero engine or manager changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.log import get_logger, log_event

logger = get_logger(__name__)


class PrePublishGate(ABC):
    """Approval workflow / human-review gate consulted before every publish."""

    key: str = ""

    @abstractmethod
    def review(self, job: dict) -> "list[str]":
        """Problems that block this publish (empty list = approved)."""


class PublishListener(ABC):
    """Analytics callback fired after every publish attempt."""

    key: str = ""

    @abstractmethod
    def on_publish_attempt(self, job: dict, attempt: dict) -> None:
        """Receive the job + attempt record (contains `analytics_ref`)."""


class RollbackHandler(ABC):
    """Future contract for withdrawing a published post."""

    key: str = ""

    @abstractmethod
    def rollback(self, job: dict, reason: str) -> dict:
        """Attempt to take the post down; returns a rollback report."""


class RegionalScheduleRule(ABC):
    """Future contract for per-region scheduling policy overrides."""

    key: str = ""

    @abstractmethod
    def adjust(self, schedule: dict, package: dict) -> dict:
        """Return an adjusted schedule entry for the package's region."""


_gates: "list[PrePublishGate]" = []
_listeners: "list[PublishListener]" = []
_rollback_handlers: "list[RollbackHandler]" = []


def register_pre_publish_gate(gate: PrePublishGate) -> None:
    _gates.append(gate)
    log_event(logger, "publishing.gate_registered", key=gate.key)


def register_publish_listener(listener: PublishListener) -> None:
    _listeners.append(listener)
    log_event(logger, "publishing.listener_registered", key=listener.key)


def register_rollback_handler(handler: RollbackHandler) -> None:
    _rollback_handlers.append(handler)
    log_event(logger, "publishing.rollback_handler_registered", key=handler.key)


def unregister_pre_publish_gate(gate: PrePublishGate) -> None:
    if gate in _gates:
        _gates.remove(gate)


def unregister_publish_listener(listener: PublishListener) -> None:
    if listener in _listeners:
        _listeners.remove(listener)


def run_pre_publish_gates(job: dict) -> "list[str]":
    """All blocking problems from registered gates (empty = approved).

    A crashing gate never blocks the pipeline — it is logged and skipped.
    """
    problems = []
    for gate in _gates:
        try:
            problems.extend(gate.review(job))
        except Exception as exc:  # noqa: BLE001 - gates must not crash publishing
            log_event(logger, "publishing.gate_error", level=30, key=gate.key, error=str(exc)[:120])
    return problems


def notify_publish_listeners(job: dict, attempt: dict) -> None:
    """Fire analytics callbacks; listener errors are logged, never raised."""
    for listener in _listeners:
        try:
            listener.on_publish_attempt(job, attempt)
        except Exception as exc:  # noqa: BLE001 - callbacks must not crash publishing
            log_event(logger, "publishing.listener_error", level=30, key=listener.key, error=str(exc)[:120])


def rollback_handlers() -> "list[RollbackHandler]":
    return list(_rollback_handlers)
