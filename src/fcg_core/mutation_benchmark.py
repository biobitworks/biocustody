"""Deterministic mutation families for pipeline benchmark."""

from __future__ import annotations

import copy
import hashlib
from typing import Any, Callable

MutationFn = Callable[[dict[str, Any]], tuple[dict[str, Any], dict[str, Any]]]


def _mid(prefix: str, base_id: str, family: str, idx: int) -> str:
    h = hashlib.sha256(f"{prefix}:{base_id}:{family}:{idx}".encode()).hexdigest()[:12]
    return f"{prefix}-{h}"


def mutate_whitespace_synonymous(obj: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    m = copy.deepcopy(obj)
    if "exact_text" in m:
        m["exact_text"] = m["exact_text"].replace(" ", "  ", 1)
    gt = {
        "expected_content_changed": True,
        "expected_semantic_changed": False,
        "expected_occurrence_changed": True,
        "expected_structure_changed": False,
        "expected_provenance_changed": False,
        "expected_contradiction_changed": False,
        "expected_terminal": "BENIGN_INVARIANCE",
    }
    return m, gt


def mutate_doi_presentation_synonymous() -> tuple[dict[str, Any], dict[str, Any]]:
    obj = {"presentation": "doi:10.1038/s41586-019-1799-4", "identifier_type": "DOI"}
    m = {"presentation": "https://doi.org/10.1038/s41586-019-1799-4", "identifier_type": "DOI"}
    gt = {
        "expected_content_changed": True,
        "expected_semantic_changed": False,
        "expected_occurrence_changed": True,
        "expected_structure_changed": False,
        "expected_provenance_changed": False,
        "expected_contradiction_changed": False,
        "expected_terminal": "BENIGN_INVARIANCE",
    }
    return m, gt


def mutate_substitution_numeric(obj: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    m = copy.deepcopy(obj)
    if "exact_value" in m:
        m["exact_value"] = str(int(str(m.get("exact_value", "0")).split()[0] or "0") + 1)
    elif "exact_text" in m:
        m["exact_text"] = m["exact_text"].replace("three", "four").replace("N{=}1", "N{=}2")
    gt = {
        "expected_content_changed": True,
        "expected_semantic_changed": True,
        "expected_occurrence_changed": True,
        "expected_structure_changed": False,
        "expected_provenance_changed": False,
        "expected_contradiction_changed": False,
        "expected_terminal": "SEMANTIC_CHANGE",
    }
    return m, gt


def mutate_insertion_unsupported_claim(obj: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    m = copy.deepcopy(obj)
    m["exact_text"] = (m.get("exact_text") or "") + " Therefore therapeutic efficacy is established."
    gt = {
        "expected_content_changed": True,
        "expected_semantic_changed": True,
        "expected_occurrence_changed": True,
        "expected_structure_changed": False,
        "expected_provenance_changed": False,
        "expected_contradiction_changed": False,
        "expected_terminal": "UNSUPPORTED_CLAIM",
        "expected_claim_ceiling_delta": "ELEVATED",
    }
    return m, gt


def mutate_deletion_evidence_edge(ctx: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    m = copy.deepcopy(ctx)
    m["supporting_atom_ids"] = []
    m["supporting_aok_ids"] = []
    gt = {
        "expected_content_changed": True,
        "expected_semantic_changed": True,
        "expected_occurrence_changed": False,
        "expected_structure_changed": False,
        "expected_provenance_changed": True,
        "expected_contradiction_changed": False,
        "expected_terminal": "PROVENANCE_BREAK",
    }
    return m, gt


def mutate_duplication_reingest(obj: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    m = copy.deepcopy(obj)
    m["reingest_alias"] = True
    gt = {
        "expected_content_changed": False,
        "expected_semantic_changed": False,
        "expected_occurrence_changed": True,
        "expected_structure_changed": False,
        "expected_provenance_changed": False,
        "expected_contradiction_changed": False,
        "expected_terminal": "DUPLICATE_ALIAS",
    }
    return m, gt


def mutate_transposition_parent(obj: dict[str, Any], wrong_parent: str) -> tuple[dict[str, Any], dict[str, Any]]:
    m = copy.deepcopy(obj)
    m["parent_id"] = wrong_parent
    gt = {
        "expected_content_changed": False,
        "expected_semantic_changed": False,
        "expected_occurrence_changed": False,
        "expected_structure_changed": True,
        "expected_provenance_changed": False,
        "expected_contradiction_changed": False,
        "expected_terminal": "STRUCTURE_CHANGE",
    }
    return m, gt


def mutate_gain_of_function_verify(obj: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    m = copy.deepcopy(obj)
    m["proof_state"] = "VERIFIED"
    m["admission_state"] = "ACCEPT"
    gt = {
        "expected_content_changed": True,
        "expected_semantic_changed": True,
        "expected_occurrence_changed": False,
        "expected_structure_changed": False,
        "expected_provenance_changed": True,
        "expected_contradiction_changed": False,
        "expected_terminal": "FALSE_VERIFICATION",
    }
    return m, gt


def mutate_contradiction_insert(ctx: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    m = copy.deepcopy(ctx)
    m["contradicting_atom_ids"] = m.get("contradicting_atom_ids", []) + ["ATOM-V2-contradiction-injected"]
    gt = {
        "expected_content_changed": True,
        "expected_semantic_changed": True,
        "expected_occurrence_changed": False,
        "expected_structure_changed": False,
        "expected_provenance_changed": False,
        "expected_contradiction_changed": True,
        "expected_terminal": "CONTRADICTION_CHANGE",
    }
    return m, gt


def mutate_provenance_wrong_commit(obj: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    m = copy.deepcopy(obj)
    m["source_commit"] = "0" * 40
    gt = {
        "expected_content_changed": True,
        "expected_semantic_changed": False,
        "expected_occurrence_changed": True,
        "expected_structure_changed": False,
        "expected_provenance_changed": True,
        "expected_contradiction_changed": False,
        "expected_terminal": "PROVENANCE_BREAK",
    }
    return m, gt


def mutate_table_cell_value(cell: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    m = copy.deepcopy(cell)
    m["exact_value"] = "999"
    m["display_value"] = "999"
    gt = {
        "expected_content_changed": True,
        "expected_semantic_changed": True,
        "expected_occurrence_changed": True,
        "expected_structure_changed": False,
        "expected_provenance_changed": False,
        "expected_contradiction_changed": False,
        "expected_terminal": "SEMANTIC_CHANGE",
    }
    return m, gt


def mutate_attestation_wrong_key(manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    m = copy.deepcopy(manifest)
    m["attestation_key_fingerprint"] = "wrong-key-fingerprint"
    gt = {
        "expected_content_changed": True,
        "expected_semantic_changed": False,
        "expected_occurrence_changed": True,
        "expected_structure_changed": False,
        "expected_provenance_changed": True,
        "expected_contradiction_changed": False,
        "expected_terminal": "ATTESTATION_MUTATION",
    }
    return m, gt


def generate_mutation_manifest(
    sentences: list[dict],
    table_cells: list[dict],
    sot_ctx: dict[str, dict],
    wrong_parent: str,
) -> list[dict[str, Any]]:
    """Build preregistered mutation cases with ground truth from generator."""
    rows: list[dict[str, Any]] = []
    idx = 0

    def add(family: str, base: dict, base_type: str, operator: str, fn: Callable[..., tuple], *args: Any) -> None:
        nonlocal idx
        idx += 1
        mutated, gt = fn(*args) if args else fn(base)
        mid = _mid("MUT", base.get("object_id") or base.get("SOT_ID") or "ctx", family, idx)
        rows.append(
            {
                "MUTATION_ID": mid,
                "MUTATION_FAMILY": family,
                "CLUSTER_ID": base.get("object_id") or base.get("SOT_ID") or mid,
                "BASE_OBJECT_ID": base.get("object_id") or base.get("SOT_ID"),
                "BASE_OBJECT_TYPE": base_type,
                "MUTATION_OPERATOR": operator,
                "mutated_payload": mutated,
                **gt,
                "expected_affected_SOT_ids": [base.get("SOT_ID")] if base_type == "SOT" else [],
            }
        )

    if sentences:
        s0, s1, s2, s3 = sentences[0], sentences[1], sentences[2], sentences[3]
        add("synonymous", s0, "Sentence", "whitespace", mutate_whitespace_synonymous, s0)
        add("substitution", s1, "Sentence", "numeric_term", mutate_substitution_numeric, s1)
        add("insertion", s2, "Sentence", "unsupported_qualifier", mutate_insertion_unsupported_claim, s2)
        add("duplication", s3, "Sentence", "reingest_alias", mutate_duplication_reingest, s3)
        if len(sentences) > 4:
            add("transposition", sentences[4], "Sentence", "wrong_parent", mutate_transposition_parent, sentences[4], wrong_parent)
        if len(sentences) > 5:
            add("gain-of-function", sentences[5], "Atom", "pending_to_verified", mutate_gain_of_function_verify, sentences[5])
        if len(sentences) > 6:
            add("provenance", sentences[6], "Sentence", "wrong_git_commit", mutate_provenance_wrong_commit, sentences[6])

    add("synonymous", {"presentation": "doi:10.1038/s41586-019-1799-4"}, "Identifier", "doi_presentation", mutate_doi_presentation_synonymous)

    if table_cells:
        add("table/figure", table_cells[0], "TableCell", "cell_value", mutate_table_cell_value, table_cells[0])

    sot_keys = list(sot_ctx.keys())
    if sot_keys:
        sk = sot_keys[0]
        add("deletion", sot_ctx[sk], "SOT", "remove_support_edges", mutate_deletion_evidence_edge, sot_ctx[sk])
        add("contradiction", sot_ctx[sk], "SOT", "inject_contradiction", mutate_contradiction_insert, sot_ctx[sk])

    add("attestation", {"attestation_key_fingerprint": "valid"}, "Manifest", "wrong_signing_key", mutate_attestation_wrong_key, {"attestation_key_fingerprint": "valid"})

    # Recombination: attach wrong citation to proposition (simulated)
    if len(sentences) > 7:
        s = copy.deepcopy(sentences[7])
        s["citation_keys"] = ["nonexistent_bib_key_xyz"]
        rows.append(
            {
                "MUTATION_ID": _mid("MUT", s["object_id"], "recombination", 99),
                "MUTATION_FAMILY": "recombination",
                "CLUSTER_ID": s["object_id"],
                "BASE_OBJECT_ID": s["object_id"],
                "BASE_OBJECT_TYPE": "Sentence",
                "MUTATION_OPERATOR": "wrong_citation_attachment",
                "mutated_payload": s,
                "expected_content_changed": True,
                "expected_semantic_changed": True,
                "expected_occurrence_changed": True,
                "expected_structure_changed": False,
                "expected_provenance_changed": True,
                "expected_contradiction_changed": False,
                "expected_terminal": "AUTHORITY_BREAK",
            }
        )

    return rows
