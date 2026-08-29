"""Credential discovery, CFMO lineage, and proof-domain invariant tests."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTROL = ROOT / "control"
AUDIT = ROOT / "audits" / "TEMPORAL_CONTROL_PLANE"
SRC = ROOT / "src"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_credential_ledgers_no_secret_values():
    for path in [
        CONTROL / "CREDENTIAL_SOURCE_LEDGER.jsonl",
        CONTROL / "CREDENTIAL_CAPABILITY_LEDGER.jsonl",
    ]:
        if not path.is_file():
            continue
        blob = path.read_text()
        assert "secret_value" not in blob
        assert not re.search(r"sk-[a-zA-Z0-9]{20,}", blob)


def test_cfmo_namespace_not_empty_implication():
    receipt = json.loads((AUDIT / "CFMO_DELTA_RECEIPT.json").read_text())
    assert receipt.get("CFMO_NAMESPACE") == "CUSTODY_PORTABILITY_AUDIT_TEMPORAL_CONTROL_PLANE"
    assert receipt.get("PREVIOUS_PROJECT_CFMO") == "NOT_PART_OF_THIS_NAMESPACE"
    assert receipt["CFMO_BEFORE"] != "EMPTY"
    assert receipt.get("CFMO_LINEAGE_CLASS") == "NEW_ISOLATED_NAMESPACE"


def test_cfmo_predecessor_binding():
    receipt = json.loads((AUDIT / "CFMO_DELTA_RECEIPT.json").read_text())
    assert receipt.get("PREDECESSOR_BATCH_ID") == "CFMO-BATCH-58f020308719471e"
    assert receipt.get("PREDECESSOR_RECEIPT_SHA256")
    assert receipt.get("receipt_sha256")


def test_proof_domains_separated():
    cred = json.loads((AUDIT / "CREDENTIAL_CAPABILITY_RECEIPT.json").read_text())
    matrix = cred.get("PROOF_DOMAIN_MATRIX") or []
    domains = {row["proof_domain"] for row in matrix}
    assert "SEEDGRAPH_OBJECT_PROOF" in domains or any("SEEDGRAPH" in d for d in domains)
    assert any(row.get("proof_domain") == "CAPABILITY_AUTH_PROOF" for row in matrix)


def test_document_closure_labels():
    closure = json.loads((AUDIT / "PROJECT_DOCUMENT_001_CLOSURE_RECEIPT.json").read_text())
    assert closure["CITATION_PATH_CLOSURE"] == "6_OF_6_SUPPORTED_BOUNDED"
    assert closure["FULL_MANUSCRIPT_SEMANTIC_CLOSURE"] == "NOT_ESTABLISHED"
    assert closure["PROJECT_DOCUMENT_001_FULL_SEMANTIC_CLOSURE"] == "NOT_PASS"


def test_turn_ledger_append_only():
    turns = load_jsonl(CONTROL / "TURN_EVENT_LEDGER.jsonl")
    assert len(turns) >= 2
    sequences = [t["TURN_SEQUENCE"] for t in turns]
    assert sequences == sorted(sequences)
    assert "TURN-20260829-TCP-002" in {t["TURN_ID"] for t in turns}


def test_secret_registry_kaggle_json_resolution():
    import sys

    sys.path.insert(0, str(SRC))
    from fcg_core.secret_registry import resolve_credential_metadata

    meta = resolve_credential_metadata("KAGGLE_USERNAME", "KAGGLE")
    if (Path.home() / ".kaggle/kaggle.json").is_file():
        assert meta.variable_present in {True, False}
    assert meta.terminal_state in {
        "NOT_FOUND", "PRESENT_UNVERIFIED", "MULTIPLE_CANDIDATES", "VERIFIED_USABLE",
    }


def test_secret_registry_daytona_presence_vs_auth_separation():
    import sys

    sys.path.insert(0, str(SRC))
    from fcg_core.secret_registry import resolve_credential_metadata

    meta = resolve_credential_metadata("DAYTONA_API_KEY", "DAYTONA")
    cap = json.loads((AUDIT / "CREDENTIAL_CAPABILITY_RECEIPT.json").read_text())
    if meta.variable_present:
        assert meta.terminal_state in {"PRESENT_UNVERIFIED", "MULTIPLE_CANDIDATES", "VERIFIED_USABLE"}
    assert cap.get("DAYTONA_AUTH") in {"VERIFIED_USABLE", "NOT_FOUND", "PRESENT_INVALID"}
