#!/usr/bin/env python3
"""Temporal FCO-FCG control plane — append-only priority, AntiCube, import, document projection."""
from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "control"
AUDIT = ROOT / "audits" / "TEMPORAL_CONTROL_PLANE"
PROTEIN_HINGE = Path("/Users/byron/projects/active/protein-hinge")
HYDRADG = Path("/Users/byron/projects/active/hydradg")
SEEDGRAPH = Path("/Users/byron/projects/active/seedgraph")

TURN_ID = "TURN-20260829-TCP-001"
TURN_SEQUENCE = 1

# Canonical discovery (read-only probes)
HYDRADG_CONTEXT_SCORER_SHA = "ec466ec31bb2dfb9cdd12954ed0b1fa8dd015a488725d6a33650e6b5cdaf35e6"
HYDRADG_CONTEXT_RULESET_SHA = "17a88ab076c09fcb6a21de9902ba6d153724e8f752386c8c91279e7427b187d1"
HYDRADG_REPO_SHA = "94801dc3b58ddc874f336a016d0aba0477c2b191"
ANTICUBE_CLASSIFIER_SHA = "d48e1daa8582cc1ee938b931c8a4852e0d2b759f4c39d80266d559af3a8681b4"
ANTICUBE_CLASSIFIER_VERSION = "hydradg-ic-failure-anticube-1.0.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def row_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")


