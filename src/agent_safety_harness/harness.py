"""The orchestrator: gates -> idempotency -> risk -> anti-duplicate -> execution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from .audit import AuditLog
from .broker import Broker, ExecutionReport, FakeBroker
from .events import Event, EventStore
from .fingerprint import semantic_fingerprint
from .gates import EmergencyStopGate, PauseGate
from .risk import RiskPolicy, RiskResult, issue_approval
from .run import Run


class Outcome(str, Enum):
    """What happened to one event."""

    DRY_RUN = "DRY_RUN"                    # approved; would have executed
    EXECUTED = "EXECUTED"                  # approved and executed by the (fake) broker
    REJECTED = "REJECTED"                  # risk policy said no
    DUPLICATE_EVENT = "DUPLICATE_EVENT"    # same source_key seen before
    DUPLICATE_ACTION = "DUPLICATE_ACTION"  # same semantic fingerprint seen before
    PAUSED = "PAUSED"                      # blocked by the pause gate
    STOPPED = "STOPPED"                    # blocked by the emergency stop gate


@dataclass(frozen=True)
class ProcessResult:
    outcome: Outcome
    run: Run | None = None
    risk: RiskResult | None = None
    report: ExecutionReport | None = None


class SafetyHarness:
    """Processes events through a fixed, deterministic pipeline.

    For each event:

    1. the emergency-stop gate, then the pause gate, may block everything;
    2. the event store drops redeliveries (same ``source_key``);
    3. a :class:`Run` is started;
    4. the risk policy evaluates the proposed action (``event.payload``);
    5. the semantic fingerprint blocks actions already decided on;
    6. in dry-run mode (the default) the action is recorded, not executed;
       otherwise it goes to the broker with a fingerprint-bound approval.

    Every step is appended to the audit log. Gate blocks happen *before*
    idempotency, so an event delivered while paused can be redelivered
    after ``resume()`` and will still be processed.
    """

    def __init__(
        self,
        policy: RiskPolicy,
        broker: Broker | None = None,
        dry_run: bool = True,
        audit: AuditLog | None = None,
    ) -> None:
        self.policy = policy
        self.broker: Broker = broker if broker is not None else FakeBroker()
        self.dry_run = dry_run
        self.audit = audit if audit is not None else AuditLog()
        self.pause_gate = PauseGate()
        self.emergency_stop = EmergencyStopGate()
        self.events = EventStore()
        self._decided_fingerprints: set[str] = set()
        self.runs: list[Run] = []

    # -- operator controls -------------------------------------------------

    def pause(self, reason: str | None = None) -> None:
        self.pause_gate.pause(reason)
        self.audit.append("gate", "pause engaged", reason=reason)

    def resume(self) -> None:
        self.pause_gate.resume()
        self.audit.append("gate", "pause released")

    def stop(self, reason: str) -> None:
        """Trigger the emergency stop. Latching: there is no way back."""
        self.emergency_stop.trigger(reason)
        self.audit.append("gate", "EMERGENCY STOP triggered", reason=reason)

    # -- pipeline ----------------------------------------------------------

    def process(self, event: Event) -> ProcessResult:
        if self.emergency_stop.is_stopped:
            self.audit.append(
                "blocked", "event blocked by emergency stop",
                source_key=event.source_key, reason=self.emergency_stop.reason,
            )
            return ProcessResult(Outcome.STOPPED)

        if self.pause_gate.is_paused:
            self.audit.append(
                "blocked", "event blocked by pause gate",
                source_key=event.source_key, reason=self.pause_gate.reason,
            )
            return ProcessResult(Outcome.PAUSED)

        if not self.events.ingest(event):
            self.audit.append(
                "idempotency", "duplicate event dropped", source_key=event.source_key
            )
            return ProcessResult(Outcome.DUPLICATE_EVENT)

        run = Run(source_key=event.source_key)
        self.runs.append(run)
        self.audit.append("run", "run started", run_id=run.run_id, source_key=event.source_key)

        try:
            action: Mapping[str, Any] = dict(event.payload)
            risk = self.policy.evaluate(action)

            if not risk.approved:
                run.complete()
                self.audit.append(
                    "risk", "action rejected", run_id=run.run_id, reasons=list(risk.reasons)
                )
                return ProcessResult(Outcome.REJECTED, run=run, risk=risk)

            fingerprint = semantic_fingerprint(action)
            if fingerprint in self._decided_fingerprints:
                run.complete()
                self.audit.append(
                    "anti-duplicate", "semantically duplicate action blocked",
                    run_id=run.run_id, fingerprint=fingerprint,
                )
                return ProcessResult(Outcome.DUPLICATE_ACTION, run=run, risk=risk)
            self._decided_fingerprints.add(fingerprint)

            if self.dry_run:
                run.complete()
                self.audit.append(
                    "dry-run", "action approved — would execute",
                    run_id=run.run_id, fingerprint=fingerprint, action=action,
                )
                return ProcessResult(Outcome.DRY_RUN, run=run, risk=risk)

            approval = issue_approval(risk, action)
            report = self.broker.submit(action, approval)
            run.complete()
            self.audit.append(
                "execution", "action executed",
                run_id=run.run_id, fingerprint=fingerprint, status=report.status,
            )
            return ProcessResult(Outcome.EXECUTED, run=run, risk=risk, report=report)

        except Exception as exc:
            run.fail(str(exc))
            self.audit.append("run", "run failed", run_id=run.run_id, error=str(exc))
            raise
