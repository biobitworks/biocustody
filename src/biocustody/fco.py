from __future__ import annotations
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Any
from .canonical import sha256_canonical

@dataclass(frozen=True)
class FCO:
    fco_version: str
    object_type: str
    payload: dict[str, Any]
    source: dict[str, Any]
    parents: tuple[str, ...] = field(default_factory=tuple)
    transformation: dict[str, Any] = field(default_factory=dict)
    claim: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    digest: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

def make_fco(
    object_type: str,
    payload: dict[str, Any],
    source: dict[str, Any],
    *,
    parents: list[str] | tuple[str, ...] = (),
    transformation: dict[str, Any] | None = None,
    claim: dict[str, Any] | None = None,
    created_at: str | None = None,
    fco_version: str = "hackday-0.2",
) -> FCO:
    created_at = created_at or datetime.now(timezone.utc).isoformat()
    unsigned = {
        "fco_version": fco_version,
        "object_type": object_type,
        "payload": payload,
        "source": source,
        "parents": list(parents),
        "transformation": transformation or {},
        "claim": claim or {},
        "created_at": created_at,
    }
    digest = "sha256:" + sha256_canonical(unsigned)
    return FCO(
        fco_version=fco_version,
        object_type=object_type,
        payload=payload,
        source=source,
        parents=tuple(parents),
        transformation=transformation or {},
        claim=claim or {},
        created_at=created_at,
        digest=digest,
    )

def verify_fco(fco: FCO) -> bool:
    unsigned = {
        "fco_version": fco.fco_version,
        "object_type": fco.object_type,
        "payload": fco.payload,
        "source": fco.source,
        "parents": list(fco.parents),
        "transformation": fco.transformation,
        "claim": fco.claim,
        "created_at": fco.created_at,
    }
    return fco.digest == "sha256:" + sha256_canonical(unsigned)

def route_compare(left: list[FCO], right: list[FCO]) -> dict[str, Any]:
    n = min(len(left), len(right))
    for i in range(n):
        if left[i].digest != right[i].digest:
            return {
                "same": False,
                "first_divergent_index": i,
                "left": left[i].digest,
                "right": right[i].digest,
            }
    if len(left) != len(right):
        return {
            "same": False,
            "first_divergent_index": n,
            "left": left[n].digest if len(left) > n else None,
            "right": right[n].digest if len(right) > n else None,
        }
    return {"same": True, "first_divergent_index": None}