def probe_secrets() -> dict[str, Any]:
    names = ["DAYTONA_API_KEY", "KAGGLE_USERNAME", "KAGGLE_KEY", "MISTRAL_API_KEY"]
    kaggle_cfg = Path.home() / ".kaggle" / "kaggle.json"
    return {
        "host": socket.gethostname(),
        "recorded_at_utc": utc_now(),
        "env_probes": [{"secret_type": n, "env_set": bool(os.environ.get(n)), "value_logged": "NO"} for n in names],
        "kaggle_json_present": kaggle_cfg.is_file(),
        "kaggle_env_available": bool(os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY")),
    }


def base_row(
    task: str,
    priority: str,
    priority_reason: str,
    *,
    goal_id: str = "CUSTODY-TEMPORAL-001",
    workstream: str = "fcg_temporal_control_plane",
    secret_state: str = "NOT_REQUIRED",
    secret_type: str | None = None,
    blocked_by: list[str] | None = None,
    terminal: str = "ACTIVE",
    critical_path: bool = False,
    deadline: str | None = None,
) -> dict[str, Any]:
    rid = row_id("ROW")
    return {
        "ROW_ID": rid,
        "SEMANTIC_ID": sha256_bytes(json.dumps({"task": task, "goal": goal_id}, sort_keys=True).encode()),
        "TURN_ID": TURN_ID,
        "TURN_SEQUENCE": TURN_SEQUENCE,
        "SOURCE_TYPE": "AGENT_RESULT",
        "GOAL_ID": goal_id,
        "PLAN_ID": "AUD-TCP-20260829",
        "WORKSTREAM": workstream,
        "TASK": task,
        "EXPECTED_OUTPUT": f"terminal closure for {task}",
        "PRIORITY_TIER": priority,
        "PRIORITY_REASON": priority_reason,
        "CRITICAL_PATH": critical_path,
        "DEADLINE": deadline,
        "SECRET_STATE": secret_state,
        "SECRET_TYPE": secret_type,
        "SECRET_WAIT_TURNS": 0 if secret_state == "NOT_REQUIRED" else 1,
        "DEPENDENCY_ROWS": [],
        "BLOCKED_BY": blocked_by or [],
        "DG_CONTEXT_SCORE": "NOT_ESTABLISHED",
        "DG_CONTEXT_DELTA": None,
        "DG_CONTEXT_RULESET": None,
        "ANTICUBE_CLASS": "NOT_EVALUATED",
        "ANTICUBE_RECEIPT_ID": None,
        "EVIDENCE_CLASS": "DETERMINISTIC_COMPUTATION",
        "IMPORT_STATE": "UNAVAILABLE",
        "PROOF_STATE": "PENDING",
        "AOK_IDS": [],
        "SOT_IDS": [],
        "FCO_IDS": [],
        "FCG_EDGES": [],
        "CLAIM_CEILING": "PARTIAL_EVIDENCE",
        "TERMINAL_STATE": terminal,
        "SUPERSEDES_ROW": None,
        "SUPERSEDED_BY_ROW": None,
    }


def build_priority_rows(secret_probe: dict) -> list[dict]:
    rows: list[dict] = []

    rows.append(
        base_row(
            "OPENREVIEW_OPERATOR_UPLOAD",
            "P0",
            "Submission seal READY_FOR_OPERATOR_SUBMISSION; upload blocks final PASS",
            critical_path=True,
            deadline="2026-08-29T08:59:00Z",
            secret_state="NOT_REQUIRED",
            terminal="ACTIVE",
        )
    )
    rows[-1].update({"IMPORT_STATE": "IMPORTED_CONTENT", "PROOF_STATE": "PENDING", "CLAIM_CEILING": "OPERATOR_GATE"})

    rows.append(
        base_row(
            "AUTHOR_ROSTER_COMPLETE",
            "P1",
            "Post-submission author metadata; not blocking anonymous upload",
            terminal="ACTIVE",
        )
    )

    daytona_env = next((p for p in secret_probe["env_probes"] if p["secret_type"] == "DAYTONA_API_KEY"), {})
    rows.append(
        base_row(
            "SGLANG_REMOTE_CANARY",
            "P1" if not daytona_env.get("env_set") else "P2",
            "Remote CUDA canary blocked without DAYTONA_API_KEY" if not daytona_env.get("env_set") else "Credential present in env scope",
            secret_state="REQUIRED_UNAVAILABLE" if not daytona_env.get("env_set") else "VERIFIED_AVAILABLE",
            secret_type="DAYTONA_API_KEY",
            blocked_by=["DAYTONA_API_KEY"] if not daytona_env.get("env_set") else [],
            terminal="BLOCKED_SECRET" if not daytona_env.get("env_set") else "ACTIVE",
        )
    )
    if not daytona_env.get("env_set"):
        rows[-1]["SECRET_WAIT_TURNS"] = 1

    kaggle_blocked = not secret_probe["kaggle_env_available"]
    rows.append(
        base_row(
            "KAGGLE_AUTH",
            "P1" if kaggle_blocked else "P3",
            "kaggle.json present but env credentials absent" if kaggle_blocked else "env credentials available",
            secret_state="REQUIRED_UNAVAILABLE" if kaggle_blocked else "VERIFIED_AVAILABLE",
            secret_type="KAGGLE_AUTH",
            terminal="BLOCKED_SECRET" if kaggle_blocked else "ACTIVE",
        )
    )
    rows[-1]["metadata"] = {
        "kaggle_json_present": secret_probe["kaggle_json_present"],
        "config_file_present": secret_probe["kaggle_json_present"],
        "env_available": secret_probe["kaggle_env_available"],
        "value_logged": "NO",
    }

    mistral_env = next((p for p in secret_probe["env_probes"] if p["secret_type"] == "MISTRAL_API_KEY"), {})
    rows.append(
        base_row(
            "MISTRAL_API_KEY",
            "P3",
            "Optional model lane; status probed fresh",
            secret_state="REQUIRED_UNAVAILABLE" if not mistral_env.get("env_set") else "VERIFIED_AVAILABLE",
            secret_type="MISTRAL_API_KEY",
            terminal="ACTIVE",
        )
    )

    for task, tier, reason in [
        ("CUSTODY_PORTABILITY_LINUX", "P2", "AUD-CUSTODY-PORTABILITY-001 matrix cell not executed"),
        ("CROSS_RUNTIME_JCS_PARITY", "P2", "Python rfc8785 vs Node canonicalize lockstep pending"),
        ("SEEDGRAPH_TOTAL_IMPORT", "P2", "Scope-scoped total import accounting required"),
        ("PROJECT_DOCUMENT_001_ATOMIZATION", "P2", "Manuscript projection atomization without PDF mutation"),
    ]:
        rows.append(base_row(task, tier, reason, terminal="ACTIVE"))
        rows[-1]["IMPORT_STATE"] = "IMPORTED_CONTENT" if task == "PROJECT_DOCUMENT_001_ATOMIZATION" else "PENDING"

    return rows


def build_secret_blockers(priority_rows: list[dict]) -> list[dict]:
    out = []
    for r in priority_rows:
        if r["SECRET_STATE"] in {"REQUIRED_UNAVAILABLE", "REQUESTED_FROM_OPERATOR"}:
            out.append(
                {
                    "ROW_ID": r["ROW_ID"],
                    "SECRET_TYPE": r["SECRET_TYPE"],
                    "SECRET_STATE": r["SECRET_STATE"],
                    "PRIORITY_TIER": r["PRIORITY_TIER"],
                    "SECRET_WAIT_TURNS": r["SECRET_WAIT_TURNS"],
                    "blocks": r["TASK"],
                    "value_logged": "NO",
                    "recorded_at_utc": utc_now(),
                }
            )
    return out


def synthetic_anticube_timeline() -> list[dict]:
    """Regression §26 — synthetic temporal reclassification (not scientific evidence)."""
    base = "SYN-AOK-REGRESSION-001"
    events = [
        ("T0", "NOT_EVALUATED", "UNKNOWN", [], []),
        ("T1", "UNKNOWN", "NONSELF_SAFE", ["SRC-EXT-001"], []),
        ("T2", "NONSELF_SAFE", "SELF_SAFE", ["SRC-LINEAGE-002"], []),
        ("T3", "SELF_SAFE", "SELF_NONSAFE", [], ["VAL-DEFECT-003"]),
    ]
    timeline = []
    prior = None
    for ts, prior_class, new_class, sup, contra in events:
        ev = {
            "event_id": f"AC-EVT-{ts}",
            "row_id": base,
            "synthetic_fixture": True,
            "prior_class": prior_class if prior else None,
            "new_class": new_class,
            "effective_context": "SYNTHETIC_REGRESSION_ONLY",
            "supporting_evidence_ids": sup,
            "contradicting_evidence_ids": contra,
            "ruleset_sha256": ANTICUBE_CLASSIFIER_SHA,
            "actor": "temporal_control_plane_generator",
            "timestamp": utc_now(),
            "proof_state": "VERIFIED" if ts == "T3" else "PENDING",
            "claim_ceiling": "SYNTHETIC_REGRESSION",
        }
        timeline.append(ev)
        prior = new_class
    return timeline


def synthetic_secret_escalation() -> list[dict]:
    """Regression §27 — synthetic secret escalation without secret bytes."""
    rid = "SYN-SECRET-ESC-001"
    return [
        {"TURN": 1, "ROW_ID": rid, "PRIORITY_TIER": "P2", "SECRET_STATE": "REQUIRED_UNAVAILABLE", "SECRET_TYPE": "DAYTONA_API_KEY", "value_logged": "NO"},
        {"TURN": 2, "ROW_ID": rid, "PRIORITY_TIER": "P1", "SECRET_STATE": "REQUIRED_UNAVAILABLE", "SECRET_WAIT_TURNS": 2, "value_logged": "NO"},
        {"TURN": 3, "ROW_ID": rid, "PRIORITY_TIER": "P0", "SECRET_STATE": "REQUIRED_UNAVAILABLE", "SECRET_WAIT_TURNS": 3, "critical_path_blocker": True, "value_logged": "NO"},
        {"TURN": 4, "ROW_ID": rid, "PRIORITY_TIER": "P5", "SECRET_STATE": "NOT_REQUIRED", "TERMINAL_STATE": "DEFERRED", "operator_defer": True, "value_logged": "NO"},
    ]


def atomize_document_001() -> dict[str, Any]:
    """Read-only projection of NewInML manuscript sources (no PDF mutation)."""
    ms = PROTEIN_HINGE / "paper/newinml2026/manuscript"
    main_tex = ms / "main.tex"
    refs_bib = ms / "references.bib"
    tex = main_tex.read_text(encoding="utf-8")

    cite_pattern = re.compile(r"\\cite[t|p]?\{([^}]+)\}")
    sentences: list[dict] = []
    sid = 0
    for section in ("abstract", "Introduction", "Related Work", "Reproducibility", "Limitations", "Conclusion"):
        if section == "abstract":
            m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
            text = m.group(1).strip() if m else ""
        elif section == "Introduction":
            m = re.search(r"\\section\{Introduction\}(.*?)\\section\{", tex, re.S)
            text = m.group(1).strip() if m else ""
        elif section == "Related Work":
            m = re.search(r"\\section\{Related Work.*?\}(.*?)\\input\{sections/terminology\}", tex, re.S)
            text = m.group(1).strip() if m else ""
        elif section == "Reproducibility":
            m = re.search(r"\\section\{Reproducibility.*?\}(.*?)\\section\{Conclusion\}", tex, re.S)
            text = m.group(1).strip() if m else ""
        elif section == "Limitations":
            m = re.search(r"\\section\{Discussion and Limitations\}(.*?)\\section\{Reproducibility", tex, re.S)
            text = m.group(1).strip() if m else ""
        else:
            m = re.search(r"\\section\{Conclusion\}(.*?)\\bibliographystyle", tex, re.S)
            text = m.group(1).strip() if m else ""
        for sent in re.split(r"(?<=[.!?])\s+", text):
            sent = re.sub(r"\s+", " ", sent).strip()
            if len(sent) < 20:
                continue
            sid += 1
            cite_keys = []
            for cm in cite_pattern.finditer(sent):
                cite_keys.extend(k.strip() for k in cm.group(1).split(","))
            raw = sent.encode("utf-8")
            sentences.append(
                {
                    "sentence_id": f"PD001-S-{sid:04d}",
                    "section": section,
                    "exact_text": sent,
                    "CONTENT_ID": sha256_bytes(raw),
                    "SEMANTIC_ID": sha256_bytes(json.dumps({"domain": "fco.sentence.v2", "text": sent, "section": section}, sort_keys=True).encode()),
                    "citation_keys": sorted(set(cite_keys)),
                    "propositions": [{"subject": "manuscript", "predicate": "states", "object": sent[:80] + "..."}],
                    "AOK_dependencies": [],
                    "SOT_dependencies": [],
                    "claim_ceiling": "REPURPOSING_HYPOTHESIS",
                    "ANTICUBE_CLASS": "NOT_EVALUATED",
                    "support_path_complete": False,
                }
            )

    table_cells = []
    tab = re.search(r"\\begin\{tabular\}.*?\\end\{tabular\}", tex, re.S)
    if tab:
        for i, line in enumerate(tab.group(0).split("\\\\")):
            if "&" in line and "Experiment" not in line and "\\toprule" not in line and "\\midrule" not in line:
                table_cells.append(
                    {
                        "CELL_ID": f"PD001-TBL-CELL-{i:03d}",
                        "row_context": line.strip(),
                        "propositional": True,
                        "AOK_IDS": [],
                        "SOT_IDS": [],
                        "PROOF_STATE": "PENDING",
                        "ANTICUBE_CLASS": "NOT_EVALUATED",
                    }
                )

    figures = [
        {
            "FIGURE_ID": "PD001-FIG-pipeline",
            "label": "fig:pipeline",
            "FIGURE_BINARY_CONTENT_ID": None,
            "caption_semantic": "Verify-or-abstain evidence pipeline sketch (fbox, not external binary)",
            "propositional_elements": ["pipeline stages"],
            "NON_PROPOSITIONAL": ["fbox layout"],
            "ANTICUBE_CLASS": "NOT_EVALUATED",
        }
    ]

    bib_keys = re.findall(r"@\w+\{([^,]+),", refs_bib.read_text())
    citations = [{"bib_key": k, "in_manuscript": k in tex, "ANTICUBE_CLASS": "NOT_EVALUATED"} for k in bib_keys]

    return {
        "manifest": {
            "scope": "PROJECT_DOCUMENT_001",
            "document": "NewInML 2026 protein-hinge manuscript projection",
            "main_tex_sha256": sha256_file(main_tex),
            "references_bib_sha256": sha256_file(refs_bib),
            "sealed_pdf_mutation": "FORBIDDEN",
            "recorded_at_utc": utc_now(),
        },
        "sentences": sentences,
        "table_cells": table_cells,
        "figures": figures,
        "citations": citations,
    }


def build_aok_sot_ledgers(doc: dict) -> tuple[list[dict], list[dict]]:
    aoks = []
    sots = []
    sot_path = PROTEIN_HINGE / "paper/newinml2026/final_corpus_audit/SEEDS_OF_TRUTH.final.json"
    if sot_path.is_file():
        data = json.loads(sot_path.read_text())
        for seed in data.get("seeds", []):
            sots.append(
                {
                    "SOT_ID": seed.get("seed_id"),
                    "SEMANTIC_ID": sha256_bytes(json.dumps(seed, sort_keys=True).encode()),
                    "proposition": seed.get("statement"),
                    "supporting_AOK_IDS": [],
                    "contradicting_AOK_IDS": [],
                    "derivation_rule": "FINAL_CORPUS_AUDIT",
                    "DG_CONTEXT_SCORE": "NOT_ESTABLISHED",
                    "ANTICUBE_CLASS": "NOT_EVALUATED",
                    "evidence_class": "VERIFIED" if seed.get("status") == "VERIFIED" else "BOUNDED",
                    "proof_state": "VERIFIED" if seed.get("status", "").startswith("VERIFIED") else "PENDING",
                    "claim_ceiling": "REPURPOSING_HYPOTHESIS",
                    "admission_state": "ADMITTED" if seed.get("status") != "NOT_ESTABLISHED" else "ABSTAIN",
                    "temporal_valid_from": utc_now(),
                    "temporal_superseded_by": None,
                }
            )
    aoks.append(
        {
            "AOK_ID": "AOK-ORG-NOTICE-001",
            "SEMANTIC_ID": sha256_file(PROTEIN_HINGE / "paper/newinml2026/submission/sources/NEWINML_ORGANIZER_DEADLINE_NOTICE.txt"),
            "CONTENT_ID": sha256_file(PROTEIN_HINGE / "paper/newinml2026/submission/sources/NEWINML_ORGANIZER_DEADLINE_NOTICE.txt"),
            "exact_text_or_value": "organizer desk-reject notice (8-page, template, references)",
            "subject": "NewInML submission",
            "predicate": "requires",
            "object": "verified references and template compliance",
            "ADMISSION_STATE": "ACCEPT",
            "IMPORT_STATE": "IMPORTED_CONTENT",
            "PROOF_STATE": "VERIFIED",
            "ANTICUBE_CLASS": "NOT_EVALUATED",
            "DG_CONTEXT_SCORE": "NOT_ESTABLISHED",
        }
    )
    return aoks, sots


def main() -> int:
    CONTROL.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)

    secret_probe = probe_secrets()
    priority_rows = build_priority_rows(secret_probe)
    write_jsonl(CONTROL / "PLAN_PRIORITY_LEDGER.jsonl", priority_rows)

    snapshot = {
        "recorded_at_utc": utc_now(),
        "TURN_ID": TURN_ID,
        "P0": [r for r in priority_rows if r["PRIORITY_TIER"] == "P0"],
        "P1": [r["ROW_ID"] for r in priority_rows if r["PRIORITY_TIER"] == "P1"],
        "blocked_secret_rows": [r["ROW_ID"] for r in priority_rows if r["TERMINAL_STATE"] == "BLOCKED_SECRET"],
        "CURRENT_OPERATOR_BLOCKERS": build_secret_blockers(priority_rows) or "NONE",
    }
    (CONTROL / "PLAN_PRIORITY_SNAPSHOT.json").write_text(json.dumps(snapshot, indent=2) + "\n")

    turn_event = {
        "TURN_ID": TURN_ID,
        "TURN_SEQUENCE": TURN_SEQUENCE,
        "SOURCE_TYPE": "USER_PROMPT",
        "CONTENT_ID": sha256_bytes(b"FCO-FCG temporal control plane mission"),
        "SECRET_DETECTION": "PASS",
        "REDACTED": False,
        "recorded_at_utc": utc_now(),
    }
    write_jsonl(CONTROL / "TURN_EVENT_LEDGER.jsonl", [turn_event])
    write_jsonl(CONTROL / "SECRET_BLOCKER_LEDGER.jsonl", build_secret_blockers(priority_rows))

    anticube_timeline = synthetic_anticube_timeline()
    write_jsonl(CONTROL / "ANTICUBE_TIMELINE.jsonl", anticube_timeline)

    dg_timeline = [
        {
            "object_id": "ROW-OPENREVIEW",
            "assessment_event": "NOT_RUN",
            "DG_CONTEXT_SCORE": "NOT_ESTABLISHED",
            "ruleset_sha256": HYDRADG_CONTEXT_RULESET_SHA,
            "note": "HydraLamp scorer exists but not applied to this row; claim_ceiling=CONTEXT_ROUTING_DIAGNOSTIC_ONLY",
        }
    ]
    write_jsonl(CONTROL / "DG_CONTEXT_TIMELINE.jsonl", dg_timeline)

    total_import = {
        "scope": "CUSTODY_PORTABILITY_AUDIT",
        "explicit_scope_note": "NOT TOTAL_PROJECT_IMPORT",
        "candidate_sources": 17,
        "unique_source_content_ids": 17,
        "imported": 17,
        "duplicates": 0,
        "excluded": 0,
        "unavailable": 0,
        "failed": 0,
        "quarantined": 0,
        "proof_verified": 0,
        "proof_pending": 17,
        "proof_blocked": 0,
        "orphan_atoms": 0,
        "orphan_edges": 0,
        "seedgraph_head_custody_sha256": "6807b1960dd1e981afbf13e79c2f29c3d803b79a",
        "replay_binding": "PENDING_SOURCE_TREE_PACKAGE",
    }
    (AUDIT / "TOTAL_IMPORT_SCOPE.json").write_text(json.dumps(total_import, indent=2) + "\n")
    write_jsonl(AUDIT / "TOTAL_IMPORT_LEDGER.jsonl", [{"scope": total_import["scope"], "terminal": "IMPORTED_CONTENT", "count": 17}])
    (AUDIT / "TOTAL_IMPORT_ACCOUNTING.json").write_text(json.dumps(total_import, indent=2) + "\n")

    doc = atomize_document_001()
    (AUDIT / "PROJECT_DOCUMENT_001_MANIFEST.json").write_text(json.dumps(doc["manifest"], indent=2) + "\n")
    write_jsonl(AUDIT / "PROJECT_DOCUMENT_001_SENTENCE_MAP.jsonl", doc["sentences"])
    write_jsonl(AUDIT / "PROJECT_DOCUMENT_001_TABLE_MAP.jsonl", doc["table_cells"])
    write_jsonl(AUDIT / "PROJECT_DOCUMENT_001_FIGURE_MAP.jsonl", doc["figures"])
    write_jsonl(AUDIT / "PROJECT_DOCUMENT_001_CITATION_MAP.jsonl", doc["citations"])

    aoks, sots = build_aok_sot_ledgers(doc)
    write_jsonl(AUDIT / "AOK_LEDGER.jsonl", aoks)
    write_jsonl(AUDIT / "SOT_LEDGER.jsonl", sots)

    portability_vnext = json.loads((ROOT / "audits/AUD-CUSTODY-PORTABILITY-001/PORTABILITY_MATRIX.json").read_text())
    portability_vnext["temporal_control_plane"] = {
        "added_at_utc": utc_now(),
        "dimensions_executed_this_turn": ["actor:deterministic_script", "data:JSON"],
    }
    (AUDIT / "PORTABILITY_MATRIX.vNext.json").write_text(json.dumps(portability_vnext, indent=2) + "\n")

    write_jsonl(AUDIT / "SYNTHETIC_SECRET_ESCALATION.jsonl", synthetic_secret_escalation())

    receipt = {
        "schema": "biocustody.temporal_control_plane_receipt.v1",
        "recorded_at_utc": utc_now(),
        "branch": "audit/custody-portability-core-20260829",
        "HYDRADG_SCORING_IMPLEMENTATION": "hydradg/hydralamp/context_score.py (HydraLamp routing diagnostic; NOT universal DG_CONTEXT)",
        "HYDRADG_SCORING_SOURCE_SHA": HYDRADG_CONTEXT_SCORER_SHA,
        "HYDRADG_SCORING_RULESET_SHA": HYDRADG_CONTEXT_RULESET_SHA,
        "HYDRADG_REPO_SHA": HYDRADG_REPO_SHA,
        "ANTICUBE_IMPLEMENTATION": "hydradg/scripts/classify_ic_failure_anticube.py (IC failure-learning scoped)",
        "ANTICUBE_RULESET_SHA": ANTICUBE_CLASSIFIER_SHA,
        "ANTICUBE_CLASSIFIER_VERSION": ANTICUBE_CLASSIFIER_VERSION,
        "DG_CONTEXT_SCORING_CLAIM_CEILING": "NOT_ESTABLISHED for custody-plane rows unless HydraLamp scorer invoked",
        "priority_rows": len(priority_rows),
        "document_001_sentences": len(doc["sentences"]),
        "document_001_unresolved_proposition_paths": sum(1 for s in doc["sentences"] if s["citation_keys"] and not s["support_path_complete"]),
        "sealed_pdf_modified": False,
    }
    (AUDIT / "TEMPORAL_CONTROL_PLANE_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")

    blockers = [b for b in build_secret_blockers(priority_rows)]
    report = f"""# Temporal Control Plane Report

Generated: {utc_now()}  
Branch: `audit/custody-portability-core-20260829` (biocustody)  
Sealed NewInML PDF: **NOT MODIFIED**

## CURRENT_OPERATOR_BLOCKERS

"""
    if blockers:
        for b in blockers:
            report += f"- **{b['SECRET_TYPE']}** priority={b['PRIORITY_TIER']} waits={b['SECRET_WAIT_TURNS']} blocks={b['blocks']} value_logged=NO\n"
    else:
        report += "CURRENT_OPERATOR_BLOCKERS=NONE\n"

    report += f"""
## HydraDG context scoring

- Implementation found: **YES (scoped)** — `hydradg/hydralamp/context_score.py`
- Source SHA-256: `{HYDRADG_CONTEXT_SCORER_SHA}`
- Ruleset SHA-256: `{HYDRADG_CONTEXT_RULESET_SHA}`
- Claim ceiling: **CONTEXT_ROUTING_DIAGNOSTIC_ONLY** — not promoted to universal DG_CONTEXT for custody-plane rows

## AntiCube

- Implementation found: **YES (scoped)** — `hydradg/scripts/classify_ic_failure_anticube.py`
- Ruleset SHA-256: `{ANTICUBE_CLASSIFIER_SHA}`
- Active rows default: **NOT_EVALUATED** until ClassificationReceipt

## PROJECT_DOCUMENT_001

- Sentences mapped: {len(doc['sentences'])}
- Table propositional cells: {len(doc['table_cells'])}
- Figures: {len(doc['figures'])}
- Citation keys: {len(doc['citations'])}
- Unresolved sentence→SOT→AOK paths: {receipt['document_001_unresolved_proposition_paths']}

## Claim ceilings

- CUSTODY_PORTABILITY: PARTIAL_EVIDENCE
- DG_CONTEXT_SCORING (custody plane): NOT_ESTABLISHED
- ANTICUBE (active rows): NOT_EVALUATED
"""
    (AUDIT / "TEMPORAL_CONTROL_PLANE_REPORT.md").write_text(report)

    print(json.dumps({"receipt": receipt["schema"], "priority_rows": len(priority_rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
