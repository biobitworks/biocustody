#!/usr/bin/env python3
"""Append-only CFMO delta receipt for audit wave (no secret bytes)."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audits" / "TEMPORAL_CONTROL_PLANE"
CONTROL = ROOT / "control"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text())


def main() -> int:
    prior_path = AUDIT / "CFMO_DELTA_RECEIPT.json"
    cfmo_before = load_json(prior_path) or {"batch_id": "CFMO-INITIAL", "CFMO_AFTER": "EMPTY"}

    new_aoks = read_jsonl(AUDIT / "CAPABILITY_AOK_DELTA.jsonl")
    new_aoks += read_jsonl(AUDIT / "AOK_LEDGER.jsonl")
    aok_ids = sorted({r.get("AOK_ID") for r in new_aoks if r.get("AOK_ID")})

    sots = read_jsonl(AUDIT / "SOT_LEDGER.jsonl")
    sot_ids = sorted({r.get("SOT_ID") for r in sots if r.get("SOT_ID")})

    cred_receipt = load_json(AUDIT / "CREDENTIAL_CAPABILITY_RECEIPT.json") or {}
    closure = load_json(AUDIT / "PROJECT_DOCUMENT_001_CLOSURE_RECEIPT.json") or {}
    anticube = read_jsonl(CONTROL / "ANTICUBE_CLASSIFICATION_RECEIPTS.jsonl")

    new_sources = []
    for p in [
        AUDIT / "CREDENTIAL_CAPABILITY_RECEIPT.json",
        CONTROL / "CREDENTIAL_DISCOVERY_RECEIPT.json",
        AUDIT / "PROJECT_DOCUMENT_001_CLOSURE_RECEIPT.json",
    ]:
        if p.is_file():
            new_sources.append({"path": str(p), "content_id": sha256_file(p), "secret_bytes": 0})

    batch_body = {
        "wave": "CREDENTIAL_DISCOVERY_SEMANTIC_CLOSURE_20260829",
        "new_aok_ids": aok_ids,
        "new_sot_ids": sot_ids,
        "recorded_at": utc_now(),
    }
    batch_id = f"CFMO-BATCH-{hashlib.sha256(json.dumps(batch_body, sort_keys=True).encode()).hexdigest()[:16]}"

    delta: dict[str, Any] = {
        "schema": "biocustody.cfmo_delta_receipt.v1",
        "batch_id": batch_id,
        "recorded_at_utc": utc_now(),
        "CFMO_BEFORE": cfmo_before.get("CFMO_AFTER", "EMPTY"),
        "NEW_SOURCE_SET": new_sources,
        "NEW_AOK_SET": aok_ids,
        "NEW_SOT_SET": sot_ids,
        "NEW_GRAPH_EDGES": [
            {"from": "CREDENTIAL_CAPABILITY_RECEIPT", "to": aid, "edge": "capability_probe"}
            for aid in aok_ids
            if aid.startswith("AOK-CAP-")
        ],
        "CONTRADICTIONS": [],
        "ABSTENTIONS": [e.get("edge_id") for e in read_jsonl(AUDIT / "PROJECT_DOCUMENT_001_UNRESOLVED_EDGES.jsonl") if e.get("resolution") == "ABSTAIN"],
        "ANTICUBE_DELTAS": [{"object_id": r.get("object_id"), "classification": r.get("classification")} for r in anticube],
        "CONTEXT_DELTAS": read_jsonl(CONTROL / "DG_CONTEXT_TIMELINE.jsonl"),
        "CREDENTIAL_STATES": {
            "DAYTONA": cred_receipt.get("DAYTONA_CREDENTIAL_STATE"),
            "KAGGLE": cred_receipt.get("KAGGLE_CREDENTIAL_STATE"),
            "MISTRAL": cred_receipt.get("MISTRAL_CREDENTIAL_STATE"),
        },
        "DOCUMENT_CLOSURE": closure,
        "SECRET_BYTES_INGESTED": 0,
        "CFMO_AFTER": batch_id,
        "MMR_CLAIMED": False,
    }

    out = AUDIT / "CFMO_DELTA_RECEIPT.json"
    if prior_path.is_file():
        archive = AUDIT / "CFMO_DELTA_RECEIPT.history.jsonl"
        with archive.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(cfmo_before, sort_keys=True) + "\n")
    out.write_text(json.dumps(delta, indent=2) + "\n")
    print(json.dumps({"batch_id": batch_id, "new_aoks": len(aok_ids)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
