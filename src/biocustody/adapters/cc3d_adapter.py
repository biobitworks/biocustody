from __future__ import annotations
import json
from pathlib import Path

def write_candidate_effect(
    path,
    *,
    compound_id,
    canonical_smiles,
    counter_score,
    target=None,
    source_fco=None,
    dose_proxy=None,
):
    """
    Bridge output for a future CompuCell3D/Antimony tissue model.
    This is a parameter handoff, NOT a claim that morphology score equals a
    mechanistic pharmacodynamic parameter.
    """
    obj = {
        "schema": "biocustody.candidate_effect.v0.1",
        "compound_id": compound_id,
        "canonical_smiles": canonical_smiles,
        "counter_score": float(counter_score),
        "target": target,
        "dose_proxy": dose_proxy,
        "source_fco": source_fco,
        "mapping_status": "not_validated",
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    return obj
