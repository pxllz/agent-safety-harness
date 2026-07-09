"""Fake execution backend. The only broker in this project — on purpose."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any, Mapping, Protocol

from .events import utcnow
from .fingerprint import semantic_fingerprint
from .risk import RiskApproval


@dataclass(frozen=True)
class ExecutionReport:
    """Record of one (fake) execution."""

    action_fingerprint: str
    status: str
    action: Mapping[str, Any]
    executed_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        object.__setattr__(self, "action", MappingProxyType(dict(self.action)))


class ApprovalMismatch(RuntimeError):
    """Raised when an approval does not match the action being executed."""


class Broker(Protocol):
    """Anything that can execute an approved action."""

    def submit(self, action: Mapping[str, Any], approval: RiskApproval) -> ExecutionReport: ...


class FakeBroker:
    """Records approved actions in memory. Never touches the outside world.

    ``submit`` refuses any action whose semantic fingerprint does not match
    the fingerprint the approval was issued for.
    """

    def __init__(self) -> None:
        self._history: list[ExecutionReport] = []

    @property
    def history(self) -> tuple[ExecutionReport, ...]:
        return tuple(self._history)

    def submit(self, action: Mapping[str, Any], approval: RiskApproval) -> ExecutionReport:
        fingerprint = semantic_fingerprint(action)
        if approval.action_fingerprint != fingerprint:
            raise ApprovalMismatch(
                "approval was issued for a different action "
                f"({approval.action_fingerprint[:12]}… != {fingerprint[:12]}…)"
            )
        report = ExecutionReport(
            action_fingerprint=fingerprint,
            status="FILLED_FAKE",
            action=action,
        )
        self._history.append(report)
        return report
