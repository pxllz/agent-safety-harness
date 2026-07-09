"""Deterministic gates that can block the harness."""

from __future__ import annotations


class GateBlocked(RuntimeError):
    """Raised when a closed gate blocks an operation."""

    def __init__(self, gate: str, reason: str | None = None) -> None:
        self.gate = gate
        self.reason = reason
        detail = f" ({reason})" if reason else ""
        super().__init__(f"blocked by {gate} gate{detail}")


class PauseGate:
    """A resumable gate: paused work can be resumed by an operator."""

    def __init__(self) -> None:
        self._paused = False
        self._reason: str | None = None

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def reason(self) -> str | None:
        return self._reason

    def pause(self, reason: str | None = None) -> None:
        self._paused = True
        self._reason = reason

    def resume(self) -> None:
        self._paused = False
        self._reason = None

    def check(self) -> None:
        """Raise :class:`GateBlocked` if the gate is closed."""
        if self._paused:
            raise GateBlocked("pause", self._reason)


class EmergencyStopGate:
    """A latching gate: once triggered it stays closed for the process lifetime.

    There is deliberately no ``reset()``. Recovering from an emergency stop
    should require restarting the process, not flipping a flag.
    """

    def __init__(self) -> None:
        self._stopped = False
        self._reason: str | None = None

    @property
    def is_stopped(self) -> bool:
        return self._stopped

    @property
    def reason(self) -> str | None:
        return self._reason

    def trigger(self, reason: str) -> None:
        if not reason:
            raise ValueError("an emergency stop requires a reason")
        # First reason wins; later triggers must not rewrite history.
        if not self._stopped:
            self._stopped = True
            self._reason = reason

    def check(self) -> None:
        """Raise :class:`GateBlocked` if the gate has been triggered."""
        if self._stopped:
            raise GateBlocked("emergency-stop", self._reason)
