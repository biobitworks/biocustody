"""seedgraph_canonical_v1 — frozen legacy serializer (do not mutate existing hashes).

Matches seedgraph.canonical.canonical_json_bytes / canonical_hash for dict payloads.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

CANONICALIZATION = "seedgraph_canonical_v1"


def canonical_json_bytes_v1(obj: dict[str, Any]) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def canonical_hash_v1(obj: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes_v1(obj)).hexdigest()


def hash_sentence_leaf_v1(normalized_text: str, byte_range: tuple[int, int]) -> str:
    """Legacy seedgraph merkle sentence leaf (ambiguous tuple concat — regression fixture F)."""
    payload = normalized_text + str(byte_range[0]) + "-" + str(byte_range[1])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def hash_citation_leaf_v1(
    authors: list[str],
    title: str,
    year: int,
    doi: str | None,
    pmid: str | None,
) -> str:
    """Legacy seedgraph citation leaf (authors sorted — regression fixture G)."""
    return canonical_hash_v1(
        {
            "authors": sorted(authors),
            "title": title.lower().strip(),
            "year": year,
            "doi": (doi or "").lower(),
            "pmid": pmid or "",
        }
    )
