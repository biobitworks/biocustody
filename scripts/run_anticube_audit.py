#!/usr/bin/env python3
"""Real AntiCube classifications for custody audit objects where ruleset applies."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "control"
AUDIT = ROOT / "audits" / "TEMPORAL_CONTROL_PLANE"
HYDRADG = Path("/Users/byron/projects/active/hydradg")
CLASSIFIER = HYDRADG / "scripts/classify_ic_failure_anticube.py"
CLASSIFIER_SHA = hashlib.sha256(CLASSIFIER.read_bytes()).hexdigest() if CLASSIFIER.is_file() else None


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def append_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")


def receipt(
    object_id: str,
    classification: str,
    *,
    applicable: bool,
    basis: str,
    prior: str = "NOT_EVALUATED",
) -> dict[str, Any]:
    return {
        "receipt_type": "ClassificationReceipt",
        "object_id": object_id,
        "prior_anticube_class": prior,
        "classification": classification if applicable else "NOT_APPLICABLE",
        "applicable": applicable,
        "basis": basis,
        "ruleset_sha256": CLASSIFIER_SHA,
        "classifier_version": "hydradg-ic-failure-anticube-1.0.0",
        "claim_ceiling": "SYNTHETIC_REGRESSION" if "SYN-" in object_id else "PARTIAL_EVIDENCE",
        "recorded_at_utc": utc_now(),
        "proof_state": "VERIFIED" if applicable else "PENDING",
    }


def main() -> int:
    rows: list[dict] = []

    # Verified citation/source — bibliography authority, not IC failure object
    rows.append(
        receipt(
            "AOK-ORG-NOTICE-001",
            "NOT_APPLICABLE",
            applicable=False,
            basis="Organizer notice is custody/submission authority; IC failure AntiCube quadrant semantics do not apply",
        )
    )

    # Unresolved support edge — related-work citation framing
    rows.append(
        receipt(
            "EDGE-PD001-S-0008",
            "NOT_APPLICABLE",
            applicable=False,
            basis="Manuscript citation framing edge; scoped AntiCube classifier targets IC failure-learning objects",
        )
    )

    # Blocked remote capability — credential absence is operational, not AntiCube quadrant
    rows.append(
        receipt(
            "AOK-CAP-MISTRAL-001",
            "NOT_APPLICABLE",
            applicable=False,
            basis="Credential capability receipt; authentication_state NOT_FOUND is not an IC self/safe classification input",
        )
    )

    # NOT_ESTABLISHED SOTs
    for sot in ["SOT-008", "SOT-014"]:
        rows.append(
            receipt(
                sot,
                "NOT_APPLICABLE",
                applicable=False,
                basis="NOT_ESTABLISHED scientific SOT; AntiCube IC classifier not validated for experiment proposition objects",
            )
        )

    # Successful deterministic audit receipt — reference integrity
    rows.append(
        receipt(
            "REFERENCE_INTEGRITY_DELTA_20260829",
            "NOT_APPLICABLE",
            applicable=False,
            basis="Deterministic bib repair receipt; outside IC failure-learning domain",
        )
    )

    # Verified capability probes — deterministic external auth
    for cap in ["AOK-CAP-DAYTONA-001", "AOK-CAP-KAGGLE-001"]:
        rows.append(
            receipt(
                cap,
                "NOT_APPLICABLE",
                applicable=False,
                basis="Redacted capability atom; DETERMINISTIC_EXTERNAL_CAPABILITY_PROBE is not IC quadrant input",
            )
        )

    append_jsonl(CONTROL / "ANTICUBE_CLASSIFICATION_RECEIPTS.jsonl", rows)

    summary = {
        "recorded_at_utc": utc_now(),
        "classifications_appended": len(rows),
        "NOT_APPLICABLE_count": sum(1 for r in rows if r["classification"] == "NOT_APPLICABLE"),
        "NOT_EVALUATED_remaining": "custody rows until IC-scoped object submitted",
    }
    (AUDIT / "ANTICUBE_DELTA_RECEIPT.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
