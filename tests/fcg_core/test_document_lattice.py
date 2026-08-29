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
    assert matrix["SEEDGRAPH_OBJECT_PROOF"]["pending"] > 0
    assert any(r["proof_state"] == "VERIFIED_USABLE" for r in matrix["CAPABILITY_AUTH_PROOF"])
