"""Semantic fingerprinting of proposed actions, for duplicate detection."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence


def _canonicalize(value: Any) -> Any:
    """Reduce *value* to a canonical, JSON-serializable form.

    Normalization rules:

    - mapping key order is irrelevant (keys are sorted at serialization),
    - sequences keep their order,
    - integral floats collapse to ints (``1.0`` fingerprints like ``1``),
    - strings are stripped of surrounding whitespace,
    - booleans and ``None`` pass through unchanged.
    """
    if isinstance(value, Mapping):
        return {str(key): _canonicalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else value
    if isinstance(value, int):
        return value
    raise TypeError(
        f"unsupported type in action: {type(value).__name__!s} "
        "(use mappings, sequences, strings, numbers, booleans, or None)"
    )


def semantic_fingerprint(action: Mapping[str, Any]) -> str:
    """Return a stable SHA-256 hex digest for *action*.

    Two actions that mean the same thing — same fields and values, regardless
    of key order, ``1`` vs ``1.0``, or stray whitespace in strings — produce
    the same fingerprint. This is the anti-duplicate primitive used by the
    harness and the broker.
    """
    canonical = _canonicalize(action)
    blob = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


__all__: Sequence[str] = ["semantic_fingerprint"]
