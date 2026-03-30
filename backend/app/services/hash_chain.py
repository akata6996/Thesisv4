"""Utilities for canonical hashing used by append-only streams."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any


def _normalize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _normalize(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    return value


def canonical_json(data: dict[str, Any]) -> str:
    """Serialize dict with stable ordering for deterministic hashing."""
    return json.dumps(_normalize(data), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_chain_hash(record_without_curr_hash: dict[str, Any]) -> str:
    serialized = canonical_json(record_without_curr_hash)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
