from __future__ import annotations
import json, hashlib, math
from pathlib import Path
from typing import Any

def _clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _clean(value[k]) for k in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    if hasattr(value, "tolist"):
        return _clean(value.tolist())
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Non-finite floats are not allowed in custody-critical payloads.")
        # Stable round-trip representation without arbitrary scientific rounding.
        return float(repr(value))
    if isinstance(value, Path):
        return str(value)
    return value

def canonical_json_bytes(value: Any) -> bytes:
    clean = _clean(value)
    return json.dumps(
        clean,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_canonical(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))

def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()
