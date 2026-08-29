#!/usr/bin/env python3
"""ANTIGENCE-AIS comparator — B4 vs B0–B3 on frozen mutation manifest."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audits" / "AUD-FCG-ATOM-SOT-SEMANTIC-003"
LATTICE = ROOT / "audits" / "AUD-FCG-DOCUMENT-LATTICE-001"
ANTIGENCE_ROOT = Path("/Users/byron/projects/active/antigence")

sys.path.insert(0, str(ROOT / "src"))

from fcg_core.antigence_b4 import (  # noqa: E402
    FROZEN_ANTIGENCE_SHA,
    load_runtime,
    verify_manifest_and_build_identities,
)
from fcg_core.pipeline_baselines import evaluate_mutation  # noqa: E402
from fcg_core.roundtrip_stats import analyze_pipeline_results, write_pairwise_tex  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> int:
    manifest_entries, verification = verify_manifest_and_build_identities()
    write_json(
        AUDIT / "ANTIGENCE_MODEL_MANIFEST.json",
        {
            "frozen_antigence_git_sha": FROZEN_ANTIGENCE_SHA,
            "recorded_at_utc": utc_now(),
            "domain_pack": str(ANTIGENCE_ROOT / "config/domain-packs/protein-hinge-v1.yaml"),
            "admission_classes": {
                "CANONICAL_ANTIBODY": [
                    "authors_antibody",
                    "doi_antibody",
                    "journal_antibody",
                    "pmid_antibody",
                    "title_antibody",
                    "year_antibody",
                ],
                "EXPERIMENTAL_TRAINED_CELL": ["scifact_bcell", "scifact_nk"],
            },
            "models": manifest_entries,
            **verification,
        },
    )

    bindings = []
    for m in manifest_entries:
        if m.get("MODEL_CONTENT_ID"):
            for domain in [
                "citation_identity",
                "doi_integrity",
                "source_attribution",
                "provenance_integrity",
                "claim_support_integrity",
            ]:
                bindings.append(
                    {
                        "domain": domain,
                        "model_name": m["model_name"],
                        "MODEL_SEMANTIC_ID": m.get("MODEL_SEMANTIC_ID"),
                        "MODEL_CONTENT_ID": m.get("MODEL_CONTENT_ID"),
                        "admission_class": m.get("admission_class"),
                        "antigence_git_sha": FROZEN_ANTIGENCE_SHA,
                    }
                )
    write_jsonl(AUDIT / "ANTIGENCE_FCG_BINDINGS.jsonl", bindings)

    rt = load_runtime()
    mutations = load_jsonl(AUDIT / "MUTATION_MANIFEST.jsonl")
    sentences = {s["object_id"]: s for s in load_jsonl(LATTICE / "PRE_INGEST" / "SENTENCES.jsonl")}
    table_cells = {c["object_id"]: c for c in load_jsonl(LATTICE / "PRE_INGEST" / "TABLE_CELLS.jsonl")}

    b4_results: list[dict] = []
    pipeline_results: list[dict] = []
    for mut in mutations:
        base_id = mut["BASE_OBJECT_ID"]
        if mut["BASE_OBJECT_TYPE"] == "Sentence":
            baseline = sentences.get(base_id, {})
        elif mut["BASE_OBJECT_TYPE"] == "TableCell":
            baseline = table_cells.get(base_id, {})
        else:
            baseline = mut.get("mutated_payload", {})
        for outcome in evaluate_mutation(mut, baseline, b4_runtime=rt):
            row = {
                "MUTATION_ID": mut["MUTATION_ID"],
                "MUTATION_FAMILY": mut["MUTATION_FAMILY"],
                "CLUSTER_ID": mut["CLUSTER_ID"],
                **outcome,
            }
            pipeline_results.append(row)
            if outcome.get("pipeline") == "B4_ANTIGENCE_TRAINED_AIS":
                b4_results.append(row)

    write_jsonl(AUDIT / "ANTIGENCE_MUTATION_RESULTS.jsonl", b4_results)
    write_jsonl(AUDIT / "PIPELINE_RESULTS_B4.jsonl", pipeline_results)

    stats = analyze_pipeline_results(pipeline_results)
    import pandas as pd

    pd.DataFrame(stats["pairwise"]).to_csv(AUDIT / "PAIRWISE_PIPELINE_COMPARISON_B4.csv", index=False)
    write_json(AUDIT / "PAIRWISE_PIPELINE_COMPARISON_B4.json", {"rows": stats["pairwise"]})
    write_pairwise_tex(stats["pairwise"], str(AUDIT / "PAIRWISE_PIPELINE_COMPARISON_B4.tex"))
    write_json(AUDIT / "MUTATION_FAMILY_RESULTS_B4.json", {"rows": stats["mutation_family_results"]})
    pd.DataFrame(stats["mutation_family_results"]).to_csv(AUDIT / "MUTATION_FAMILY_RESULTS_B4.csv", index=False)
    write_json(AUDIT / "GEE_SENSITIVITY_RESULTS_B4.json", stats["gee_sensitivity"])
    write_json(AUDIT / "BOOTSTRAP_RESULTS_B4.json", stats["bootstrap"])

    gee = stats["gee_sensitivity"]
    b3 = stats["pipeline_summary"].get("B3_FULL_VERIFY_OR_ABSTAIN", {})
    b4 = stats["pipeline_summary"].get("B4_ANTIGENCE_TRAINED_AIS", {})
    b3_b4 = next(
        (
            r
            for r in stats["pairwise"]
            if r["endpoint"] == "correct_semantic_disposition"
            and {r["pipeline_a"], r["pipeline_b"]} == {"B3_FULL_VERIFY_OR_ABSTAIN", "B4_ANTIGENCE_TRAINED_AIS"}
        ),
        None,
    )

    receipt = {
        "audit_id": "ANTIGENCE-AIS-COMPARATOR",
        "recorded_at_utc": utc_now(),
        "frozen_antigence_git_sha": FROZEN_ANTIGENCE_SHA,
        "mutation_manifest": str(AUDIT / "MUTATION_MANIFEST.jsonl"),
        "n_mutations": len(mutations),
        "scifact_cells_status": verification["manifest_verification"].get("scifact_bcell"),
        "canonical_antibodies_verified": all(
            v == "PASS"
            for k, v in verification["manifest_verification"].items()
            if k.endswith("_antibody.pkl")
        ),
        "B3_semantic_disposition_rate": b3.get("correct_semantic_disposition_rate"),
        "B4_semantic_disposition_rate": b4.get("correct_semantic_disposition_rate"),
        "B3_false_claim_acceptance_rate": b3.get("false_claim_acceptance_rate"),
        "B4_false_claim_acceptance_rate": b4.get("false_claim_acceptance_rate"),
        "B3_vs_B4_semantic_disposition": b3_b4,
        "endpoint_distinction": [
            "ANOMALY_DETECTION",
            "SEMANTIC_DISPOSITION",
            "CAUSAL_LOCALIZATION",
            "CLAIM_CEILING_DISPOSITION",
        ],
        "blind_to_mutation_truth": True,
        "load_errors": rt.load_errors,
        "gee_sensitivity_status": gee.get("status"),
        "gee_sensitivity_reason": gee.get("reason"),
    }
    write_json(AUDIT / "ANTIGENCE_COMPARISON_RECEIPT.json", receipt)

    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
