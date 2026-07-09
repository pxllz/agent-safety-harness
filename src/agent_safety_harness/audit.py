"""A simple append-only audit log."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from .events import utcnow


@dataclass(frozen=True)
class AuditRecord:
    category: str
    message: str
    data: Mapping[str, Any]
    at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        object.__setattr__(self, "data", MappingProxyType(dict(self.data)))

    def as_dict(self) -> dict[str, Any]:
        return {
            "at": self.at.isoformat(),
            "category": self.category,
            "message": self.message,
            "data": dict(self.data),
        }


class AuditLog:
    """Append-only, in-memory audit trail with JSONL export."""

    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    def append(self, category: str, message: str, **data: Any) -> AuditRecord:
        record = AuditRecord(category=category, message=message, data=data)
        self._records.append(record)
        return record

    @property
    def records(self) -> tuple[AuditRecord, ...]:
        return tuple(self._records)

    def to_jsonl(self) -> str:
        return "\n".join(json.dumps(r.as_dict(), default=str, sort_keys=True) for r in self._records)

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.write_text(self.to_jsonl() + "\n", encoding="utf-8")
        return path

    def __len__(self) -> int:
        return len(self._records)
