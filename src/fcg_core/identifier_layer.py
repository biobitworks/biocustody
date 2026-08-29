"""Canonical identifier / citation layer for AUD-FCG-ATOM-SOT-ROUNDTRIP-002."""

from __future__ import annotations

import re
from typing import Any

from fcg_core.canonical_v2 import canonical_hash_v2

DOI_RULESET_SHA = canonical_hash_v2({"ruleset": "doi_normalization_v1"})


def normalize_doi(presentation: str) -> str | None:
    s = presentation.strip().lower()
    s = s.replace("https://doi.org/", "").replace("http://doi.org/", "").replace("doi:", "")
    if re.match(r"^10\.\d{4,9}/[-._;()/:a-z0-9]+", s):
        return s
    return None


def identifier_semantic_id(identifier_type: str, canonical_value: str) -> str:
    return canonical_hash_v2(
        {
            "domain": "fcg.identifier.v1",
            "identifier_type": identifier_type,
            "canonical_value": canonical_value,
            "doi_ruleset_sha256": DOI_RULESET_SHA if identifier_type == "DOI" else None,
        }
    )


def build_identifier_record(identifier_type: str, presentation: str, **extra: Any) -> dict[str, Any]:
    if identifier_type == "DOI":
        canonical = normalize_doi(presentation)
        if not canonical:
            raise ValueError(f"invalid DOI presentation: {presentation!r}")
    elif identifier_type == "BIBKEY_ALIAS":
        canonical = presentation.strip()
    elif identifier_type == "GIT_COMMIT":
        canonical = presentation.strip().lower()
    else:
        canonical = presentation.strip().lower()
    sem = identifier_semantic_id(identifier_type, canonical)
    return {
        "IDENTIFIER_ID": f"ID-{sem[:16]}",
        "SEMANTIC_ID": sem,
        "identifier_type": identifier_type,
        "presentation": presentation,
        "canonical_value": canonical,
        "doi_ruleset_sha256": DOI_RULESET_SHA if identifier_type == "DOI" else None,
        **extra,
    }


def build_resource(identifier_id: str, resource_type: str, title: str) -> dict[str, Any]:
    sem = canonical_hash_v2({"domain": "fcg.resource.v1", "identifier_id": identifier_id, "resource_type": resource_type, "title": title})
    return {
        "RESOURCE_ID": f"RES-{sem[:16]}",
        "SEMANTIC_ID": sem,
        "identifier_id": identifier_id,
        "resource_type": resource_type,
        "title": title,
    }


def build_citation_occurrence(
    *,
    bib_key: str,
    identifier_id: str,
    structural_object_id: str,
    occurrence_id_val: str,
) -> dict[str, Any]:
    sem = canonical_hash_v2(
        {
            "domain": "fcg.citation_occurrence.v1",
            "bib_key": bib_key,
            "identifier_id": identifier_id,
            "structural_object_id": structural_object_id,
        }
    )
    return {
        "CITATION_OCCURRENCE_ID": f"CIT-OCC-{sem[:16]}",
        "SEMANTIC_ID": sem,
        "bib_key_local_alias": bib_key,
        "identifier_id": identifier_id,
        "structural_object_id": structural_object_id,
        "occurrence_id": occurrence_id_val,
        "note": "bib_key is LOCAL ALIAS only; not canonical scholarly identity",
    }
