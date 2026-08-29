"""AUD-FCG-DOCUMENT-LATTICE-001 invariant tests."""

from __future__ import annotations

import json
from pathlib import Path

AUDIT = Path(__file__).resolve().parents[2] / "audits" / "AUD-FCG-DOCUMENT-LATTICE-001"


def test_source_git_manifest_frozen_commit():
    manifest = json.loads((AUDIT / "SOURCE_GIT_MANIFEST.json").read_text())
    assert manifest["source_commit"] == "4a372a5c459ad60cd23b850709011cbfd0e516b4"
    assert manifest["sealed_pdf_mutation"] == "FORBIDDEN"


def test_pre_ingest_root_has_objects():
    root = json.loads((AUDIT / "PRE_INGEST" / "PRE_INGEST_ROOT.json").read_text())
    assert root["object_counts"]["sentences"] >= 20
    assert root["object_counts"]["sections"] >= 8


def test_roundtrip_gate_pass():
    rt = json.loads((AUDIT / "FCG_PRE_POST_ROUNDTRIP.json").read_text())
    assert rt["mismatch"] == 0
    assert rt["identical"] == rt["total_pre"]


def test_document_closure_not_full_pass():
    receipt = json.loads((AUDIT / "AUDIT_RECEIPT.json").read_text())
    assert receipt["document_closure"]["FULL_MANUSCRIPT_SEMANTIC_CLOSURE"] == "NOT_ESTABLISHED"
    assert receipt["document_closure"]["CITATION_PATH_CLOSURE"] == "6_OF_6_SUPPORTED_BOUNDED"


def test_proof_domains_separated():
    receipt = json.loads((AUDIT / "AUDIT_RECEIPT.json").read_text())
    matrix = receipt["proof_domain_matrix"]
    sg = matrix["SEEDGRAPH_OBJECT_PROOF"]
    assert sg.get("verified", 0) + sg.get("pending", 0) > 0
    assert any(r["proof_state"] == "VERIFIED_USABLE" for r in matrix["CAPABILITY_AUTH_PROOF"])


def test_non_citation_closure_terminal():
    receipt_path = AUDIT.parent / "TEMPORAL_CONTROL_PLANE" / "PROJECT_DOCUMENT_001_NON_CITATION_CLOSURE_RECEIPT.json"
    if not receipt_path.is_file():
        return
    receipt = json.loads(receipt_path.read_text())
    assert receipt["non_citation_sentences"] == 18
    assert receipt["NON_CITATION_TERMINAL_CLOSURE"] == "PASS"


def test_seedgraph_live_import_receipt_when_present():
    receipt_path = AUDIT / "SEEDGRAPH_LIVE_IMPORT_RECEIPT.json"
    if not receipt_path.is_file():
        return
    receipt = json.loads(receipt_path.read_text())
    assert receipt["production_neo4j_touched"] is False
    assert receipt["objects_imported"] == 136
    assert receipt["contract_mismatches"] == 0
