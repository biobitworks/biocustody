from __future__ import annotations
import numpy as np
import pandas as pd

def _cosine(a, b, eps=1e-12):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + eps
    return float(np.dot(a, b) / denom)

def opposition_score(perturbation_signature, compound_signature) -> float:
    """Higher is more directionally opposite. Range approximately [-1, 1]."""
    return -_cosine(perturbation_signature, compound_signature)

def rank_counter_perturbations(
    reference,
    perturbation,
    candidates: dict[str, np.ndarray],
) -> pd.DataFrame:
    reference = np.asarray(reference, dtype=float)
    perturbation = np.asarray(perturbation, dtype=float)
    delta_p = perturbation - reference

    rows = []
    for name, x in candidates.items():
        x = np.asarray(x, dtype=float)
        delta_c = x - reference
        rows.append({
            "candidate": name,
            "opposition_score": opposition_score(delta_p, delta_c),
            "distance_to_reference": float(np.linalg.norm(delta_c)),
            "magnitude_ratio": float(np.linalg.norm(delta_c) / (np.linalg.norm(delta_p) + 1e-12)),
        })
    return pd.DataFrame(rows).sort_values(
        ["opposition_score", "distance_to_reference"],
        ascending=[False, True],
    ).reset_index(drop=True)
