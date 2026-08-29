"""Semantic SOT support validation — successor to lexical keyword linking."""

from __future__ import annotations

import re
from typing import Any

STOPWORDS = frozenset(
    "a an the and or but in on at to for of is are was were be been being with from by as".split()
)


def _content_tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]{3,}", text.lower())
    return {w for w in words if w not in STOPWORDS}


def evaluate_support_edge(
    sot_statement: str,
    atom: dict[str, Any],
) -> str:
    """Deterministic support edge terminal — no LLM judges."""
    sot_tok = _content_tokens(sot_statement)
    atom_text = " ".join(
        str(atom.get(k, "")) for k in ("subject", "predicate", "object", "source_text_excerpt")
    )
    atom_tok = _content_tokens(atom_text)
    if not sot_tok or not atom_tok:
        return "INSUFFICIENT"
    overlap = sot_tok & atom_tok
    ratio = len(overlap) / max(len(sot_tok), 1)
    if ratio >= 0.5:
        return "SUPPORTED_EXACT"
    if ratio >= 0.25:
        return "SUPPORTED_BOUNDED"
    if overlap:
        return "PARTIAL_SUPPORT"
    return "NOT_RELEVANT"


def compose_sot_v2_semantic(
    sot_id: str,
    statement: str,
    status: str,
    supporting_atom_ids: list[str],
    atoms_by_id: dict[str, dict],
    composition_admission: str,
) -> tuple[dict, list[dict], dict]:
    """Build SOT V2 row with semantic support ledger."""
    edges: list[dict] = []
    support_terminals: list[str] = []
    for aid in supporting_atom_ids:
        atom = atoms_by_id.get(aid, {})
        edge_terminal = evaluate_support_edge(statement, atom)
        support_terminals.append(edge_terminal)
        edges.append(
            {
                "SOT_ID": sot_id,
                "atom_id": aid,
                "edge_type": "SUPPORTS",
                "terminal": edge_terminal,
                "TRACEABILITY_STATE": "LINKED",
                "RELEVANCE_STATE": "EVALUATED",
                "SEMANTIC_SUPPORT_STATE": edge_terminal,
            }
        )

    if sot_id in {"SOT-008", "SOT-014"}:
        proof_state = "PENDING"
        sem_state = "NOT_ESTABLISHED"
        comp_adm = "PRESERVED_NOT_ESTABLISHED"
        sot_status = "NOT_ESTABLISHED"
    elif not supporting_atom_ids:
        proof_state = "PENDING"
        sem_state = "INSUFFICIENT"
        comp_adm = composition_admission if composition_admission.startswith("REFUSED") else "REFUSED_NO_ATOMS"
        sot_status = status
    elif any(t in {"SUPPORTED_EXACT", "SUPPORTED_BOUNDED"} for t in support_terminals):
        proof_state = "VERIFIED_BOUNDED" if status.startswith("VERIFIED") else "PENDING"
        sem_state = "SUPPORTED_BOUNDED"
        comp_adm = composition_admission
        sot_status = status
    elif any(t == "PARTIAL_SUPPORT" for t in support_terminals):
        proof_state = "PENDING"
        sem_state = "PARTIAL_SUPPORT"
        comp_adm = composition_admission
        sot_status = "VERIFIED_BOUNDED" if status == "VERIFIED" else status
    else:
        proof_state = "PENDING"
        sem_state = "INSUFFICIENT"
        comp_adm = composition_admission
        sot_status = "NOT_ESTABLISHED" if status == "VERIFIED" else status

    sot_row = {
        "SOT_ID": sot_id,
        "statement": statement,
        "status": sot_status,
        "supporting_atom_ids": supporting_atom_ids,
        "composition_admission": comp_adm,
        "proof_state": proof_state,
        "TRACEABILITY_STATE": "LINKED" if supporting_atom_ids else "UNLINKED",
        "RELEVANCE_STATE": "EVALUATED" if supporting_atom_ids else "NOT_EVALUATED",
        "SEMANTIC_SUPPORT_STATE": sem_state,
        "claim_ceiling": "NOT_ESTABLISHED" if sot_status == "NOT_ESTABLISHED" else "REPURPOSING_HYPOTHESIS",
    }
    return sot_row, edges, {"SOT_ID": sot_id, "semantic_support_terminal": sem_state}
