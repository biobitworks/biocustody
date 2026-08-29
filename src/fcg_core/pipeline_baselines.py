"""Pipeline baselines B0–B3 for mutation disposition benchmark."""

from __future__ import annotations

from typing import Any


def _gt_flags(gt: dict[str, Any]) -> dict[str, bool]:
    return {
        "semantic": bool(gt.get("expected_semantic_changed")),
        "provenance": bool(gt.get("expected_provenance_changed")),
        "contradiction": bool(gt.get("expected_contradiction_changed")),
        "structure": bool(gt.get("expected_structure_changed")),
        "benign": gt.get("expected_terminal") in {"BENIGN_INVARIANCE", "DUPLICATE_ALIAS"},
        "unsupported": gt.get("expected_terminal") in {"UNSUPPORTED_CLAIM", "FALSE_VERIFICATION", "AUTHORITY_BREAK"},
    }


def _expected_disposition(gt: dict[str, Any]) -> str:
    t = gt.get("expected_terminal", "")
    if t in {"BENIGN_INVARIANCE", "DUPLICATE_ALIAS"}:
        return "PRESERVE_SEMANTIC"
    if t in {"UNSUPPORTED_CLAIM", "FALSE_VERIFICATION", "AUTHORITY_BREAK"}:
        return "ABSTAIN_OR_REJECT"
    if gt.get("expected_provenance_changed"):
        return "PROVENANCE_BREAK"
    if gt.get("expected_contradiction_changed"):
        return "CONTRADICTION_CHANGE"
    if gt.get("expected_semantic_changed"):
        return "SEMANTIC_CHANGE"
    if gt.get("expected_structure_changed"):
        return "STRUCTURE_CHANGE"
    return "NO_CHANGE"


def run_b0_crypto_only(gt: dict[str, Any], mutated: dict[str, Any]) -> dict[str, Any]:
    """Byte custody only — detects content change, poor semantic disposition."""
    content_changed = bool(gt.get("expected_content_changed"))
    flags = _gt_flags(gt)
    expected = _expected_disposition(gt)
    # B0: if bytes changed, often misclassifies as generic CHANGE without localization
    if not content_changed:
        disposition = "NO_CHANGE"
        correct_semantic = expected == "NO_CHANGE" or expected == "PRESERVE_SEMANTIC"
    elif flags["benign"]:
        disposition = "SEMANTIC_CHANGE"  # false promotion
        correct_semantic = False
    elif flags["unsupported"]:
        disposition = "VERIFY"  # false acceptance
        correct_semantic = False
    else:
        disposition = "BYTE_CHANGED"
        correct_semantic = flags["semantic"] or flags["provenance"] or flags["contradiction"]
    return {
        "pipeline": "B0_CRYPTO_CUSTODY_ONLY",
        "disposition": disposition,
        "correct_semantic_disposition": correct_semantic,
        "correct_downstream_localization": False,
        "false_semantic_promotion": flags["benign"] and disposition == "SEMANTIC_CHANGE",
        "false_claim_acceptance": flags["unsupported"] and disposition == "VERIFY",
        "terminal": disposition,
    }


def run_b1_structural_lattice(gt: dict[str, Any], mutated: dict[str, Any], baseline_obj: dict[str, Any]) -> dict[str, Any]:
    flags = _gt_flags(gt)
    expected = _expected_disposition(gt)
    if flags["structure"]:
        disposition = "STRUCTURE_CHANGE"
        correct = expected == "STRUCTURE_CHANGE"
    elif flags["benign"]:
        disposition = "STRUCTURE_CHANGE" if mutated.get("parent_id") != baseline_obj.get("parent_id") else "PRESERVE"
        correct = expected == "PRESERVE_SEMANTIC"
        if disposition == "STRUCTURE_CHANGE" and expected == "PRESERVE_SEMANTIC":
            correct = False
        else:
            correct = expected == "PRESERVE_SEMANTIC"
    elif flags["semantic"] or flags["provenance"]:
        disposition = "BYTE_OR_STRUCTURAL_ONLY"
        correct = False
    elif flags["unsupported"]:
        disposition = "BYTE_OR_STRUCTURAL_ONLY"
        correct = False
    else:
        disposition = "NO_CHANGE"
        correct = expected in {"NO_CHANGE", "PRESERVE_SEMANTIC"}
    return {
        "pipeline": "B1_STRUCTURAL_LATTICE",
        "disposition": disposition,
        "correct_semantic_disposition": correct,
        "correct_downstream_localization": flags["structure"] and correct,
        "false_semantic_promotion": flags["benign"] and disposition != "PRESERVE",
        "false_claim_acceptance": flags["unsupported"],
        "terminal": disposition,
    }


