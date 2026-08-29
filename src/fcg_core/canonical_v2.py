"""rfc8785_jcs_v2 — versioned successor for new semantic objects."""

from __future__ import annotations

import hashlib
from typing import Any

try:
    import rfc8785

    _HAS_RFC8785 = True
except ImportError:  # pragma: no cover
    _HAS_RFC8785 = False

CANONICALIZATION = "rfc8785_jcs_v2"


def canonical_json_bytes_v2(payload: Any) -> bytes:
    if _HAS_RFC8785:
        return rfc8785.dumps(payload)
    # Strict fallback for CI without rfc8785 — ASCII finite payloads only.
    import json

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def canonical_hash_v2(payload: Any) -> str:
    return hashlib.sha256(canonical_json_bytes_v2(payload)).hexdigest()
