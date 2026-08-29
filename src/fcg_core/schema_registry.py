"""Schema file SHA-256 registry."""

from __future__ import annotations

import hashlib
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas" / "fcg_core"


def schema_hashes() -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        out[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out
