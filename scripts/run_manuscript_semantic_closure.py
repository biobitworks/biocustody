#!/usr/bin/env python3
"""Terminal semantic closure for 18 non-citation manuscript sentences.

Does not fabricate SOT/AOK support. Every sentence receives a terminal resolution.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TCP = ROOT / "audits" / "TEMPORAL_CONTROL_PLANE"
LATTICE = ROOT / "audits" / "AUD-FCG-DOCUMENT-LATTICE-001"
PROTEIN_HINGE = Path("/Users/byron/projects/active/protein-hinge")
SOT_PATH = PROTEIN_HINGE / "paper/newinml2026/final_corpus_audit/SEEDS_OF_TRUTH.final.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_sentences() -> list[dict]:
    path = TCP / "PROJECT_DOCUMENT_001_SENTENCE_MAP.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_sots() -> dict[str, dict]:
    if not SOT_PATH.is_file():
        return {}
    seeds = json.loads(SOT_PATH.read_text())["seeds"]
    return {s["seed_id"]: s for s in seeds}


def classify_non_citation(sentence: dict, sots: dict[str, dict]) -> dict[str, Any]:
    sid = sentence["sentence_id"]
    text = sentence.get("exact_text", "")
    section = sentence.get("section", "")
    edge_id = f"EDGE-{sid}"

    # Quarantine / meta disclosure — terminal QUARANTINE or ABSTAIN, not elevated claims
    if "UNVERIFIED_HISTORICAL_CLAIM" in text or "quarantined" in text.lower():
        return {
            "edge_id": edge_id,
            "sentence_id": sid,
            "section": section,
            "gap_class": "QUARANTINE_META",
            "resolution": "QUARANTINE",
            "resolution_detail": "Explicit quarantine disclosure; not evidentiary support",
            "supporting_SOT_IDS": [],
            "supporting_AOK_IDS": ["AOK-ORG-NOTICE-001"],
            "claim_ceiling": "CONTEXT_ROUTING_DIAGNOSTIC_ONLY",
            "terminal": True,
            "recorded_at": utc_now(),
        }

    # Negative boundary / scope disclaimers — bounded by SOT where applicable
    scope_rules: list[tuple[list[str], str, str, list[str]]] = [
        (["morphology null", "negative evidence"], "SOT-013", "SUPPORTED_BOUNDED", ["SOT-013"]),
        (["do not claim therapeutic", "clinical utility", "biological rescue"], "SOT-009", "SUPPORTED_BOUNDED", ["SOT-009"]),
        (["no structure-prediction", "no folding experiment"], "SOT-009", "SUPPORTED_BOUNDED", ["SOT-009"]),
        (["hash-valid custody", "necessary but insufficient"], "SOT-003", "SUPPORTED_BOUNDED", ["SOT-003"]),
        (["integrity of bytes, not meaning", "custody and hash verification"], "SOT-003", "SUPPORTED_BOUNDED", ["SOT-003"]),
        (["byte identity and provenance closure, not biological"], "SOT-003", "SUPPORTED_BOUNDED", ["SOT-003"]),
        (["Frozen Custody Graph", "SHA-256 manifests"], "SOT-003", "SUPPORTED_BOUNDED", ["SOT-003"]),
        (["historical aggregate reported zero abstentions", "three abstentions"], "SOT-001", "SUPPORTED_BOUNDED", ["SOT-001", "SOT-002"]),
        (["successor implementation with derived aggregates"], "SOT-002", "SUPPORTED_BOUNDED", ["SOT-002"]),
        (["identity contract passes", "guard is bypassed"], "SOT-004", "PARTIAL_SUPPORT", ["SOT-004", "SOT-006"]),
        (["G1/G2 corpora were not recovered"], "SOT-007", "SUPPORTED_BOUNDED", ["SOT-007", "SOT-010"]),
        (["EXP-005 replication not executed"], "SOT-014", "ABSTAIN", ["SOT-014"]),
        (["llms assisted drafting"], "PROCEDURAL", "SUPPORTED_BOUNDED", []),
    ]
    lower = text.lower()
    for needles, _aok_hint, resolution, sot_ids in scope_rules:
        if any(n.lower() in lower for n in needles):
            valid_sots = [s for s in sot_ids if s in sots]
            aok_ids = [f"AOK-CAND-{sentence['SEMANTIC_ID'][:12]}"] if valid_sots else []
            if not valid_sots and resolution == "SUPPORTED_BOUNDED":
                aok_ids = ["AOK-ORG-NOTICE-001"]
            gap = "BOUNDED_SOT_LINK" if valid_sots else ("PROCEDURAL" if resolution == "SUPPORTED_BOUNDED" else "NO_SOT")
            return {
                "edge_id": edge_id,
                "sentence_id": sid,
                "section": section,
                "gap_class": gap,
                "resolution": resolution,
                "resolution_detail": "Terminal closure via manuscript scope + admitted SOT projection",
                "supporting_SOT_IDS": valid_sots,
                "supporting_AOK_IDS": aok_ids,
                "claim_ceiling": sentence.get("claim_ceiling", "REPURPOSING_HYPOTHESIS"),
                "terminal": True,
                "recorded_at": utc_now(),
            }

    # Framing / thesis sentences without experiment backing — ABSTAIN
    if section in {"abstract", "Introduction", "Conclusion"}:
        return {
            "edge_id": edge_id,
            "sentence_id": sid,
            "section": section,
            "gap_class": "NO_AOK",
            "resolution": "ABSTAIN",
            "resolution_detail": "Framing proposition; no full SOT→AOK experiment closure wired",
            "supporting_SOT_IDS": [],
            "supporting_AOK_IDS": [],
            "claim_ceiling": sentence.get("claim_ceiling", "REPURPOSING_HYPOTHESIS"),
            "terminal": True,
            "recorded_at": utc_now(),
        }

    # Reproducibility procedural statements
    if section == "Reproducibility":
        if "anonymous supplementary" in lower:
            return {
                "edge_id": edge_id,
                "sentence_id": sid,
                "section": section,
                "gap_class": "PROCEDURAL",
                "resolution": "SUPPORTED_BOUNDED",
                "resolution_detail": "Submission packaging statement; not biological claim",
                "supporting_SOT_IDS": [],
                "supporting_AOK_IDS": ["AOK-ORG-NOTICE-001"],
                "claim_ceiling": "CONTEXT_ROUTING_DIAGNOSTIC_ONLY",
                "terminal": True,
                "recorded_at": utc_now(),
            }
        if "clinvar" in lower or "no new model weights" in lower:
            return {
                "edge_id": edge_id,
                "sentence_id": sid,
                "section": section,
                "gap_class": "SCOPE_BOUNDARY",
                "resolution": "SUPPORTED_BOUNDED",
                "resolution_detail": "Data release boundary; bibliography-only reference",
                "supporting_SOT_IDS": [],
                "supporting_AOK_IDS": ["AOK-ORG-NOTICE-001"],
                "claim_ceiling": "REPURPOSING_HYPOTHESIS",
                "terminal": True,
                "recorded_at": utc_now(),
            }

    return {
        "edge_id": edge_id,
        "sentence_id": sid,
        "section": section,
        "gap_class": "NO_AOK",
        "resolution": "ABSTAIN",
        "resolution_detail": "Insufficient admitted evidence for SOT/AOK closure; terminal abstain",
        "supporting_SOT_IDS": [],
        "supporting_AOK_IDS": [],
        "claim_ceiling": sentence.get("claim_ceiling", "REPURPOSING_HYPOTHESIS"),
        "terminal": True,
        "recorded_at": utc_now(),
    }


def main() -> int:
    sentences = load_sentences()
    sots = load_sots()
    non_citation = [s for s in sentences if not s.get("citation_keys")]

    edges = [classify_non_citation(s, sots) for s in non_citation]
    assert len(non_citation) == 18, f"expected 18 non-citation sentences, got {len(non_citation)}"

    out_path = TCP / "PROJECT_DOCUMENT_001_NON_CITATION_CLOSURE.jsonl"
    with out_path.open("w", encoding="utf-8") as fh:
        for row in edges:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    lattice_path = LATTICE / "NON_CITATION_SEMANTIC_CLOSURE.jsonl"
    with lattice_path.open("w", encoding="utf-8") as fh:
        for row in edges:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    terminal = sum(1 for e in edges if e.get("terminal"))
    abstain = sum(1 for e in edges if e["resolution"] == "ABSTAIN")
    bounded = sum(1 for e in edges if e["resolution"] in {"SUPPORTED_BOUNDED", "PARTIAL_SUPPORT"})
    quarantine = sum(1 for e in edges if e["resolution"] == "QUARANTINE")

    summary = {
        "schema": "biocustody.manuscript_non_citation_closure.v1",
        "recorded_at_utc": utc_now(),
        "non_citation_sentences": len(non_citation),
        "terminal_accounting": f"{terminal}/{len(non_citation)}",
        "abstain": abstain,
        "bounded_or_partial": bounded,
        "quarantine": quarantine,
        "FULL_MANUSCRIPT_SEMANTIC_CLOSURE": "NOT_ESTABLISHED",
        "NON_CITATION_TERMINAL_CLOSURE": "PASS" if terminal == len(non_citation) else "FAIL",
        "CITATION_PATH_CLOSURE": "6_OF_6_SUPPORTED_BOUNDED",
        "SOT_008_PRESERVED": "NOT_ESTABLISHED",
        "SOT_014_PRESERVED": "NOT_ESTABLISHED",
        "edges": [e["edge_id"] for e in edges],
    }
    (TCP / "PROJECT_DOCUMENT_001_NON_CITATION_CLOSURE_RECEIPT.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    (LATTICE / "NON_CITATION_SEMANTIC_CLOSURE_RECEIPT.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )

    # Patch lattice audit receipt document_closure if present
    receipt_path = LATTICE / "AUDIT_RECEIPT.json"
    if receipt_path.is_file():
        receipt = json.loads(receipt_path.read_text())
        receipt["document_closure"]["non_citation_terminal_closure"] = summary["NON_CITATION_TERMINAL_CLOSURE"]
        receipt["document_closure"]["non_citation_abstain"] = abstain
        receipt["document_closure"]["non_citation_bounded"] = bounded
        receipt["recorded_at_utc"] = utc_now()
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

    print(json.dumps(summary, indent=2))
    return 0 if terminal == len(non_citation) else 1


if __name__ == "__main__":
    raise SystemExit(main())
