"""Run state machine: STARTED -> COMPLETED | FAILED."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .events import utcnow


class RunState(str, Enum):
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


_ALLOWED_TRANSITIONS: dict[RunState, frozenset[RunState]] = {
    RunState.STARTED: frozenset({RunState.COMPLETED, RunState.FAILED}),
    RunState.COMPLETED: frozenset(),
    RunState.FAILED: frozenset(),
}


class InvalidTransition(RuntimeError):
    """Raised on an attempt to leave a terminal run state."""


def _new_run_id() -> str:
    return uuid.uuid4().hex


@dataclass
class Run:
    """One processing attempt for one event.

    A run starts in ``STARTED`` and ends in exactly one terminal state,
    ``COMPLETED`` or ``FAILED``. Terminal states are final.
    """

    source_key: str
    run_id: str = field(default_factory=_new_run_id)
    state: RunState = RunState.STARTED
    started_at: datetime = field(default_factory=utcnow)
    finished_at: datetime | None = None
    error: str | None = None

    @property
    def is_terminal(self) -> bool:
        return not _ALLOWED_TRANSITIONS[self.state]

    def complete(self) -> None:
        self._transition(RunState.COMPLETED)

    def fail(self, error: str) -> None:
        self._transition(RunState.FAILED)
        self.error = error

    def _transition(self, target: RunState) -> None:
        if target not in _ALLOWED_TRANSITIONS[self.state]:
            raise InvalidTransition(
                f"run {self.run_id}: cannot transition {self.state.value} -> {target.value}"
            )
        self.state = target
        self.finished_at = utcnow()
