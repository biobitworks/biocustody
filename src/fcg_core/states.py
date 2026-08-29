"""IMPORT_STATE and PROOF_STATE are orthogonal — import PASS must not promote proof."""

from __future__ import annotations

from enum import StrEnum


class ImportState(StrEnum):
    IMPORTED_CONTENT = "IMPORTED_CONTENT"
    IMPORTED_REFERENCE = "IMPORTED_REFERENCE"
    DUPLICATE = "DUPLICATE"
    EXCLUDED = "EXCLUDED"
    UNAVAILABLE = "UNAVAILABLE"
    FAILED = "FAILED"
    QUARANTINED = "QUARANTINED"


class ProofState(StrEnum):
    VERIFIED = "VERIFIED"
    PENDING = "PENDING"
    BLOCKED = "BLOCKED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT = "INSUFFICIENT"
    NOT_APPLICABLE = "NOT_APPLICABLE"


def import_terminal_ok(state: ImportState) -> bool:
    return state in {
        ImportState.IMPORTED_CONTENT,
        ImportState.IMPORTED_REFERENCE,
        ImportState.DUPLICATE,
        ImportState.EXCLUDED,
    }


def proof_promotable(import_state: ImportState, proof_state: ProofState) -> bool:
    """An import may complete while proof remains blocked/pending (regression fixture G)."""
    if not import_terminal_ok(import_state):
        return False
    return proof_state == ProofState.VERIFIED
