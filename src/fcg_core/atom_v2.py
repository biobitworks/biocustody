"""SEEDGRAPH_ATOM_V2 — RFC8785 JCS v2 knowledge atoms (successor to legacy merkle v1)."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from fcg_core.canonical_v2 import canonical_hash_v2
from fcg_core.identities import content_id, occurrence_id, semantic_id

ATOM_V2_DOMAIN = "seedgraph.atom.v2"
ATOM_V2_SCHEMA = "1.0.0"
DERIVATION_RULE_SHA = hashlib.sha256(b"atom_v2_derivation_rules_v1").hexdigest()


def atom_semantic_payload(
    *,
    atom_type: str,
    subject: str,
    predicate: str,
    obj: str,
    qualifiers: list[str] | None = None,
    negations: list[str] | None = None,
    quantifiers: list[str] | None = None,
    temporal_scope: str | None = None,
) -> dict[str, Any]:
    return {
        "atom_type": atom_type,
        "subject": subject,
        "predicate": predicate,
        "object": obj,
        "qualifiers": sorted(qualifiers or []),
        "negations": sorted(negations or []),
        "quantifiers": sorted(quantifiers or []),
        "temporal_scope": temporal_scope or "",
    }


def build_atom_v2(
    *,
    atom_type: str,
    subject: str,
    predicate: str,
    obj: str,
    source_text: str,
    structural_object_id: str,
    source_occurrence_id: str,
    source_file: str,
    source_commit: str,
    legacy_merkle_v1_ref: str | None = None,
    qualifiers: list[str] | None = None,
    negations: list[str] | None = None,
    admission_state: str = "ACCEPT",
    proof_state: str = "PENDING",
    claim_ceiling: str = "REPURPOSING_HYPOTHESIS",
) -> dict[str, Any]:
    sem_payload = atom_semantic_payload(
        atom_type=atom_type,
        subject=subject,
        predicate=predicate,
        obj=obj,
        qualifiers=qualifiers,
        negations=negations,
    )
    sem_id = semantic_id(ATOM_V2_DOMAIN, ATOM_V2_SCHEMA, sem_payload)
    cid = content_id(source_text.encode("utf-8"))
    occ = occurrence_id(
        ATOM_V2_DOMAIN,
        cid,
        source_locator=f"{source_file}::{structural_object_id}",
        actor_ref="audit:AUD-FCG-ATOM-SOT-ROUNDTRIP-002",
        provider_ref="biocustody:fcg_core.atom_v2",
        observation_context={"source_commit": source_commit},
    )
    atom_id = f"ATOM-V2-{sem_id[:16]}"
    return {
        "ATOM_ID": atom_id,
        "SEMANTIC_ID": sem_id,
        "CONTENT_ID": cid,
        "OCCURRENCE_ID": occ,
        "ATOM_TYPE": atom_type,
        "schema_version": ATOM_V2_SCHEMA,
        "domain_separator": ATOM_V2_DOMAIN,
        "subject": subject,
        "predicate": predicate,
        "object": obj,
        "qualifiers": qualifiers or [],
        "negations": negations or [],
        "quantifiers": [],
        "temporal_scope": None,
        "SOURCE_OCCURRENCE_IDS": [source_occurrence_id],
        "STRUCTURAL_OBJECT_IDS": [structural_object_id],
        "SEEDGRAPH_MERKLE_ATOM_V1": legacy_merkle_v1_ref,
        "proof_state": proof_state,
        "admission_state": admission_state,
        "claim_ceiling": claim_ceiling,
        "source_text_excerpt": source_text[:160],
    }


def proposition_from_sentence(sentence: dict[str, Any]) -> list[dict[str, Any]]:
    text = sentence.get("exact_text", "")
    atoms = []
    # Primary proposition
    atoms.append(
        build_atom_v2(
            atom_type="PROPOSITION",
            subject="manuscript",
            predicate="states",
            obj=text[:240],
            source_text=text,
            structural_object_id=sentence["object_id"],
            source_occurrence_id=sentence["OCCURRENCE_ID"],
            source_file=sentence.get("source_file", ""),
            source_commit=sentence.get("source_commit", ""),
            admission_state="CHALLENGE" if sentence.get("citation_keys") else "ACCEPT",
        )
    )
    # Negation boundary atom for explicit disclaimers
    if re.search(r"\bdo not claim\b|\bnot establish\b|\bnot executed\b", text, re.I):
        atoms.append(
            build_atom_v2(
                atom_type="BOUNDARY",
                subject="manuscript",
                predicate="limits_claim",
                obj=text[:160],
                source_text=text,
                structural_object_id=sentence["object_id"],
                source_occurrence_id=sentence["OCCURRENCE_ID"],
                source_file=sentence.get("source_file", ""),
                source_commit=sentence.get("source_commit", ""),
                admission_state="ACCEPT",
                claim_ceiling="NOT_ESTABLISHED",
            )
        )
    return atoms
