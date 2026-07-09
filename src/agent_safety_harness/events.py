"""Events entering the harness, with idempotent ingestion."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping


def utcnow() -> datetime:
    """Timezone-aware UTC timestamp used across the library."""
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Event:
    """An external stimulus the agent may react to.

    ``source_key`` is the idempotency key: two events carrying the same
    ``source_key`` are considered the same real-world occurrence, no matter
    how many times they are delivered. ``payload`` describes the action the
    agent proposes in response to the event.
    """

    source_key: str
    kind: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        if not self.source_key:
            raise ValueError("source_key must be a non-empty string")
        if not self.kind:
            raise ValueError("kind must be a non-empty string")
        # Freeze the payload so an Event cannot mutate after ingestion.
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))


class EventStore:
    """In-memory idempotent event store keyed by ``source_key``."""

    def __init__(self) -> None:
        self._events: dict[str, Event] = {}

    def ingest(self, event: Event) -> bool:
        """Store *event*; return ``False`` if its source_key was already seen."""
        if event.source_key in self._events:
            return False
        self._events[event.source_key] = event
        return True

    def get(self, source_key: str) -> Event | None:
        return self._events.get(source_key)

    def __contains__(self, source_key: object) -> bool:
        return source_key in self._events

    def __len__(self) -> int:
        return len(self._events)
