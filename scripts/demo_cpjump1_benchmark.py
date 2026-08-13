#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path
import json
import hashlib

import numpy as np
import pandas as pd

from biocustody.fco import make_fco, verify_fco
from biocustody.merkle import merkle_root_hex
from biocustody.state import ReferenceStateModel


ROOT = Path(__file__).resolve().parents[1]
S3 = "https://cellpainting-gallery.s3.amazonaws.com"
BATCH = "2020_11_04_CPJUMP1"
COMPOUND_PLATE = "BR00116991"
ORF_PLATE = "BR00117006"
BENCHMARK_GENE = "KCNN4"
MAX_FEATURES = 96
CANDIDATE_LIMIT = 50
CALCULATION_VERSION = "bio-delta-g-restoration-v0.1"

OUT_DIR = ROOT / "data/external/cpjump1_tiny"
RUN_DIR = ROOT / "runs/local"


def s3_url(key: str) -> str:
    return f"{S3}/{key}"


def key(*parts: str) -> str:
    return "/".join(("cpg0000-jump-pilot", "source_4", *parts))


def read_tsv_from_s3(path: str) -> pd.DataFrame:
    return pd.read_csv(s3_url(path), sep="\t")


def read_csv_from_s3(path: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(s3_url(path), **kwargs)


def profile_key(plate: str) -> str:
    return key("workspace", "backend", BATCH, plate, f"{plate}.csv")


def choose_feature_columns(profile_path: str) -> list[str]:
    columns = list(read_csv_from_s3(profile_path, nrows=0).columns)
    features = [c for c in columns if not c.startswith("Metadata_")]
    return features[:MAX_FEATURES]


def load_plate_profiles(plate: str, feature_cols: list[str]) -> pd.DataFrame:
    cols = ["Metadata_Plate", "Metadata_Well", *feature_cols]
    df = read_csv_from_s3(profile_key(plate), usecols=cols)
    df["Metadata_Well"] = df["Metadata_Well"].astype(str)
    return df


def load_labeled_profiles(plate: str, plate_map_name: str, feature_cols: list[str]) -> pd.DataFrame:
    profiles = load_plate_profiles(plate, feature_cols)
    platemap = read_tsv_from_s3(
        key("workspace", "metadata", "platemaps", BATCH, "platemap", f"{plate_map_name}.txt")
    )
    platemap = platemap.rename(columns={"well_position": "Metadata_Well"})
    labeled = profiles.merge(platemap, on="Metadata_Well", how="left")
    labeled["assay_plate_barcode"] = plate
    labeled["plate_map_name"] = plate_map_name
    return labeled


def prepare_subset() -> tuple[pd.DataFrame, list[str]]:
    compound_path = profile_key(COMPOUND_PLATE)
    feature_cols = choose_feature_columns(compound_path)

    compound = load_labeled_profiles(COMPOUND_PLATE, "JUMP-Target-1_compound_platemap", feature_cols)
    compound_meta = read_tsv_from_s3(
        key("workspace", "metadata", "external_metadata", "JUMP-Target-1_compound_metadata_targets.tsv")
    )
    compound = compound.merge(compound_meta, on="broad_sample", how="left")
    compound["perturbation_kind"] = "compound"
    compound["benchmark_label"] = compound["pert_iname"].fillna(compound["broad_sample"])
    compound["gene"] = np.nan

    orf = load_labeled_profiles(ORF_PLATE, "JUMP-Target-1_orf_platemap", feature_cols)
    orf_meta = read_tsv_from_s3(
        key("workspace", "metadata", "external_metadata", "JUMP-Target-1_orf_metadata.tsv")
    )
    orf = orf.merge(orf_meta, on="broad_sample", how="left")
    orf["perturbation_kind"] = "orf"
    orf["benchmark_label"] = orf["gene"].fillna(orf["broad_sample"])
    orf["target"] = orf["gene"]
    orf["pert_iname"] = orf["gene"]
    orf["smiles"] = np.nan

    keep_cols = [
        "assay_plate_barcode",
        "plate_map_name",
        "Metadata_Plate",
        "Metadata_Well",
        "perturbation_kind",
        "broad_sample",
        "benchmark_label",
        "pert_iname",
        "target",
        "gene",
        "pert_type",
        "control_type",
        "smiles",
        *feature_cols,
    ]
    subset = pd.concat([compound[keep_cols], orf[keep_cols]], ignore_index=True)
    return subset, feature_cols


def is_control(df: pd.DataFrame) -> pd.Series:
    broad = df["broad_sample"].fillna("").astype(str).str.strip()
    pert_type = df["pert_type"].fillna("").astype(str).str.strip()
    control_type = df["control_type"].fillna("").astype(str).str.strip()
    return (broad == "") | (pert_type == "control") | (control_type != "")


def numeric_matrix(df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    values = df[feature_cols].apply(pd.to_numeric, errors="coerce")
    values = values.replace([np.inf, -np.inf], np.nan)
    return values


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def pathway_for_target(target: str) -> str:
    pathway_map = {
        "KCNN4": "potassium ion transport / calcium-activated potassium channel activity",
        "KCNMA1": "potassium ion transport / calcium-activated potassium channel activity",
        "CACNB4": "calcium channel regulation",
        "CACNA2D3": "calcium channel regulation",
        "CA5A": "carbonic anhydrase / pH homeostasis",
        "AKR1C1": "steroid metabolism",
        "NTRK1": "neurotrophin receptor signaling",
        "CDK4": "cell-cycle regulation",
        "DDR2": "receptor tyrosine kinase signaling",
    }
    return pathway_map.get(str(target), "target annotation present; pathway not curated in tiny MVP map")


def bio_delta_g_claim(shifted: bool, restoration_supported: bool) -> str:
    if restoration_supported:
        return "PREDICTED_PHENOTYPIC_RESTORATION"
    if shifted:
        return "PERTURBATION_DIFFERS_FROM_CONTROL"
    return "OBSERVED_PROFILE"


def run_benchmark() -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    subset, feature_cols = prepare_subset()
    subset_path = OUT_DIR / f"{COMPOUND_PLATE}_{ORF_PLATE}_{BENCHMARK_GENE}_profiles.csv"
    subset.to_csv(subset_path, index=False)
    subset_digest = file_sha256(subset_path)

    values = numeric_matrix(subset, feature_cols)
    control_mask = is_control(subset)
    gene_mask = (
        (subset["perturbation_kind"] == "orf")
        & (subset["gene"].fillna("") == BENCHMARK_GENE)
        & ~control_mask
    )
    compound_mask = (
        (subset["perturbation_kind"] == "compound")
        & (subset["pert_type"].fillna("") == "trt")
        & subset["pert_iname"].notna()
    )

    usable = values.loc[control_mask | gene_mask | compound_mask].notna().all(axis=0)
    usable_features = list(usable[usable].index)
    if len(usable_features) < 4:
        raise RuntimeError("Too few finite CPJUMP1 features for benchmark.")

    controls = values.loc[control_mask, usable_features]
    gene_profile = values.loc[gene_mask, usable_features].median(axis=0)
    compound_profiles = values.loc[compound_mask, usable_features].copy()
    compound_meta = subset.loc[
        compound_mask,
        ["Metadata_Well", "broad_sample", "pert_iname", "target", "smiles"],
    ].copy()

    if len(controls) < 4:
        raise RuntimeError("Too few CPJUMP1 control wells for reference-state model.")
    if gene_profile.isna().any():
        raise RuntimeError(f"No complete ORF profile found for {BENCHMARK_GENE}.")

    model = ReferenceStateModel(quantile=0.95, max_components=12).fit(controls.to_numpy())
    decision = model.decide(gene_profile.to_numpy())
    perturbation_distance = float(np.sqrt(max(decision.distance2, 0.0)))
    reference_mean = controls.mean(axis=0)
    reference_variance = controls.var(axis=0, ddof=1)

    candidate_vectors = {}
    metadata_by_candidate = {}
    grouped = compound_profiles.join(compound_meta).groupby(
        ["broad_sample", "pert_iname", "target"],
        dropna=True,
        sort=False,
    )
    for (broad_sample, pert_iname, target), group in grouped:
        label = f"{pert_iname}|{target}|{broad_sample}"
        candidate_vectors[label] = group[usable_features].median(axis=0).to_numpy(dtype=float)
        smiles_values = group["smiles"].dropna().unique()
        well_values = sorted(group["Metadata_Well"].dropna().astype(str).unique())
        metadata_by_candidate[label] = {
            "broad_sample": broad_sample,
            "pert_iname": pert_iname,
            "target": target,
            "target_match": bool(target == BENCHMARK_GENE),
            "plate": COMPOUND_PLATE,
            "wells": well_values,
            "smiles": str(smiles_values[0]) if len(smiles_values) else None,
            "pathway": pathway_for_target(target),
        }

    target_match_labels = [k for k, v in metadata_by_candidate.items() if v["target_match"]]
    other_labels = [k for k in candidate_vectors if k not in set(target_match_labels)]
    selected_labels = (target_match_labels + other_labels)[:CANDIDATE_LIMIT]

    rows = []
    for label in selected_labels:
        candidate_distance2 = model.distance2(candidate_vectors[label])
        candidate_distance = float(np.sqrt(max(candidate_distance2, 0.0)))
        restoration_score = 1.0 - (candidate_distance / (perturbation_distance + 1e-12))
        rows.append(
            {
                "candidate": label,
                "candidate_distance": candidate_distance,
                "candidate_distance2": float(candidate_distance2),
                "perturbation_distance": perturbation_distance,
                "restoration_score": float(restoration_score),
                "distance_ratio": float(candidate_distance / (perturbation_distance + 1e-12)),
            }
        )
    ranking = pd.DataFrame(rows).sort_values(
        ["restoration_score", "candidate_distance"],
        ascending=[False, True],
    ).reset_index(drop=True)
    meta_df = pd.DataFrame.from_dict(metadata_by_candidate, orient="index")
    ranking = ranking.join(meta_df, on="candidate")
    ranking["benchmark_gene"] = BENCHMARK_GENE

    top = ranking.iloc[0]
    target_matches = ranking[ranking["target_match"]].copy()
    top_target_match = target_matches.iloc[0].to_dict() if len(target_matches) else None

    shifted = decision.decision == "TRANSITION"
    ceiling = bio_delta_g_claim(
        shifted=shifted,
        restoration_supported=shifted and float(top["restoration_score"]) > 0.0,
    )
    evidence_graph = {
        "nodes": [
            {
                "id": f"compound:{top['broad_sample']}",
                "type": "compound",
                "label": top["pert_iname"],
                "smiles": top["smiles"],
                "source": "JUMP-Target-1_compound_metadata_targets.tsv",
            },
            {
                "id": f"target:{top['target']}",
                "type": "target",
                "label": top["target"],
                "source": "JUMP-Target-1_compound_metadata_targets.tsv",
            },
            {
                "id": f"pathway:{top['pathway']}",
                "type": "pathway",
                "label": top["pathway"],
                "source": "tiny local Bio-Delta-G MVP pathway map",
            },
            {
                "id": f"perturbation:{BENCHMARK_GENE}",
                "type": "orf_perturbation",
                "label": BENCHMARK_GENE,
                "source": "JUMP-Target-1_orf_metadata.tsv",
            },
        ],
        "edges": [
            {
                "source": f"compound:{top['broad_sample']}",
                "target": f"target:{top['target']}",
                "predicate": "annotated_target",
                "evidence": "public CPJUMP1 compound target metadata",
            },
            {
                "source": f"target:{top['target']}",
                "target": f"pathway:{top['pathway']}",
                "predicate": "mapped_to_pathway_family",
                "evidence": "small local demo map; not a comprehensive pathway database",
            },
            {
                "source": f"perturbation:{BENCHMARK_GENE}",
                "target": f"pathway:{pathway_for_target(BENCHMARK_GENE)}",
                "predicate": "mapped_to_pathway_family",
                "evidence": "small local demo map; not a comprehensive pathway database",
            },
        ],
    }

    p_control = model.transform(controls.to_numpy())[:, :2]
    p_gene = model.transform(gene_profile.to_numpy())[0, :2]
    top_candidate_profiles = np.vstack([candidate_vectors[label] for label in ranking["candidate"].head(10)])
    p_candidates = model.transform(top_candidate_profiles)[:, :2]
    plot_points = {
        "controls": [{"x": float(x), "y": float(y)} for x, y in p_control],
        "perturbation": {"x": float(p_gene[0]), "y": float(p_gene[1]), "label": BENCHMARK_GENE},
        "candidates": [
            {
                "x": float(x),
                "y": float(y),
                "label": str(row["pert_iname"]),
                "restoration_score": float(row["restoration_score"]),
            }
            for (x, y), (_, row) in zip(p_candidates, ranking.head(10).iterrows())
        ],
    }

    source = {
        "public_data": True,
        "contains_phi": False,
        "access_restricted": False,
        "usage_rights_verified": True,
        "source": "Cell Painting Gallery CPJUMP1 pilot public S3",
        "source_record_id": f"{BATCH}:{COMPOUND_PLATE}+{ORF_PLATE}:{BENCHMARK_GENE}",
        "license_or_terms": "public Cell Painting Gallery data; terms not reinterpreted by this script",
        "subset_path": str(subset_path.relative_to(ROOT)),
        "subset_sha256": subset_digest,
        "records": {
            "compound_plate": COMPOUND_PLATE,
            "perturbation_plate": ORF_PLATE,
            "perturbation_gene": BENCHMARK_GENE,
            "top_candidate_wells": top["wells"],
        },
    }
    fco = make_fco(
        "bio_delta_g_phenotypic_restoration_ranking",
        payload={
            "benchmark_gene": BENCHMARK_GENE,
            "top_candidate": top["candidate"],
            "top_candidate_target": top["target"],
            "top_candidate_target_match": bool(top["target_match"]),
            "top_restoration_score": float(top["restoration_score"]),
            "top_candidate_distance": float(top["candidate_distance"]),
            "perturbation_distance": perturbation_distance,
            "top_target_match": top_target_match,
            "plate_count": 2,
            "subset_rows": int(len(subset)),
            "feature_count": int(len(usable_features)),
        },
        source=source,
        claim={"claim_ceiling": ceiling},
        transformation={
            "algorithm": "Bio-Delta-G restoration score: 1 - D(candidate, reference) / (D(perturbation, reference) + epsilon)",
            "reference_state": "mean/variance and covariance model of public CPJUMP1 control wells from selected compound and ORF plates",
            "perturbed_state": f"median ORF profile for {BENCHMARK_GENE}",
            "candidate_profiles": "median compound well profiles grouped by broad_sample, pert_iname, target",
            "state_model": "median/MAD -> PCA -> LedoitWolf -> empirical q95",
            "calculation_version": CALCULATION_VERSION,
            "benchmark_boundary": "independent morphology restoration-distance ranking only; not measured rescue",
        },
    )
    from dataclasses import replace

    tampered = replace(
        fco,
        payload={
            **fco.payload,
            "top_restoration_score": float(fco.payload["top_restoration_score"]) + 0.001,
        },
    )

    result = {
        "benchmark": {
            "name": "Bio-Delta-G CPJUMP1 phenotypic restoration MVP",
            "dataset": "CPJUMP1 pilot",
            "batch": BATCH,
            "compound_plate": COMPOUND_PLATE,
            "perturbation_plate": ORF_PLATE,
            "benchmark_gene": BENCHMARK_GENE,
            "subset_path": str(subset_path.relative_to(ROOT)),
            "subset_sha256": subset_digest,
            "subset_rows": int(len(subset)),
            "control_rows": int(control_mask.sum()),
            "compound_candidate_count": int(len(selected_labels)),
            "feature_count": int(len(usable_features)),
            "calculation_version": CALCULATION_VERSION,
        },
        "reference_state": {
            "replicate_count": int(len(controls)),
            "mean_first_10_features": reference_mean.head(10).to_dict(),
            "variance_first_10_features": reference_variance.head(10).to_dict(),
        },
        "state_decision": decision.__dict__,
        "ranking": ranking.head(25).to_dict(orient="records"),
        "evidence_graph": evidence_graph,
        "plot_points": plot_points,
        "claim_ceiling": ceiling,
        "fco": fco.as_dict(),
        "fco_verifies": verify_fco(fco),
        "tamper_demo": {
            "changed_field": "payload.top_restoration_score",
            "verifies_after_tamper": verify_fco(tampered),
        },
        "merkle_root": merkle_root_hex([fco.digest]),
    }

    result_path = RUN_DIR / "cpjump1_benchmark_result.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("\nBIO-DELTA-G CPJUMP1 PHENOTYPIC RESTORATION BENCHMARK")
    print(f"Dataset: {BATCH}")
    print(f"Compound plate: {COMPOUND_PLATE}")
    print(f"Perturbation/ORF plate: {ORF_PLATE}")
    print(f"Perturbed state: {BENCHMARK_GENE}")
    print(f"Subset: {subset_path}")
    print(f"Rows={len(subset)} controls={int(control_mask.sum())} features={len(usable_features)}")
    print(f"Perturbation decision: {decision.decision}")
    print(f"D={perturbation_distance:.3f} D^2={decision.distance2:.3f} threshold^2={decision.threshold2:.3f}")
    print("\nTOP RANKED COMPOUNDS BY RETURN-TOWARD-REFERENCE SCORE")
    show_cols = ["candidate", "target", "target_match", "restoration_score", "candidate_distance", "distance_ratio"]
    print(ranking[show_cols].head(12).to_string(index=False))
    print("\nTOP CLAIM")
    print("Claim ceiling:", ceiling)
    print("FCO:", fco.digest)
    print("FCO verifies:", verify_fco(fco))
    print("Tampered FCO verifies:", verify_fco(tampered))
    print("Merkle root:", result["merkle_root"])
    print("\nWrote", result_path)
    return result


if __name__ == "__main__":
    run_benchmark()
