"""VALIDATION_RESULT (deterministic) vs VALIDATION_OCCURRENCE (run event)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from fcg_core.canonical_v2 import canonical_hash_v2
from fcg_core.states import ImportState, ProofState


class ValidationResult(BaseModel):
    """Reproducible validation bytes — no wall-clock timestamp in identity."""

    schema_version: str = "1.0.0"
    input_hashes: dict[str, str]
    schema_hashes: dict[str, str]
    ruleset_sha256: str
    deterministic_outputs: dict[str, Any]
    terminal_classifications: dict[str, str]
    import_state: ImportState
    proof_state: ProofState

    @property
    def validation_result_id(self) -> str:
        payload = self.model_dump(mode="json")
        payload.pop("validation_result_id", None)
        return canonical_hash_v2({"domain": "fcg.validation_result.v1", **payload})


class ValidationOccurrence(BaseModel):
    """Run-event metadata bound to a validation_result_id."""

    validation_result_id: str
    observed_at: str
    actor_ref: str
    runtime_ref: str
    host_ref: str
    provider_ref: str
    toolchain_ref: str
