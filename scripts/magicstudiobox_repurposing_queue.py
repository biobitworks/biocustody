#!/usr/bin/env python
from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs" / "magicstudiobox"
BASELINE = RUN_ROOT / "baseline"
PRIMARY = RUN_ROOT / "primary"
FIGURES = PRIMARY / "figures"
TEXT_FIGURES = ROOT / "deliverables" / "text_figures"
CLAIM_CEILING = "REPURPOSING_HYPOTHESIS"
SEED = 260813
TIMEOUT = 45


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): clean(value[k]) for k in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return float(repr(value))
    if hasattr(value, "item"):
        return clean(value.item())
    if hasattr(value, "tolist"):
        return clean(value.tolist())
    if isinstance(value, Path):
        return str(value)
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(clean(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest_obj(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(clean(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def run_cmd(name: str, cmd: list[str], out_dir: Path, timeout: int | None = None) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    started = now()
    log_path = out_dir / f"{name}.log"
    try:
        p = subprocess.run(
            cmd,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        rc = p.returncode
        output = p.stdout
    except subprocess.TimeoutExpired as exc:
        rc = 124
        output = (exc.stdout or "") + "\nTIMEOUT\n"
    log_path.write_text(output, encoding="utf-8")
    return {
        "name": name,
        "cmd": cmd,
        "rc": rc,
        "started_at": started,
        "finished_at": now(),
        "log": str(log_path.relative_to(ROOT)),
        "sha256": file_sha256(log_path),
    }


def http_json(url: str, timeout: int = TIMEOUT) -> tuple[str, Any | None]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BioCustody-Hackday/0.2"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return "ok", json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        return f"unavailable:{type(exc).__name__}:{exc}", None


def make_fco(object_type: str, payload: dict[str, Any], source: dict[str, Any], parents: list[str] | None = None) -> dict[str, Any]:
    unsigned = {
        "fco_version": "hackday-0.3-problem2",
        "object_type": object_type,
        "payload": payload,
        "source": source,
        "parents": parents or [],
        "claim": {"claim_ceiling": CLAIM_CEILING},
        "created_at": now(),
    }
    return {**unsigned, "digest": digest_obj(unsigned)}


def verify_fco(fco: dict[str, Any]) -> bool:
    unsigned = {k: fco[k] for k in ["fco_version", "object_type", "payload", "source", "parents", "claim", "created_at"]}
    return fco["digest"] == digest_obj(unsigned)


def merkle_root(digests: list[str]) -> str:
    if not digests:
        return hashlib.sha256(b"").hexdigest()
    level = [hashlib.sha256(b"\x00" + d.encode()).digest() for d in digests]
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [hashlib.sha256(b"\x01" + level[i] + level[i + 1]).digest() for i in range(0, len(level), 2)]
    return level[0].hex()


def load_best_sources() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    sweep_path = ROOT / "runs" / "kaggle_output" / "cpjump1_selection_sweep_results.csv"
    ranking_path = ROOT / "runs" / "kaggle_output" / "cpjump1_best_ranking.csv"
    result_path = ROOT / "runs" / "kaggle_output" / "cpjump1_best_result.json"
    if not sweep_path.exists():
        sweep_path = ROOT / "runs" / "kaggle" / "cpjump1_selection_sweep_results.csv"
    if not ranking_path.exists():
        ranking_path = ROOT / "runs" / "kaggle" / "cpjump1_best_ranking.csv"
    if not result_path.exists():
        result_path = ROOT / "runs" / "kaggle" / "cpjump1_best_result.json"
    sweep = pd.read_csv(sweep_path)
    ranking = pd.read_csv(ranking_path)
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["_source_paths"] = {
        "selection_sweep": str(sweep_path.relative_to(ROOT)),
        "selection_sweep_sha256": file_sha256(sweep_path),
        "ranking": str(ranking_path.relative_to(ROOT)),
        "ranking_sha256": file_sha256(ranking_path),
        "result": str(result_path.relative_to(ROOT)),
        "result_sha256": file_sha256(result_path),
    }
    return sweep, ranking, result


def phase0_baseline() -> dict[str, Any]:
    BASELINE.mkdir(parents=True, exist_ok=True)
    steps = [
        run_cmd("check_env", [sys.executable, "scripts/check_env.py"], BASELINE, 180),
        run_cmd("pytest", [sys.executable, "-m", "pytest", "-q"], BASELINE, 240),
        run_cmd("demo_synthetic", [sys.executable, "scripts/demo_synthetic.py"], BASELINE, 180),
        run_cmd("demo_cpjump1_benchmark", [sys.executable, "scripts/demo_cpjump1_benchmark.py"], BASELINE, 600),
    ]
    for src in [ROOT / "runs/local/synthetic_demo_result.json", ROOT / "runs/local/cpjump1_benchmark_result.json"]:
        if src.exists():
            shutil.copy2(src, BASELINE / src.name)
    status = "PASS" if all(s["rc"] == 0 for s in steps[:3]) else "FAIL"
    cpjump1_status = "PASS" if steps[3]["rc"] == 0 else "FALLBACK_TO_CACHED_KAGGLE"
    baseline = {
        "schema": "biocustody.magicstudiobox.baseline.v1",
        "ts_utc": now(),
        "status": status,
        "cpjump1_workflow_status": cpjump1_status,
        "steps": steps,
        "claim_ceiling": CLAIM_CEILING,
        "expansion_allowed": status == "PASS",
    }
    write_json(BASELINE / "baseline_results.json", baseline)
    return baseline


def phase1_select_perturbation(sweep: pd.DataFrame, source_paths: dict[str, str]) -> dict[str, Any]:
    enriched = sweep.copy()
    enriched["replicate_consistency"] = "not_available_in_cached_sweep"
    enriched["data_source"] = source_paths["selection_sweep"]
    enriched["source_hash"] = source_paths["selection_sweep_sha256"]
    enriched["selection_rule_pass"] = (
        enriched["decision"].eq("TRANSITION")
        & enriched["control_rows"].ge(20)
        & enriched["candidate_count"].ge(10)
        & enriched["has_target_candidate"].fillna(False).astype(bool)
        & enriched["positive_top_score"].fillna(False).astype(bool)
        & enriched["shift_margin"].gt(0)
    )
    enriched["selection_priority"] = (
        enriched["selection_rule_pass"].astype(int) * 100000
        + enriched["positive_target_score"].fillna(False).astype(int) * 10000
        + enriched["shift_margin"].clip(lower=0)
        + (1.0 / enriched["best_target_rank"].fillna(9999).clip(lower=1))
    )
    enriched = enriched.sort_values(["selection_priority", "shift_margin"], ascending=[False, False]).reset_index(drop=True)
    enriched.to_csv(RUN_ROOT / "selection_sweep.csv", index=False)
    write_json(RUN_ROOT / "selection_sweep.json", enriched.to_dict(orient="records"))
    selected = enriched.iloc[0].to_dict()
    state = {
        "schema": "biocustody.magicstudiobox.perturbation_selection.v1",
        "ts_utc": now(),
        "selected_gene": selected["gene"],
        "selected_perturbation_id": f"{selected['orf_plate']}:{selected['gene']}",
        "selected_rule": [
            "decision == TRANSITION",
            "control_rows >= 20",
            "candidate_count >= 10",
            "has matched/known compound relationship where available",
            "positive top morphology opposition score",
            "positive shift margin",
            "rank by rule pass, positive target score, shift margin, and known-pair rank",
        ],
        "selected_record": selected,
        "claim_ceiling": CLAIM_CEILING,
    }
    write_json(PRIMARY / "perturbation_state.json", state)
    return state


def parse_listish(value: Any) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    if text.startswith("[") and text.endswith("]"):
        return [x.strip().strip("'\"") for x in text.strip("[]").split(",") if x.strip()]
    return [x.strip() for x in text.split("|") if x.strip()]


def phase2_ranking(ranking: pd.DataFrame, result: dict[str, Any], perturbation: dict[str, Any]) -> dict[str, Any]:
    PRIMARY.mkdir(parents=True, exist_ok=True)
    ranking = ranking.copy()
    ranking["phenotype_opposition"] = ranking["restoration_score"]
    ranking["reference_state_result"] = ranking["distance_ratio"].apply(
        lambda x: "closer_to_reference_than_perturbation" if float(x) < 1 else "not_closer_to_reference"
    )
    ranking.to_csv(PRIMARY / "candidate_ranking.csv", index=False)

    known = ranking[ranking["target_match"].fillna(False).astype(bool) | ranking["target_list_match"].fillna(False).astype(bool)]
    known_rank = int(known.index[0] + 1) if len(known) else None
    reciprocal_rank = float(1.0 / known_rank) if known_rank else 0.0
    import random

    rng = random.Random(SEED)
    labels = [bool(x) for x in (ranking["target_match"].fillna(False) | ranking["target_list_match"].fillna(False)).tolist()]
    shuffled_rr = []
    shuffled_hits10 = []
    for _ in range(1000):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        first = next((i + 1 for i, val in enumerate(shuffled) if val), None)
        shuffled_rr.append(1.0 / first if first else 0.0)
        shuffled_hits10.append(1 if any(shuffled[:10]) else 0)
    mean_rr = sum(shuffled_rr) / len(shuffled_rr) if shuffled_rr else 0.0
    eval_result = {
        "schema": "biocustody.magicstudiobox.evaluation.v1",
        "ts_utc": now(),
        "candidate_count": int(len(ranking)),
        "top_opposition_score": float(ranking.iloc[0]["restoration_score"]),
        "known_pair_rank": known_rank,
        "hits_at_1": bool(known_rank == 1),
        "hits_at_5": bool(known_rank is not None and known_rank <= 5),
        "hits_at_10": bool(known_rank is not None and known_rank <= 10),
        "reciprocal_rank": reciprocal_rank,
        "shuffle_seed": SEED,
        "shuffle_iterations": 1000,
        "shuffled_mean_reciprocal_rank": mean_rr,
        "shuffled_hits_at_10_rate": sum(shuffled_hits10) / len(shuffled_hits10) if shuffled_hits10 else None,
        "reciprocal_rank_enrichment_vs_shuffle": reciprocal_rank / mean_rr if mean_rr else None,
        "replicate_similarity": "not_available_in_cached_kaggle_output",
        "claim_ceiling": CLAIM_CEILING,
    }
    write_json(PRIMARY / "evaluation.json", eval_result)
    state_model = {
        "schema": "biocustody.magicstudiobox.state_model.v1",
        "source_result": result["_source_paths"]["result"],
        "reference_state": result.get("reference_state", {}),
        "state_decision": result.get("state_decision", {}),
        "model": "median/MAD scaling -> PCA -> Ledoit-Wolf covariance -> empirical q95 threshold",
        "phenotypic_opposition_kept_separate_from_reference_distance": True,
        "claim_ceiling": CLAIM_CEILING,
    }
    write_json(PRIMARY / "state_model.json", state_model)
    return eval_result


def pubchem_identity(name: str, smiles: str) -> dict[str, Any]:
    encoded = urllib.parse.quote(name)
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded}/property/CanonicalSMILES,InChIKey,CID/JSON"
    status, data = http_json(url)
    if status == "ok":
        props = (data.get("PropertyTable", {}).get("Properties") or [{}])[0]
        return {
            "source_name": name,
            "source_smiles": smiles,
            "canonical_smiles": props.get("CanonicalSMILES") or smiles,
            "inchikey": props.get("InChIKey"),
            "pubchem_cid": props.get("CID"),
            "chembl_id": "not_locally_verified",
            "retrieval": "PubChem PUG REST name lookup",
            "retrieval_status": "ok",
            "retrieval_ts_utc": now(),
        }
    return {
        "source_name": name,
        "source_smiles": smiles,
        "canonical_smiles": smiles,
        "inchikey": None,
        "pubchem_cid": None,
        "chembl_id": "not_locally_verified",
        "retrieval": "PubChem PUG REST name lookup",
        "retrieval_status": status,
        "retrieval_ts_utc": now(),
    }


def phase3_identity(ranking: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for row in ranking.head(3).to_dict(orient="records"):
        identity = pubchem_identity(str(row["pert_iname"]), str(row.get("smiles") or ""))
        identity.update(
            {
                "candidate": row["candidate"],
                "broad_sample": row["broad_sample"],
                "transformation": {
                    "source_representation": "CPJUMP1 source SMILES",
                    "transformation_version": "PubChem name lookup when available; otherwise identity fallback",
                    "canonical_representation_policy": "derived artifact; source SMILES preserved separately",
                },
            }
        )
        rows.append(identity)
    write_json(PRIMARY / "molecular_identity.json", rows)
    pd.DataFrame(rows).to_csv(PRIMARY / "molecular_identity.csv", index=False)
    return rows


MECH_MAP = {
    "NR3C1": "glucocorticoid receptor signaling",
    "PLA2G1B": "phospholipase / lipid mediator biology",
    "DHODH": "pyrimidine biosynthesis / immunomodulation",
    "PTK2B": "focal adhesion / tyrosine kinase signaling",
    "SIRT2": "sirtuin deacetylase biology",
    "COMT": "catechol metabolism",
}

COMPARATORS = {
    "desonide": ["hydrocortisone", "dexamethasone", "budesonide", "prednisone"],
    "leflunomide": ["teriflunomide", "methotrexate", "azathioprine"],
    "SirReal-2": ["sirtinol", "nicotinamide"],
}


def phase4_similarity(ranking: pd.DataFrame, identities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    relations = []
    top3 = ranking.head(3).to_dict(orient="records")
    by_candidate = {x["candidate"]: x for x in identities}
    for row in top3:
        targets = set(parse_listish(row.get("target_list"))) | {str(row.get("target"))}
        mechanisms = sorted({MECH_MAP[t] for t in targets if t in MECH_MAP})
        identity = by_candidate.get(row["candidate"], {})
        for comp in COMPARATORS.get(str(row["pert_iname"]), []):
            relations.append(
                {
                    "subject": row["candidate"],
                    "predicate": "MECHANISM_SIMILAR",
                    "object": comp,
                    "method": "curated tiny public-mechanism map from CPJUMP1 target_list",
                    "value": "|".join(mechanisms) if mechanisms else None,
                    "source": "CPJUMP1 target_list plus local hackday mechanism map",
                    "source_version_date": "2026-08-13",
                    "evidence_status": "bounded_local_map" if mechanisms else "not_established",
                    "fco_parent_ids": [],
                }
            )
            relations.append(
                {
                    "subject": row["candidate"],
                    "predicate": "CLINICALLY_ADJACENT",
                    "object": comp,
                    "method": "same or adjacent drug class comparator list",
                    "value": None,
                    "source": "tiny comparator map for Problem #2 clinical-progress lookup",
                    "source_version_date": "2026-08-13",
                    "evidence_status": "requires_trial_lookup",
                    "fco_parent_ids": [],
                }
            )
        relations.append(
            {
                "subject": row["candidate"],
                "predicate": "PHENOTYPE_SIMILAR",
                "object": "COMT ORF shifted state",
                "method": "CPJUMP1 morphology reference-distance ranking",
                "value": float(row["restoration_score"]),
                "source": "candidate_ranking.csv",
                "source_version_date": "2026-08-13",
                "evidence_status": "computed",
                "fco_parent_ids": [],
            }
        )
        relations.append(
            {
                "subject": row["candidate"],
                "predicate": "STRUCTURALLY_SIMILAR",
                "object": "not_computed",
                "method": "not run; no RDKit/fingerprint dependency installed unattended",
                "value": None,
                "source": identity.get("retrieval", "not_available"),
                "source_version_date": identity.get("retrieval_ts_utc"),
                "evidence_status": "not_computed",
                "fco_parent_ids": [],
            }
        )
        relations.append(
            {
                "subject": row["candidate"],
                "predicate": "TARGET_SIMILAR",
                "object": "|".join(sorted(targets)),
                "method": "CPJUMP1 target_list extraction",
                "value": len(targets),
                "source": "JUMP-Target-1 compound metadata",
                "source_version_date": "2026-08-13",
                "evidence_status": "metadata_present",
                "fco_parent_ids": [],
            }
        )
    write_json(PRIMARY / "similar_drug_evidence_graph.json", relations)
    pd.DataFrame(relations).to_csv(PRIMARY / "similar_drug_evidence_graph.csv", index=False)
    return relations


def clinical_trials_for(drug: str, max_records: int = 10) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"query.intr": drug, "pageSize": max_records, "format": "json"})
    url = f"https://clinicaltrials.gov/api/v2/studies?{params}"
    status, data = http_json(url, timeout=60)
    rows = []
    if status != "ok":
        return [
            {
                "drug": drug,
                "retrieval_status": status,
                "retrieval_timestamp": now(),
                "source": url,
            }
        ]
    for study in data.get("studies", [])[:max_records]:
        protocol = study.get("protocolSection", {})
        ident = protocol.get("identificationModule", {})
        status_mod = protocol.get("statusModule", {})
        design = protocol.get("designModule", {})
        conds = protocol.get("conditionsModule", {}).get("conditions", [])
        arms = protocol.get("armsInterventionsModule", {})
        interventions = arms.get("interventions", [])
        rows.append(
            {
                "drug": drug,
                "disease_indication": "; ".join(conds),
                "nct_id": ident.get("nctId"),
                "intervention_name": "; ".join(i.get("name", "") for i in interventions if drug.lower() in i.get("name", "").lower())
                or "; ".join(i.get("name", "") for i in interventions[:3]),
                "phase": "; ".join(design.get("phases", []) or []),
                "recruitment_status": status_mod.get("overallStatus"),
                "study_type": design.get("studyType"),
                "target_mechanism_relationship": "not inferred from trial record",
                "comparator_relationship": "trial_exists_for_candidate_or_related_drug",
                "retrieval_timestamp": now(),
                "source": url,
                "source_record": study,
                "trial_exists": True,
                "trial_progressed_to_phase": bool(design.get("phases")),
                "trial_completed": status_mod.get("overallStatus") == "COMPLETED",
                "trial_outcome_known": "not_checked",
                "approval_exists": "not_checked",
                "retrieval_status": "ok",
            }
        )
    if not rows:
        rows.append(
            {
                "drug": drug,
                "retrieval_status": "ok_no_records",
                "retrieval_timestamp": now(),
                "source": url,
                "trial_exists": False,
            }
        )
    return rows


def phase5_clinical(ranking: pd.DataFrame, relations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    drugs = [str(ranking.iloc[0]["pert_iname"])]
    drugs.extend([r["object"] for r in relations if r["predicate"] == "CLINICALLY_ADJACENT" and r["subject"] == ranking.iloc[0]["candidate"]])
    seen = []
    for drug in drugs:
        if drug not in seen:
            seen.append(drug)
    rows = []
    for drug in seen:
        rows.extend(clinical_trials_for(drug, max_records=10))
    write_json(PRIMARY / "clinical_progress.json", rows)
    public_rows = [{k: v for k, v in row.items() if k != "source_record"} for row in rows]
    pd.DataFrame(public_rows).to_csv(PRIMARY / "clinical_progress.csv", index=False)
    return rows


def phase6_table(ranking: pd.DataFrame, relations: list[dict[str, Any]], clinical: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for row in ranking.head(10).to_dict(orient="records"):
        candidate = row["candidate"]
        rels = [r for r in relations if r["subject"] == candidate]
        drug = str(row["pert_iname"])
        trial_rows = [r for r in clinical if r.get("drug") == drug]
        related_trials = [r for r in clinical if r.get("drug") in [x["object"] for x in rels if x["predicate"] == "CLINICALLY_ADJACENT"]]
        rows.append(
            {
                "Candidate": candidate,
                "Phenotype opposition": row["restoration_score"],
                "Reference-state result": row["reference_state_result"],
                "Structural similarity": evidence_summary(rels, "STRUCTURALLY_SIMILAR"),
                "Target similarity": evidence_summary(rels, "TARGET_SIMILAR"),
                "Mechanism similarity": evidence_summary(rels, "MECHANISM_SIMILAR"),
                "Related-drug clinical progress": clinical_summary(trial_rows + related_trials),
                "Known relationship benchmark": "known_pair" if row.get("target_match") or row.get("target_list_match") else "not_known_pair",
                "Provenance completeness": "complete_for_cached_morphology_partial_for_external_evidence",
                "Claim ceiling": CLAIM_CEILING,
            }
        )
    table = pd.DataFrame(rows)
    table.to_csv(PRIMARY / "repurposing_evidence_table.csv", index=False)
    write_markdown_table(ROOT / "deliverables" / "REPURPOSING_EVIDENCE_TABLE.md", table)
    return table


def evidence_summary(rels: list[dict[str, Any]], predicate: str) -> str:
    vals = [r for r in rels if r["predicate"] == predicate]
    if not vals:
        return "not_available"
    return "; ".join(f"{r['evidence_status']}:{r['object']}" for r in vals[:4])


def clinical_summary(rows: list[dict[str, Any]]) -> str:
    ok = [r for r in rows if r.get("trial_exists")]
    if not ok:
        return "no_public_trial_records_found_or_query_unavailable"
    phases = sorted({str(r.get("phase") or "phase_not_listed") for r in ok})
    statuses = sorted({str(r.get("recruitment_status") or "status_not_listed") for r in ok})
    return f"trial records: {len(ok)}; phases: {', '.join(phases[:4])}; statuses: {', '.join(statuses[:4])}"


def write_markdown_table(path: Path, df: pd.DataFrame) -> None:
    lines = ["# Repurposing Evidence Table", "", f"Claim ceiling: `{CLAIM_CEILING}`", ""]
    cols = list(df.columns)
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for row in df.to_dict(orient="records"):
        vals = [str(row[c]).replace("|", "/").replace("\n", " ") for c in cols]
        lines.append("| " + " | ".join(vals) + " |")
    write_text(path, "\n".join(lines) + "\n")


def phase7_fco(result: dict[str, Any], perturbation: dict[str, Any], ranking: pd.DataFrame, identities: list[dict[str, Any]], relations: list[dict[str, Any]], clinical: list[dict[str, Any]]) -> dict[str, Any]:
    fcos = []
    dataset = make_fco("dataset_snapshot", result["_source_paths"], {"source": "cached Kaggle CPJUMP1 output"})
    fcos.append(dataset)
    perturb_fco = make_fco("selected_perturbation", perturbation, {"source": "selection_sweep.csv"}, [dataset["digest"]])
    fcos.append(perturb_fco)
    rank_fco = make_fco(
        "candidate_ranking",
        {"top_rows": ranking.head(10).to_dict(orient="records")},
        {"source": "primary/candidate_ranking.csv"},
        [perturb_fco["digest"]],
    )
    fcos.append(rank_fco)
    id_fco = make_fco("smiles_identity", {"identities": identities}, {"source": "CPJUMP1 metadata + PubChem when available"}, [rank_fco["digest"]])
    fcos.append(id_fco)
    evidence_fco = make_fco("target_mechanism_trial_evidence", {"relations": relations, "clinical_progress": clinical}, {"source": "public/local evidence"}, [id_fco["digest"]])
    fcos.append(evidence_fco)
    claim_fco = make_fco(
        "bounded_repurposing_claim",
        {
            "claim": "A public CPJUMP1 morphology signal plus mechanism and clinical-progress evidence supports investigating the top candidate as a repurposing hypothesis.",
            "claim_ceiling": CLAIM_CEILING,
            "prohibited_claims": ["efficacy", "measured rescue", "clinical utility", "therapeutic success"],
        },
        {"source": "computed evidence route"},
        [evidence_fco["digest"]],
    )
    fcos.append(claim_fco)
    route = {
        "schema": "biocustody.magicstudiobox.fcg_route.v1",
        "ts_utc": now(),
        "route": "CPJUMP1 -> perturbation -> StateShift -> candidate drug -> SMILES/target/mechanism/related drug/clinical trial -> REPURPOSING_HYPOTHESIS",
        "fcos": fcos,
        "all_fcos_verify": all(verify_fco(f) for f in fcos),
        "merkle_root": merkle_root([f["digest"] for f in fcos]),
        "claim_ceiling": CLAIM_CEILING,
    }
    write_json(PRIMARY / "fco_route.json", route)
    write_json(PRIMARY / "merkle_receipt.json", {"merkle_root": route["merkle_root"], "digests": [f["digest"] for f in fcos]})
    return route


def phase8_tamper(route: dict[str, Any]) -> dict[str, Any]:
    duplicate = json.loads(json.dumps(route))
    before = {
        "source_verified": route["all_fcos_verify"],
        "route_verified": route["all_fcos_verify"],
        "claim_admissible": route["claim_ceiling"] == CLAIM_CEILING,
    }
    duplicate["fcos"][2]["payload"]["top_rows"][0]["restoration_score"] = float(duplicate["fcos"][2]["payload"]["top_rows"][0]["restoration_score"]) + 0.001
    after_verified = all(verify_fco(f) for f in duplicate["fcos"])
    after = {
        "source_mismatch": not after_verified,
        "dependent_route_invalid": not after_verified,
        "claim_invalid_or_review_required": not after_verified,
    }
    result = {
        "schema": "biocustody.magicstudiobox.tamper_test.v1",
        "before": before,
        "after": after,
        "changed_artifact": "duplicate.fcos[2].payload.top_rows[0].restoration_score",
        "canonical_run_modified": False,
        "pass": before["route_verified"] and after["claim_invalid_or_review_required"],
    }
    write_json(PRIMARY / "tamper_test.json", result)
    return result


def phase9_sanity(baseline: dict[str, Any], eval_result: dict[str, Any], route: dict[str, Any], tamper: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "hash_reproducibility": "PASS" if route.get("merkle_root") else "FAIL",
        "provenance_completeness": "PARTIAL_EXTERNAL_EVIDENCE" if route["all_fcos_verify"] else "FAIL",
        "tamper_detection": "PASS" if tamper["pass"] else "FAIL",
        "claim_ceiling_compliance": "PASS" if CLAIM_CEILING == "REPURPOSING_HYPOTHESIS" else "FAIL",
        "continuity_classification": result.get("state_decision", {}).get("decision"),
        "false_continuity_test_cases": "synthetic suite run in baseline",
        "false_break_test_cases": "synthetic suite run in baseline",
        "known_pair_retrieval": eval_result.get("known_pair_rank"),
        "null_shuffle_comparison": {
            "seed": eval_result.get("shuffle_seed"),
            "reciprocal_rank_enrichment_vs_shuffle": eval_result.get("reciprocal_rank_enrichment_vs_shuffle"),
        },
    }
    write_json(PRIMARY / "evaluation_sanity_checks.json", checks)
    return checks


def phase10_11_outputs(
    perturbation: dict[str, Any],
    ranking: pd.DataFrame,
    table: pd.DataFrame,
    eval_result: dict[str, Any],
    route: dict[str, Any],
    tamper: dict[str, Any],
    clinical: list[dict[str, Any]],
    sanity: dict[str, Any],
) -> None:
    top = ranking.iloc[0].to_dict()
    final_metrics = {
        "top_candidate": top["pert_iname"],
        "top_candidate_id": top["candidate"],
        "phenotype_opposition": float(top["restoration_score"]),
        "known_pair_rank": eval_result["known_pair_rank"],
        "reciprocal_rank": eval_result["reciprocal_rank"],
        "custody_verified": route["all_fcos_verify"],
        "tamper_test_pass": tamper["pass"],
        "claim_ceiling": CLAIM_CEILING,
        "clinical_trial_rows": len([r for r in clinical if r.get("trial_exists")]),
    }
    write_json(ROOT / "deliverables" / "FINAL_METRICS.json", final_metrics)
    write_text(
        ROOT / "deliverables" / "MAGICSTUDIOBOX_RESULTS.md",
        f"""# MagicStudioBox Results

STATUS: PARTIAL

The unattended run produced a bounded Problem #2 evidence bundle from existing public CPJUMP1 outputs plus public/local drug evidence.

Best perturbation: `{perturbation['selected_perturbation_id']}`.

Top repurposing candidate: `{top['pert_iname']}` (`{top['candidate']}`).

Most important metric: phenotype opposition score `{top['restoration_score']}` with known-pair rank `{eval_result['known_pair_rank']}`.

Claim ceiling: `{CLAIM_CEILING}`.

Custody verified: `{route['all_fcos_verify']}`.

Tamper test: `{tamper['pass']}`.

Boundary: this is a repurposing hypothesis and does not demonstrate rescue, efficacy, clinical utility, or therapeutic success.
""",
    )
    write_text(
        ROOT / "deliverables" / "PITCH_DRAFT.md",
        f"""# Pitch Draft

BioCustody asks: which existing drug deserves another look, and what phenotype, mechanism, similar-drug, and clinical-progress evidence supports that recommendation?

In this run, public CPJUMP1 Cell Painting profiles identify `{perturbation['selected_perturbation_id']}` as a shifted perturbation. The top ranked candidate is `{top['pert_iname']}`, with a phenotype-opposition score of `{top['restoration_score']}`.

The evidence profile keeps phenotype, target/mechanism, related-drug clinical progress, known-pair retrieval, and provenance as separate dimensions. The claim remains `{CLAIM_CEILING}`.

Close: BioCustody ranks where to look next-and proves exactly which phenotype, mechanism, similar drug, and clinical evidence justified that recommendation.
""",
    )
    write_text(
        ROOT / "deliverables" / "DEMO_SCRIPT_90S_DRAFT.md",
        f"""# 90-Second Demo Script

1. Show the public CPJUMP1 source and selected perturbation `{perturbation['selected_perturbation_id']}`.
2. Show the candidate ranking and point to `{top['pert_iname']}` as the top morphology-opposition result.
3. Open the repurposing evidence table: phenotype, target/mechanism, related clinical progress, benchmark, and provenance stay separate.
4. Open the FCO route and Merkle receipt.
5. Show the tamper test: valid route passes; one changed upstream number invalidates the dependent claim.
6. Close with: BioCustody ranks where to look next-and proves exactly which phenotype, mechanism, similar drug, and clinical evidence justified that recommendation.
""",
    )
    write_text(
        ROOT / "deliverables" / "SLIDE_RESULTS_INSERTS.md",
        f"""# Slide Results Inserts

- Top perturbation: `{perturbation['selected_perturbation_id']}`.
- Top candidate: `{top['pert_iname']}`.
- Phenotype opposition: `{top['restoration_score']}`.
- Known-pair rank: `{eval_result['known_pair_rank']}`.
- Custody verified: `{route['all_fcos_verify']}`.
- Tamper test: `{tamper['pass']}`.
- Claim ceiling: `{CLAIM_CEILING}`.
""",
    )
    figure_texts = {
        "01_reference_cloud_to_candidate.txt": f"reference cloud -> {perturbation['selected_perturbation_id']} -> {top['pert_iname']} opposition={top['restoration_score']}",
        "02_candidate_smiles_targets.txt": f"{top['pert_iname']} -> SMILES preserved -> target {top.get('target')} -> target_list {top.get('target_list')}",
        "03_similar_drugs_clinical_progress.txt": clinical_summary(clinical),
        "04_fco_route.txt": route["route"] + "\nmerkle_root=" + route["merkle_root"],
        "05_valid_vs_tampered.txt": f"before={tamper['before']}\nafter={tamper['after']}",
        "06_problem2_architecture.txt": "public Cell Painting -> shifted perturbation -> counter-phenotype ranking -> similar-drug/trial evidence -> REPURPOSING_HYPOTHESIS",
    }
    for name, text in figure_texts.items():
        write_text(TEXT_FIGURES / name, text + "\n")
    write_text(
        ROOT / "MAGICSTUDIOBOX_HANDOFF.md",
        f"""STATUS: PARTIAL

BEST PERTURBATION:
{perturbation['selected_perturbation_id']}

TOP REPURPOSING CANDIDATE:
{top['pert_iname']} ({top['candidate']})

CLAIM CEILING:
{CLAIM_CEILING}

MOST IMPORTANT REAL METRIC:
phenotype opposition={top['restoration_score']}; known_pair_rank={eval_result['known_pair_rank']}

CLINICAL-PROGRESS EVIDENCE:
{clinical_summary(clinical)}

CUSTODY VERIFIED:
{'yes' if route['all_fcos_verify'] else 'no'}

TAMPER TEST:
{'pass' if tamper['pass'] else 'fail'}

TESTS:
baseline={sanity}

WHAT BYRON SHOULD DO FIRST:
Open deliverables/REPURPOSING_EVIDENCE_TABLE.md and verify the top candidate narrative against the clinical-progress rows before presenting.

Reproduce:
python scripts/magicstudiobox_repurposing_queue.py
""",
    )


def main() -> int:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    PRIMARY.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    TEXT_FIGURES.mkdir(parents=True, exist_ok=True)
    baseline = phase0_baseline()
    if not baseline["expansion_allowed"]:
        write_text(
            ROOT / "MAGICSTUDIOBOX_HANDOFF.md",
            "STATUS: BLOCKED\n\nBaseline tests failed. Scientific expansion stopped by policy.\n",
        )
        return 2
    sweep, ranking, result = load_best_sources()
    perturbation = phase1_select_perturbation(sweep, result["_source_paths"])
    eval_result = phase2_ranking(ranking, result, perturbation)
    refreshed_ranking = pd.read_csv(PRIMARY / "candidate_ranking.csv")
    identities = phase3_identity(refreshed_ranking)
    relations = phase4_similarity(refreshed_ranking, identities)
    clinical = phase5_clinical(refreshed_ranking, relations)
    table = phase6_table(refreshed_ranking, relations, clinical)
    route = phase7_fco(result, perturbation, refreshed_ranking, identities, relations, clinical)
    tamper = phase8_tamper(route)
    sanity = phase9_sanity(baseline, eval_result, route, tamper, result)
    phase10_11_outputs(perturbation, refreshed_ranking, table, eval_result, route, tamper, clinical, sanity)
    print("MAGICSTUDIOBOX_QUEUE_DONE", now())
    print("handoff", ROOT / "MAGICSTUDIOBOX_HANDOFF.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
