#!/usr/bin/env python
from pathlib import Path
import json
import pandas as pd
import numpy as np

from biocustody.state import ReferenceStateModel
from biocustody.opposition import rank_counter_perturbations
from biocustody.claims import claim_ceiling
from biocustody.fco import make_fco, verify_fco
from biocustody.merkle import merkle_root_hex

ROOT = Path(__file__).resolve().parents[1]

controls = pd.read_csv(ROOT / "data/synthetic/controls.csv")
perturb = pd.read_csv(ROOT / "data/synthetic/perturbation.csv").iloc[0]
cand_df = pd.read_csv(ROOT / "data/synthetic/candidates.csv")

model = ReferenceStateModel(quantile=0.95, max_components=6).fit(controls.values)
decision = model.decide(perturb.values)

reference = controls.median(axis=0).values
candidates = {
    row["candidate"]: row[controls.columns].to_numpy(dtype=float)
    for _, row in cand_df.iterrows()
}
ranking = rank_counter_perturbations(reference, perturb.values, candidates)

top = ranking.iloc[0]
ceiling = claim_ceiling(
    profile_observed=True,
    perturbation_detected=(decision.decision == "TRANSITION"),
    opposition_supported=(top["opposition_score"] > 0.5),
    target_evidence=False,
)

source = {
    "public_data": True,
    "contains_phi": False,
    "access_restricted": False,
    "usage_rights_verified": True,
    "source": "repo synthetic demo",
    "source_record_id": top["candidate"],
    "license_or_terms": "generated test data",
}
fco = make_fco(
    "candidate_ranking",
    payload={
        "candidate": top["candidate"],
        "opposition_score": float(top["opposition_score"]),
        "reference_state_distance": float(top["distance_to_reference"]),
    },
    source=source,
    claim={"claim_ceiling": ceiling},
    transformation={
        "algorithm": "negative cosine opposition",
        "state_model": "median/MAD -> PCA -> LedoitWolf -> empirical q95",
    },
)

print("\nREFERENCE STATE")
print(f"Perturbation decision: {decision.decision}")
print(f"D^2={decision.distance2:.3f} threshold={decision.threshold2:.3f}")

print("\nCOUNTER-PERTURBATION RANKING")
print(ranking.to_string(index=False))

print("\nTOP CLAIM")
print("Claim ceiling:", ceiling)
print("FCO:", fco.digest)
print("FCO verifies:", verify_fco(fco))
print("Merkle root:", merkle_root_hex([fco.digest]))

out = ROOT / "runs/local/synthetic_demo_result.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({
    "state_decision": decision.__dict__,
    "ranking": ranking.to_dict(orient="records"),
    "claim_ceiling": ceiling,
    "fco": fco.as_dict(),
}, indent=2), encoding="utf-8")
print("\nWrote", out)
