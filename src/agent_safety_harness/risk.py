"""Risk evaluation: RiskResult, RiskApproval, and a small built-in policy."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable, Mapping, Protocol

from .events import utcnow
from .fingerprint import semantic_fingerprint


@dataclass(frozen=True)
class RiskResult:
    """Outcome of evaluating one proposed action against a policy."""

    approved: bool
    reasons: tuple[str, ...] = ()
    checked_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True)
class RiskApproval:
    """Proof that a *specific* action passed risk evaluation.

    The approval is bound to the action's semantic fingerprint, so it cannot
    be reused for a different action.
    """

    action_fingerprint: str
    reasons: tuple[str, ...] = ()
    issued_at: datetime = field(default_factory=utcnow)


class NotApproved(RuntimeError):
    """Raised when asking for an approval from a rejecting RiskResult."""


def issue_approval(result: RiskResult, action: Mapping[str, Any]) -> RiskApproval:
    """Turn an approving :class:`RiskResult` into a fingerprint-bound approval."""
    if not result.approved:
        raise NotApproved(f"action was rejected: {'; '.join(result.reasons) or 'no reason given'}")
    return RiskApproval(
        action_fingerprint=semantic_fingerprint(action),
        reasons=result.reasons,
    )


class RiskPolicy(Protocol):
    """Anything that can evaluate a proposed action."""

    def evaluate(self, action: Mapping[str, Any]) -> RiskResult: ...


class BasicRiskPolicy:
    """A deliberately simple deterministic policy.

    Approves an action when:

    - its ``kind`` field is in ``allowed_kinds``, and
    - if ``max_magnitude`` is set, its ``magnitude_field`` value (default
      ``"magnitude"``, missing counts as 0) does not exceed it.

    This is an example policy for tests and demos; real users are expected
    to provide their own :class:`RiskPolicy` implementation.
    """

    def __init__(
        self,
        allowed_kinds: Iterable[str],
        max_magnitude: float | None = None,
        magnitude_field: str = "magnitude",
    ) -> None:
        self.allowed_kinds = frozenset(allowed_kinds)
        self.max_magnitude = max_magnitude
        self.magnitude_field = magnitude_field

    def evaluate(self, action: Mapping[str, Any]) -> RiskResult:
        reasons: list[str] = []

        kind = action.get("kind")
        if kind not in self.allowed_kinds:
            reasons.append(f"kind {kind!r} is not in the allowed set")

        if self.max_magnitude is not None:
            magnitude = action.get(self.magnitude_field, 0)
            if not isinstance(magnitude, (int, float)) or isinstance(magnitude, bool):
                reasons.append(f"{self.magnitude_field} must be a number")
            elif magnitude > self.max_magnitude:
                reasons.append(
                    f"{self.magnitude_field} {magnitude} exceeds limit {self.max_magnitude}"
                )

        if reasons:
            return RiskResult(approved=False, reasons=tuple(reasons))
        return RiskResult(approved=True, reasons=("all checks passed",))
