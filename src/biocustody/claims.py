from __future__ import annotations

CLAIM_LEVELS = [
    "OBSERVED_PROFILE",
    "PERTURBATION_DIFFERS_FROM_CONTROL",
    "PHENOTYPIC_OPPOSITION",
    "PREDICTED_COUNTER_PERTURBATION",
    "MECHANISTICALLY_PLAUSIBLE_CANDIDATE",
    "MEASURED_RESCUE",
    "REPLICATED_BIOLOGICAL_INTERVENTION",
    "THERAPEUTIC_CLAIM",
]

def claim_ceiling(
    *,
    profile_observed: bool,
    perturbation_detected: bool,
    opposition_supported: bool,
    target_evidence: bool = False,
    measured_combination_rescue: bool = False,
    replicated_validation: bool = False,
) -> str:
    if replicated_validation:
        return "REPLICATED_BIOLOGICAL_INTERVENTION"
    if measured_combination_rescue:
        return "MEASURED_RESCUE"
    if target_evidence and opposition_supported:
        return "MECHANISTICALLY_PLAUSIBLE_CANDIDATE"
    if opposition_supported:
        return "PREDICTED_COUNTER_PERTURBATION"
    if perturbation_detected:
        return "PERTURBATION_DIFFERS_FROM_CONTROL"
    if profile_observed:
        return "OBSERVED_PROFILE"
    return "UNSUPPORTED"
