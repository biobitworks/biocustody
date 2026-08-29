"""Canonical lattice ↔ SeedGraph atom identity bridge (no fuzzy proof)."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

NORMALIZATION_RULESET_SHA = "document_lattice_text_normalize_v1"


def normalize_manuscript_text(text: str) -> str:
    """Frozen normalization ruleset for cross-path text identity."""
    s = unicodedata.normalize("NFKC", text)
    s = re.sub(r"\\(?:cite|ref|emph|textsc|texttt)\{[^}]*\}", " ", s)
    s = re.sub(r"\\[a-zA-Z]+\*?", " ", s)
    s = re.sub(r"[{}$]", " ", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def strip_pdf_line_numbers(text: str) -> str:
    """Remove leading line-number prefixes from PDF-extracted sentences."""
    s = re.sub(r"^\d+\s+", "", text.strip())
    s = re.sub(r"\n\d+\s+", " ", s)
    return normalize_manuscript_text(s)


def build_canonical_bridge(
    lattice_sentences: list[dict],
    pdf_sentence_map: list[dict],
    discovery_bridge: list[dict] | None = None,
) -> tuple[list[dict], dict]:
    """Match lattice sentences to PDF atoms by exact normalized text or CONTENT_ID."""
    pdf_by_norm: dict[str, list[dict]] = {}
    for row in pdf_sentence_map:
        norm = strip_pdf_line_numbers(row.get("text", ""))
        if norm:
            pdf_by_norm.setdefault(norm, []).append(row)

    discovery_by_lattice = {r["lattice_object_id"]: r for r in (discovery_bridge or [])}
    rows: list[dict] = []
    terminals: dict[str, int] = {}

    for sent in lattice_sentences:
        oid = sent["object_id"]
        exact_norm = normalize_manuscript_text(sent.get("exact_text", ""))
        cid = sent.get("CONTENT_ID")
        terminal = "NOT_FOUND"
        atom_seed_id = None
        match_method = None

        if exact_norm in pdf_by_norm:
            cands = pdf_by_norm[exact_norm]
            if len(cands) == 1:
                terminal = "NORMALIZED_IDENTITY"
                atom_seed_id = cands[0]["sentence_id"]
                match_method = "normalized_text_exact"
            else:
                terminal = "AMBIGUOUS"
                match_method = "normalized_text_multiple"
        elif sent.get("source_span"):
            terminal = "SOURCE_LOCATION_IDENTITY"
            match_method = "lattice_source_span_only"
            disc = discovery_by_lattice.get(oid)
            if disc and disc.get("linked"):
                atom_seed_id = disc.get("atom_seed_id")
                terminal = "EXACT_IDENTITY" if disc.get("match_score", 0) >= 0.99 else "NORMALIZED_IDENTITY"

        terminals[terminal] = terminals.get(terminal, 0) + 1
        rows.append(
            {
                "lattice_object_id": oid,
                "lattice_CONTENT_ID": cid,
                "atom_seed_id": atom_seed_id,
                "match_method": match_method,
                "terminal": terminal,
                "bridge_class": "CANONICAL_IDENTITY",
                "discovery_bridge_preserved": oid in discovery_by_lattice,
            }
        )

    receipt = {
        "bridge_class": "CANONICAL_IDENTITY",
        "normalization_ruleset_sha": NORMALIZATION_RULESET_SHA,
        "terminals": terminals,
        "total": len(rows),
        "discovery_bridge_class": "DISCOVERY_BRIDGE",
        "note": "Fuzzy match_score bridge preserved separately; not used for proof",
    }
    return rows, receipt
