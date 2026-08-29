#!/usr/bin/env python3
"""Repair CFMO lineage — isolated namespace with explicit predecessor binding."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audits" / "TEMPORAL_CONTROL_PLANE"
CONTROL = ROOT / "control"
HYDRADG_EXEC = Path("/Users/byron/projects/active/hydradg/eval/newinml_final_daisy_20260829/execution/lane6_seedgraph")

CFMO_NAMESPACE = "CUSTODY_PORTABILITY_AUDIT_TEMPORAL_CONTROL_PLANE"
GENESIS_BATCH = "CFMO-BATCH-58f020308719471e"
SUPERSEDED_BATCHES = [
    {"batch_id": GENESIS_BATCH, "defect": "CFMO_BEFORE=EMPTY without namespace fields"},
    {"batch_id": "CFMO-BATCH-76fef2ed0cafce1b", "defect": "duplicate regeneration without lineage repair"},
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_json(obj: dict) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text())


def external_cfmo_references() -> list[dict[str, str]]:
    refs = []
    for name in ["BATCH003_CFMO_UPDATE.json", "BATCH004_CFMO_UPDATE.json", "BATCH_CFMO_UPDATE.json"]:
        p = HYDRADG_EXEC / name
        if p.is_file():
            refs.append({"repo": "hydradg", "path": str(p), "content_id": sha256_file(p), "in_namespace": "false"})
    return refs


def proof_domain_matrix(cred: dict) -> list[dict]:
    return [
        {
            "proof_domain": "SEEDGRAPH_OBJECT_PROOF",
            "proof_subject": "custody_portability_import_objects",
            "proof_state": "PENDING",
            "verified_count": 0,
            "pending_count": 21,
        },
        {
            "proof_domain": "CAPABILITY_AUTH_PROOF",
            "proof_subject": "DAYTONA_API",
            "proof_state": cred.get("DAYTONA_AUTH", "UNKNOWN"),
        },
        {
            "proof_domain": "CAPABILITY_AUTH_PROOF",
            "proof_subject": "KAGGLE_API",
            "proof_state": cred.get("KAGGLE_AUTH", "UNKNOWN"),
        },
        {
            "proof_domain": "CAPABILITY_AUTH_PROOF",
            "proof_subject": "MISTRAL_API",
            "proof_state": cred.get("MISTRAL_AUTH", "NOT_FOUND"),
        },
    ]


def build_corrected_receipt() -> dict[str, Any]:
    cred = load_json(AUDIT / "CREDENTIAL_CAPABILITY_RECEIPT.json") or {}
    closure = load_json(AUDIT / "PROJECT_DOCUMENT_001_CLOSURE_RECEIPT.json") or {}
    anticube = read_jsonl(CONTROL / "ANTICUBE_CLASSIFICATION_RECEIPTS.jsonl")
    aoks = read_jsonl(AUDIT / "CAPABILITY_AOK_DELTA.jsonl") + read_jsonl(AUDIT / "AOK_LEDGER.jsonl")
    aok_ids = sorted({r.get("AOK_ID") for r in aoks if r.get("AOK_ID")})
    sot_ids = sorted({r.get("SOT_ID") for r in read_jsonl(AUDIT / "SOT_LEDGER.jsonl") if r.get("SOT_ID")})

    new_sources = []
    for p in [
        AUDIT / "CREDENTIAL_CAPABILITY_RECEIPT.json",
        CONTROL / "CREDENTIAL_DISCOVERY_RECEIPT.json",
        AUDIT / "PROJECT_DOCUMENT_001_CLOSURE_RECEIPT.json",
    ]:
        if p.is_file():
            new_sources.append({"path": str(p), "content_id": sha256_file(p), "secret_bytes": 0})

    genesis_receipt_sha = None
    history = read_jsonl(AUDIT / "CFMO_DELTA_RECEIPT.history.jsonl")
    for row in history:
        if row.get("batch_id") == GENESIS_BATCH or row.get("CFMO_AFTER") == GENESIS_BATCH:
            genesis_receipt_sha = sha256_json(row)
            break
    if not genesis_receipt_sha:
        genesis_receipt_sha = "UNAVAILABLE_PRE_ARCHIVE"

    body_for_id = {
        "wave": "CFMO_LINEAGE_REPAIR_20260829",
        "namespace": CFMO_NAMESPACE,
        "genesis_batch": GENESIS_BATCH,
        "aok_ids": aok_ids,
    }
    batch_id = f"CFMO-BATCH-{hashlib.sha256(json.dumps(body_for_id, sort_keys=True).encode()).hexdigest()[:16]}"

    receipt: dict[str, Any] = {
        "schema": "biocustody.cfmo_delta_receipt.v2",
        "batch_id": batch_id,
        "recorded_at_utc": utc_now(),
        "CFMO_LINEAGE_CLASS": "NEW_ISOLATED_NAMESPACE",
        "CFMO_NAMESPACE": CFMO_NAMESPACE,
        "CFMO_INITIALIZATION": "NEW_ISOLATED_NAMESPACE",
        "PREVIOUS_PROJECT_CFMO": "NOT_PART_OF_THIS_NAMESPACE",
        "EXTERNAL_CFMO_REFERENCES": external_cfmo_references(),
        "CFMO_BEFORE": "CFMO-NAMESPACE-ROOT",
        "CFMO_AFTER": batch_id,
        "PREDECESSOR_BATCH_ID": GENESIS_BATCH,
        "PREDECESSOR_RECEIPT_SHA256": genesis_receipt_sha,
        "PREDECESSOR_SHA256_NOTE": "SHA-256 of archived genesis receipt object, not MMR root",
        "SUPERSEDED_RECEIPTS": SUPERSEDED_BATCHES,
        "NEW_SOURCE_SET": new_sources,
        "NEW_AOK_SET": aok_ids,
        "NEW_SOT_SET": sot_ids,
        "NEW_GRAPH_EDGES": [
            {"from": "CREDENTIAL_CAPABILITY_RECEIPT", "to": aid, "edge": "capability_probe"}
            for aid in aok_ids
            if aid.startswith("AOK-CAP-")
        ],
        "PROOF_DOMAIN_MATRIX": proof_domain_matrix(cred),
        "CONTRADICTIONS": [],
        "ABSTENTIONS": [],
        "ANTICUBE_DELTAS": [{"object_id": r.get("object_id"), "classification": r.get("classification")} for r in anticube],
        "CONTEXT_DELTAS": read_jsonl(CONTROL / "DG_CONTEXT_TIMELINE.jsonl"),
        "CREDENTIAL_STATES": {
            "DAYTONA": cred.get("DAYTONA_CREDENTIAL_STATE"),
            "KAGGLE": cred.get("KAGGLE_CREDENTIAL_STATE"),
            "MISTRAL": cred.get("MISTRAL_CREDENTIAL_STATE"),
        },
        "DOCUMENT_CLOSURE": closure,
        "SECRET_BYTES_INGESTED": 0,
        "MMR_CLAIMED": False,
        "receipt_sha256": "",
    }
    receipt["receipt_sha256"] = sha256_json({k: v for k, v in receipt.items() if k != "receipt_sha256"})
    return receipt


def main() -> int:
    prior = load_json(AUDIT / "CFMO_DELTA_RECEIPT.json")
    corrected = build_corrected_receipt()

    if prior:
        archive = AUDIT / "CFMO_DELTA_RECEIPT.history.jsonl"
        superseded = dict(prior)
        superseded["SUPERSEDED_BY"] = corrected["batch_id"]
        superseded["SUPERSEDED_AT_UTC"] = utc_now()
        with archive.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(superseded, sort_keys=True) + "\n")

    (AUDIT / "CFMO_DELTA_RECEIPT.json").write_text(json.dumps(corrected, indent=2) + "\n")

    cred_path = AUDIT / "CREDENTIAL_CAPABILITY_RECEIPT.json"
    if cred_path.is_file():
        cred = load_json(cred_path) or {}
        cred["PROOF_DOMAIN_MATRIX"] = corrected["PROOF_DOMAIN_MATRIX"]
        cred_path.write_text(json.dumps(cred, indent=2) + "\n")

    for name in ["TOTAL_IMPORT_ACCOUNTING.json", "TOTAL_IMPORT_SCOPE.json"]:
        p = AUDIT / name
        if p.is_file():
            data = load_json(p) or {}
            data["SEEDGRAPH_OBJECT_PROOF"] = {"verified": 0, "pending": data.get("imported", 21), "proof_domain": "SEEDGRAPH_OBJECT_PROOF"}
            data["CAPABILITY_AUTH_PROOF"] = corrected["PROOF_DOMAIN_MATRIX"][1:]
            data["proof_domains_separated"] = True
            p.write_text(json.dumps(data, indent=2) + "\n")

    print(json.dumps({
        "batch_id": corrected["batch_id"],
        "CFMO_BEFORE": corrected["CFMO_BEFORE"],
        "CFMO_NAMESPACE": corrected["CFMO_NAMESPACE"],
        "receipt_sha256": corrected["receipt_sha256"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