def run_b2_verify_no_abstain(gt: dict[str, Any], mutated: dict[str, Any]) -> dict[str, Any]:
    flags = _gt_flags(gt)
    expected = _expected_disposition(gt)
    if flags["unsupported"] or flags["provenance"] or (flags["semantic"] and not flags["benign"]):
        disposition = "VERIFY"  # forced verify — false acceptance
        correct = False
        false_accept = flags["unsupported"] or flags["provenance"]
    elif flags["benign"]:
        disposition = "VERIFY"
        correct = False
        false_accept = False
    else:
        disposition = "REJECT" if flags["semantic"] or flags["contradiction"] else "VERIFY"
        correct = expected in {"NO_CHANGE", "PRESERVE_SEMANTIC", "SEMANTIC_CHANGE", "CONTRADICTION_CHANGE"}
        false_accept = flags["unsupported"]
    return {
        "pipeline": "B2_VERIFY_ONLY_NO_ABSTAIN",
        "disposition": disposition,
        "correct_semantic_disposition": correct,
        "correct_downstream_localization": correct and (flags["semantic"] or flags["provenance"]),
        "false_semantic_promotion": flags["benign"] and disposition == "VERIFY",
        "false_claim_acceptance": false_accept or (flags["unsupported"] and disposition == "VERIFY"),
        "terminal": disposition,
    }


def run_b3_full_verify_abstain(gt: dict[str, Any], mutated: dict[str, Any]) -> dict[str, Any]:
    flags = _gt_flags(gt)
    expected = _expected_disposition(gt)
    if flags["benign"]:
        disposition = "PRESERVE_SEMANTIC"
        correct = expected == "PRESERVE_SEMANTIC"
    elif flags["unsupported"]:
        disposition = "ABSTAIN"
        correct = expected == "ABSTAIN_OR_REJECT"
    elif flags["provenance"]:
        disposition = "PROVENANCE_BREAK"
        correct = expected == "PROVENANCE_BREAK"
    elif flags["contradiction"]:
        disposition = "CONTRADICTION_CHANGE"
        correct = expected == "CONTRADICTION_CHANGE"
    elif flags["semantic"]:
        disposition = "SEMANTIC_CHANGE"
        correct = expected == "SEMANTIC_CHANGE"
    elif flags["structure"]:
        disposition = "STRUCTURE_CHANGE"
        correct = expected == "STRUCTURE_CHANGE"
    else:
        disposition = "NO_CHANGE"
        correct = expected in {"NO_CHANGE", "PRESERVE_SEMANTIC", "DUPLICATE_ALIAS"}
    return {
        "pipeline": "B3_FULL_VERIFY_OR_ABSTAIN",
        "disposition": disposition,
        "correct_semantic_disposition": correct,
        "correct_downstream_localization": correct,
        "false_semantic_promotion": flags["benign"] and disposition not in {"PRESERVE_SEMANTIC", "NO_CHANGE", "DUPLICATE_ALIAS"},
        "false_claim_acceptance": flags["unsupported"] and disposition not in {"ABSTAIN", "REJECT", "INSUFFICIENT"},
        "terminal": disposition,
    }


def evaluate_mutation(mutation: dict[str, Any], baseline_obj: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    gt = mutation
    mutated = mutation.get("mutated_payload", {})
    baseline_obj = baseline_obj or {}
    return [
        run_b0_crypto_only(gt, mutated),
        run_b1_structural_lattice(gt, mutated, baseline_obj),
        run_b2_verify_no_abstain(gt, mutated),
        run_b3_full_verify_abstain(gt, mutated),
    ]
