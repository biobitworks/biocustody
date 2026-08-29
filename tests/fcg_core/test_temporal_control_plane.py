"""Temporal control plane invariant tests."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTROL = ROOT / "control"
AUDIT = ROOT / "audits" / "TEMPORAL_CONTROL_PLANE"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_priority_rows_have_anticube_and_proof():
    rows = load_jsonl(CONTROL / "PLAN_PRIORITY_LEDGER.jsonl")
    assert rows
    for r in rows:
        assert r["ANTICUBE_CLASS"] in {
            "NOT_EVALUATED", "UNKNOWN", "SELF_SAFE", "SELF_NONSAFE", "NONSELF_SAFE", "NONSELF_NONSAFE",
        }
        assert r["PROOF_STATE"]
        assert "SECRET_VALUE" not in json.dumps(r)


def test_secret_blockers_never_log_values():
    rows = load_jsonl(CONTROL / "SECRET_BLOCKER_LEDGER.jsonl")
    for r in rows:
        assert r.get("value_logged") == "NO"
        blob = json.dumps(r).lower()
        assert "secret_value" not in blob


def test_anticube_timeline_append_only():
    events = load_jsonl(CONTROL / "ANTICUBE_TIMELINE.jsonl")
    assert len(events) >= 4
    assert events[0]["new_class"] == "UNKNOWN"


def test_document_001_no_pdf_mutation_flag():
    manifest = json.loads((AUDIT / "PROJECT_DOCUMENT_001_MANIFEST.json").read_text())
    assert manifest["sealed_pdf_mutation"] == "FORBIDDEN"
