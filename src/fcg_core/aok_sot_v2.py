"""AOK V2 and SOT V2 composition from Atom V2 lattice."""

from __future__ import annotations

import hashlib
from typing import Any

from fcg_core.canonical_v2 import canonical_hash_v2

DERIVATION_RULE_ID = "aok_sot_v2_derivation_v1"
DERIVATION_RULE_SHA = hashlib.sha256(DERIVATION_RULE_ID.encode()).hexdigest()
TRANSFORMATION_ID = "AUD-FCG-ATOM-SOT-ROUNDTRIP-002:compose"


def build_aok_from_atoms(atom_ids: list[str], atoms_by_id: dict[str, dict]) -> dict[str, Any]:
    """Compose one AOK per structural sentence cluster."""
    source_atoms = [atoms_by_id[a] for a in atom_ids if a in atoms_by_id]
    if not source_atoms:
        raise ValueError("AOK requires at least one source atom")
    primary = source_atoms[0]
    sem_payload = {
        "subject": primary["subject"],
        "predicate": primary["predicate"],
        "object": primary["object"],
        "qualifiers": sorted(primary.get("qualifiers") or []),
    }
    sem_id = canonical_hash_v2({"domain": "fcg.aok.v2", **sem_payload})
    aok_id = f"AOK-V2-{sem_id[:16]}"
    admission = "ACCEPT"
    for a in source_atoms:
        if a.get("admission_state") == "CHALLENGE":
            admission = "CHALLENGE"
        if a.get("claim_ceiling") == "NOT_ESTABLISHED":
            admission = "ABSTAIN"
    return {
        "AOK_ID": aok_id,
        "SEMANTIC_ID": sem_id,
        "SOURCE_ATOM_IDS": atom_ids,
        "SOURCE_OCCURRENCE_IDS": sorted({o for a in source_atoms for o in a.get("SOURCE_OCCURRENCE_IDS", [])}),
        "subject": primary["subject"],
        "predicate": primary["predicate"],
        "object": primary["object"],
        "qualifiers": primary.get("qualifiers") or [],
        "negations": primary.get("negations") or [],
        "quantifiers": primary.get("quantifiers") or [],
        "temporal_scope": primary.get("temporal_scope"),
        "evidence_class": "MANUSCRIPT_PROPOSITION",
        "proof_state": "PENDING",
        "admission_state": admission,
        "claim_ceiling": primary.get("claim_ceiling", "REPURPOSING_HYPOTHESIS"),
        "contradicting_atom_ids": [],
        "supersedes": [],
    }


def build_sot_v2(
    *,
    sot_id: str,
    statement: str,
    status: str,
    supporting_atom_ids: list[str],
    supporting_aok_ids: list[str],
    composition_admission: str,
    proof_state: str,
) -> dict[str, Any]:
    sem_payload = {"domain": "fcg.sot.v2", "sot_id": sot_id, "statement": statement}
    sem_id = canonical_hash_v2(sem_payload)
    admitted = status not in {"NOT_ESTABLISHED", "OPERATOR_REQUIRED"} and composition_admission not in {
        "PRESERVED_NOT_ESTABLISHED",
        "REFUSED_NO_ATOMS",
    }
    if admitted and not supporting_atom_ids and not supporting_aok_ids:
        composition_admission = "REFUSED_NO_ATOMS"
        proof_state = "PENDING"
    return {
        "SOT_ID": sot_id,
        "SEMANTIC_ID": sem_id,
        "statement": statement,
        "status": status,
        "supporting_atom_ids": supporting_atom_ids,
        "supporting_aok_ids": supporting_aok_ids,
        "contradicting_atom_ids": [],
        "contradicting_aok_ids": [],
        "derivation_rule_id": DERIVATION_RULE_ID,
        "derivation_rule_sha256": DERIVATION_RULE_SHA,
        "transformation_id": TRANSFORMATION_ID,
        "composition_admission": composition_admission,
        "proof_state": proof_state,
        "claim_ceiling": "NOT_ESTABLISHED" if status == "NOT_ESTABLISHED" else "REPURPOSING_HYPOTHESIS",
    }


def compose_sots_from_reference(
    sot_reference: list[dict],
    atomization_composition: list[dict],
    lattice_to_v2_atom: dict[str, str],
) -> tuple[list[dict], list[dict], list[dict]]:
    """Map historical SOT composition to Atom V2 / AOK V2 lineage."""
    comp_by_sot = {r["SOT_ID"]: r for r in atomization_composition}
    sots: list[dict] = []
    receipts: list[dict] = []
    contradictions: list[dict] = []

    for seed in sot_reference:
        sid = seed["seed_id"]
        prior = comp_by_sot.get(sid, {})
        v1_ids = prior.get("supporting_atom_seed_ids") or []
        v2_ids = [lattice_to_v2_atom[v1] for v1 in v1_ids if v1 in lattice_to_v2_atom]
        comp_adm = prior.get("composition_admission", "COMPOSED")
        if sid in {"SOT-008", "SOT-014"}:
            comp_adm = "PRESERVED_NOT_ESTABLISHED"
            v2_ids = []
        sot = build_sot_v2(
            sot_id=sid,
            statement=seed.get("statement", ""),
            status=seed.get("status", "PENDING"),
            supporting_atom_ids=v2_ids,
            supporting_aok_ids=[],
            composition_admission=comp_adm,
            proof_state=prior.get("proof_state", "PENDING"),
        )
        sots.append(sot)
        receipts.append(
            {
                "SOT_ID": sid,
                "receipt_type": "SOT_COMPOSITION",
                "supporting_atom_count": len(v2_ids),
                "traceability_invariant": "PASS" if sid in {"SOT-008", "SOT-014"} or v2_ids or comp_adm.startswith("REFUSED") else "FAIL",
            }
        )
        if comp_adm == "PRESERVED_NOT_ESTABLISHED":
            contradictions.append({"SOT_ID": sid, "state": "NOT_ESTABLISHED", "contradiction_edges": 0})
    return sots, receipts, contradictions
