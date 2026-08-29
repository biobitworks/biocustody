#!/usr/bin/env python3
"""Preregister AUD-FCG-ATOM-SOT-SEMANTIC-003 before outcomes."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audits" / "AUD-FCG-ATOM-SOT-SEMANTIC-003"
PREDECESSOR = "AUD-FCG-ATOM-SOT-ROUNDTRIP-002"
SOURCE_COMMIT = "4a372a5c459ad60cd23b850709011cbfd0e516b4"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def main() -> int:
    AUDIT.mkdir(parents=True, exist_ok=True)
    write_json(
        AUDIT / "PREREGISTRATION.json",
        {
            "audit_id": "AUD-FCG-ATOM-SOT-SEMANTIC-003",
            "predecessor_audit": PREDECESSOR,
            "registered_at_utc": utc_now(),
            "host": subprocess.check_output(["hostname"], text=True).strip(),
            "source_commit": SOURCE_COMMIT,
            "primary_question": "Does semantic SOT support validation + full pipeline outperform custody-only baselines?",
            "allowed_terminals": [
                "PASS", "NEGATIVE", "NULL", "UNDERPOWERED", "FAILED", "BLOCKED",
                "QUARANTINED", "ABSTAIN", "NOT_APPLICABLE", "NOT_ESTABLISHED",
            ],
            "post_hoc_label": "POST_HOC",
            "no_optional_stopping": True,
            "no_n_inflation_after_outcomes": True,
        },
    )
    write_json(
        AUDIT / "HYPOTHESES.json",
        {
            "H0-A-CUSTODY-SUFFICIENCY": {"comparison": "B3 vs B0", "endpoint": "CORRECT_SEMANTIC_DISPOSITION"},
            "H0-B-STRUCTURE-SUFFICIENCY": {"comparison": "B3 vs B1", "endpoint": "CORRECT_SEMANTIC_DISPOSITION"},
            "H0-C-ABSTENTION-VALUE": {"comparison": "B3 vs B2", "endpoint": "FALSE_CLAIM_ACCEPTANCE_RATE"},
            "H0-SEMANTIC-SOT-SUPPORT": {"endpoint": "SOT semantic support terminal accounting"},
        },
    )
    write_json(
        AUDIT / "STATISTICAL_ANALYSIS_PLAN.json",
        {
            "alpha": 0.05,
            "target_power": 0.80,
            "minimum_practical_improvement": 0.15,
            "omnibus": "Cochran Q",
            "pairwise": "Exact McNemar all 6 pipeline pairs",
            "multiple_comparison": "Holm FWER",
            "clustered_sensitivity": "GEE binary cluster=BASE_OBJECT_ID",
            "bootstrap_seed": 20260829,
        },
    )
    write_json(AUDIT / "BASELINE_DEFINITIONS.json", json.loads((ROOT / "audits/AUD-FCG-ATOM-SOT-ROUNDTRIP-002/BASELINE_DEFINITIONS.json").read_text()))
    template_path = AUDIT / "MUTATION_MANIFEST.template.jsonl"
    template_path.write_text(
        json.dumps({"MUTATION_FAMILY": "template", "note": "ground truth from generator only"}) + "\n"
    )
    import numpy as np

    write_json(
        AUDIT / "POWER_PLAN.json",
        {
            "alpha": 0.05,
            "target_power": 0.80,
            "planned_mutation_cases": 13,
            "minimum_practical_improvement": 0.15,
            "predecessor_actual_n": 13,
            "predecessor_terminal": "UNDERPOWERED",
            "rng_seed": 20260829,
            "note": "Same frozen corpus; no post-hoc N inflation",
        },
    )
    write_json(
        AUDIT / "SOURCE_MANIFEST.json",
        {
            "source_commit": SOURCE_COMMIT,
            "lattice_audit": "audits/AUD-FCG-DOCUMENT-LATTICE-001",
            "predecessor_audit": f"audits/{PREDECESSOR}",
            "manuscript_source": "paper/newinml2026/manuscript/main.tex",
            "sealed_pdf_mutation": "FORBIDDEN",
        },
    )
    try:
        import pandas
        import scipy
        import statsmodels
        sm_v = statsmodels.__version__
    except ImportError:
        pandas = scipy = None
        sm_v = "NOT_INSTALLED"
    write_json(
        AUDIT / "TOOLCHAIN_LOCK.json",
        {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "numpy": __import__("numpy").__version__,
            "pandas": getattr(pandas, "__version__", "NOT_INSTALLED"),
            "scipy": getattr(scipy, "__version__", "NOT_INSTALLED"),
            "statsmodels": sm_v,
            "biocustody_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        },
    )
    write_json(
        AUDIT / "CLAIM_CEILING_MATRIX.initial.json",
        {"SOT-008": "NOT_ESTABLISHED", "SOT-014": "NOT_ESTABLISHED", "default": "REPURPOSING_HYPOTHESIS"},
    )
    files = [
        "PREREGISTRATION.json", "HYPOTHESES.json", "STATISTICAL_ANALYSIS_PLAN.json",
        "MUTATION_MANIFEST.template.jsonl", "BASELINE_DEFINITIONS.json", "POWER_PLAN.json",
        "SOURCE_MANIFEST.json", "TOOLCHAIN_LOCK.json", "CLAIM_CEILING_MATRIX.initial.json",
    ]
    manifest_files = {f: sha256_file(AUDIT / f) for f in files}
    prereg_sha = hashlib.sha256(json.dumps(manifest_files, sort_keys=True).encode()).hexdigest()
    write_json(
        AUDIT / "PREREGISTRATION_MANIFEST.json",
        {
            "schema": "biocustody.preregistration_manifest.v1",
            "audit_id": "AUD-FCG-ATOM-SOT-SEMANTIC-003",
            "registered_at_utc": utc_now(),
            "files": manifest_files,
            "PREREGISTRATION_SHA256": prereg_sha,
            "PREREGISTRATION_GIT_SHA": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        },
    )
    print(json.dumps({"PREREGISTRATION_SHA256": prereg_sha}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
