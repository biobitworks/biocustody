#!/usr/bin/env python3
"""Write preregistration bundle for AUD-FCG-ATOM-SOT-ROUNDTRIP-002 (no outcomes)."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audits" / "AUD-FCG-ATOM-SOT-ROUNDTRIP-002"
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

    prereg = {
        "audit_id": "AUD-FCG-ATOM-SOT-ROUNDTRIP-002",
        "registered_at_utc": utc_now(),
        "host": subprocess.check_output(["hostname"], text=True).strip(),
        "source_commit": SOURCE_COMMIT,
        "prior_lattice_audit": "AUD-FCG-ATOM-SOT-ROUNDTRIP-001",
        "prior_lattice_id": "AUD-FCG-ATOM-SOT-ROUNDTRIP-001",
        "note": "Builds on AUD-FCG-DOCUMENT-LATTICE-001 frozen corpus",
        "primary_question": "Does FULL verify-or-abstain materially outperform crypto-only and structural baselines on semantic/provenance disposition?",
        "allowed_terminals": ["PASS", "NEGATIVE", "NULL", "UNDERPOWERED", "FAILED", "BLOCKED", "QUARANTINED"],
        "no_optional_stopping": True,
        "post_hoc_label": "POST_HOC_ANALYSIS",
    }
    # fix audit id reference
    prereg["prior_lattice_audit"] = "AUD-FCG-DOCUMENT-LATTICE-001"

    write_json(AUDIT / "PREREGISTRATION.json", prereg)

    write_json(
        AUDIT / "HYPOTHESES.json",
        {
            "H0-CUSTODY-SUFFICIENCY": {
                "comparison": "B3 vs B0",
                "endpoint": "CORRECT_SEMANTIC_DISPOSITION",
                "alternative": "B3 > B0 with practical effect >= 0.15",
            },
            "H0-STRUCTURE-SUFFICIENCY": {
                "comparison": "B3 vs B1",
                "endpoint": "CORRECT_SEMANTIC_DISPOSITION",
                "alternative": "B3 > B1 with practical effect >= 0.15",
            },
            "H0-ABSTENTION-NO-VALUE": {
                "comparison": "B3 vs B2",
                "endpoint": "FALSE_CLAIM_ACCEPTANCE_RATE",
                "alternative": "B3 false-acceptance < B2",
            },
            "H0-BENIGN-INVARIANCE": {
                "target": "false_semantic_promotion <= 0.05",
            },
            "H0-SEEDGRAPH-LOSS": {
                "evaluation": "deterministic conformance roundtrip",
            },
        },
    )

    write_json(
        AUDIT / "MUTATION_FAMILIES.json",
        {
            "families": [
                "synonymous",
                "substitution",
                "insertion",
                "deletion",
                "duplication",
                "transposition",
                "recombination",
                "gain-of-function",
                "contradiction",
                "provenance",
                "table/figure",
                "attestation",
            ],
            "generator": "fcg_core.mutation_benchmark.generate_mutation_manifest",
            "deterministic": True,
            "cluster_rule": "CLUSTER_ID = BASE_OBJECT_ID",
        },
    )

    write_json(
        AUDIT / "BASELINE_DEFINITIONS.json",
        {
            "B0_CRYPTO_CUSTODY_ONLY": "SHA-256 byte/manifest seal only",
            "B1_STRUCTURAL_LATTICE": "Lattice identity/parent/order without AtomV2→AOK→SOT",
            "B2_VERIFY_ONLY_NO_ABSTAIN": "Full checks but forced VERIFY/REJECT",
            "B3_FULL_VERIFY_OR_ABSTAIN": "AtomV2+AOK+SOT+abstention+contradiction+ceilings",
        },
    )

    # Pre-outcome power simulation (planned N=12 mutations)
    import numpy as np

    rng = np.random.default_rng(20260829)
    n_planned = 12
    p_b3, p_b0 = 0.88, 0.42
    sims = []
    for _ in range(5000):
        b3 = rng.binomial(n_planned, p_b3)
        b0 = rng.binomial(n_planned, p_b0)
        sims.append(b3 - b0)
    sims_arr = np.array(sims)
    power_est = float(np.mean(sims_arr / n_planned >= 0.15))
    write_json(
        AUDIT / "POWER_PLAN.json",
        {
            "alpha": 0.05,
            "target_power": 0.80,
            "planned_mutation_cases_min": 10,
            "planned_mutation_cases_simulation_n": n_planned,
            "simulated_p_b3": p_b3,
            "simulated_p_b0": p_b0,
            "simulated_practical_threshold": 0.15,
            "simulated_power_estimate": power_est,
            "rng_seed": 20260829,
            "note": "Pre-outcome simulation only; actual N recorded at execution",
        },
    )

    write_json(
        AUDIT / "STATISTICAL_ANALYSIS_PLAN.json",
        {
            "primary_endpoints": [
                "CORRECT_SEMANTIC_DISPOSITION",
                "CORRECT_DOWNSTREAM_LOCALIZATION",
                "FALSE_SEMANTIC_PROMOTION_RATE",
                "FALSE_CLAIM_ACCEPTANCE_RATE",
                "TERMINAL_ACCOUNTING_RATE",
            ],
            "omnibus": "Cochran Q",
            "pairwise": "Exact McNemar",
            "multiple_comparison": "Holm FWER",
            "alpha": 0.05,
            "effect_threshold_absolute": 0.15,
            "clustered_sensitivity": "statsmodels GEE binary family cluster=BASE_OBJECT_ID",
            "bootstrap": {"seed": 20260829, "clusters": "BASE_OBJECT_ID", "ci": "95% BCa"},
            "conformance_endpoints_no_pvalue": [
                "UNMUTATED_ROUNDTRIP_IDENTITY",
                "PROVENANCE_PRESERVATION",
                "CONTRADICTION_PRESERVATION",
                "TERMINAL_ACCOUNTING",
                "SECRET_SAFETY",
            ],
        },
    )

    write_json(
        AUDIT / "SOURCE_MANIFEST.json",
        {
            "source_commit": SOURCE_COMMIT,
            "lattice_audit_path": "audits/AUD-FCG-DOCUMENT-LATTICE-001",
            "atomization_path": "audits/AUD-FCG-DOCUMENT-LATTICE-001/SEEDGRAPH_ATOMIZATION",
            "sealed_pdf_mutation": "FORBIDDEN",
            "pdf_for_atom_extract": "paper/newinml2026/manuscript/main_smoke.pdf",
        },
    )

    try:
        import numpy as np2
        import pandas
        import scipy
        try:
            import statsmodels
            sm_ver = statsmodels.__version__
        except ImportError:
            sm_ver = "NOT_INSTALLED"
    except ImportError:
        np2 = scipy = pandas = None
        sm_ver = "NOT_INSTALLED"

    write_json(
        AUDIT / "TOOLCHAIN_LOCK.json",
        {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "numpy": getattr(np2, "__version__", "NOT_INSTALLED"),
            "pandas": getattr(pandas, "__version__", "NOT_INSTALLED"),
            "scipy": getattr(scipy, "__version__", "NOT_INSTALLED"),
            "statsmodels": sm_ver,
            "biocustody_branch": subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT, text=True).strip(),
            "biocustody_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        },
    )

    files = [
        "PREREGISTRATION.json",
        "HYPOTHESES.json",
        "MUTATION_FAMILIES.json",
        "BASELINE_DEFINITIONS.json",
        "POWER_PLAN.json",
        "STATISTICAL_ANALYSIS_PLAN.json",
        "SOURCE_MANIFEST.json",
        "TOOLCHAIN_LOCK.json",
    ]
    manifest_files = {}
    for fname in files:
        manifest_files[fname] = sha256_file(AUDIT / fname)

    prereg_manifest = {
        "schema": "biocustody.preregistration_manifest.v1",
        "audit_id": "AUD-FCG-ATOM-SOT-ROUNDTRIP-002",
        "registered_at_utc": utc_now(),
        "files": manifest_files,
        "PREREGISTRATION_SHA256": hashlib.sha256(
            json.dumps(manifest_files, sort_keys=True).encode()
        ).hexdigest(),
        "PREREGISTRATION_GIT_SHA": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    }
    write_json(AUDIT / "PREREGISTRATION_MANIFEST.json", prereg_manifest)
    print(json.dumps(prereg_manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
