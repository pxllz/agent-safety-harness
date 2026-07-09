"""agent-safety-harness: deterministic safety rails for sandboxed autonomous agents."""

from .audit import AuditLog, AuditRecord
from .broker import ApprovalMismatch, Broker, ExecutionReport, FakeBroker
from .events import Event, EventStore
from .fingerprint import semantic_fingerprint
from .gates import EmergencyStopGate, GateBlocked, PauseGate
from .harness import Outcome, ProcessResult, SafetyHarness
from .risk import (
    BasicRiskPolicy,
    NotApproved,
    RiskApproval,
    RiskPolicy,
    RiskResult,
    issue_approval,
)
from .run import InvalidTransition, Run, RunState

__version__ = "0.1.0"

__all__ = [
    "ApprovalMismatch",
    "AuditLog",
    "AuditRecord",
    "BasicRiskPolicy",
    "Broker",
    "EmergencyStopGate",
    "Event",
    "EventStore",
    "ExecutionReport",
    "FakeBroker",
    "GateBlocked",
    "InvalidTransition",
    "NotApproved",
    "Outcome",
    "PauseGate",
    "ProcessResult",
    "RiskApproval",
    "RiskPolicy",
    "RiskResult",
    "Run",
    "RunState",
    "SafetyHarness",
    "issue_approval",
    "semantic_fingerprint",
    "__version__",
]
