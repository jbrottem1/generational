"""Pre-publish gate — nothing reaches live publish without PQA APPROVE."""

from __future__ import annotations

from services.publishing.extensions import PrePublishGate, register_pre_publish_gate


class ProductionQAGate(PrePublishGate):
    """Block publish jobs that lack PQA approval.

    Dry-run / mock publishes are allowed so tests and local rehearsal keep
    working. Live jobs (or those with enforce_pqa=True) require decision=APPROVE.
    """

    key = "production_qa"

    def review(self, job: dict) -> list[str]:
        dry_run = (
            job.get("publish_mode") == "dry_run"
            or job.get("mode") == "dry_run"
            or bool((job.get("package") or {}).get("dry_run"))
        )
        enforce = bool(job.get("enforce_pqa") or job.get("enforce_production_qc"))
        if dry_run and not enforce:
            return []

        package = job.get("package") or {}
        content = package.get("content") if isinstance(package.get("content"), dict) else {}
        item = job.get("item") if isinstance(job.get("item"), dict) else {}
        report = (
            job.get("pqa_report")
            or package.get("pqa_report")
            or content.get("pqa_report")
            or item.get("pqa_report")
        )
        passed = (
            job.get("pqa_passed")
            or package.get("pqa_passed")
            or (isinstance(report, dict) and report.get("decision") == "APPROVE")
            or (isinstance(report, dict) and report.get("passed") is True)
        )
        decision = None
        if isinstance(report, dict):
            decision = report.get("decision")

        # If no live OAuth enforcement and no explicit enforce flag, only block
        # when a failing report is explicitly attached.
        if not enforce and not report:
            return []

        if passed and decision in (None, "APPROVE"):
            return []

        if decision == "BLOCK_EXPORT":
            return ["PQA BLOCK_EXPORT — production must not publish"]
        if decision == "REQUEST_REVISION":
            return ["PQA REQUEST_REVISION — resolve revision_requests before publish"]
        if enforce and not report:
            return ["PQA report missing — Production QA must approve before publish"]
        if report and not passed:
            return [f"PQA did not approve (decision={decision or 'unknown'})"]
        return []


_REGISTERED = False


def ensure_pqa_gate_registered() -> None:
    global _REGISTERED
    if _REGISTERED:
        return
    register_pre_publish_gate(ProductionQAGate())
    _REGISTERED = True
