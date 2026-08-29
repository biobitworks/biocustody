"""B4 Antigence trained AIS comparator — blind to mutation truth labels."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

# biocustody canonical hashing
from fcg_core.canonical_v2 import canonical_hash_v2

ANTIGENCE_ROOT = Path("/Users/byron/projects/active/antigence")
FROZEN_ANTIGENCE_SHA = "1f12b3c2b2f7df90e11753f74443e4add48d5b46"
SCIFACT_BCELL_PATHS = [
    ANTIGENCE_ROOT / ".antigence/models/scifact-bcell-2026-01-05.pkl",
    ANTIGENCE_ROOT / ".antigence/runs/scifact-bcell-2026-01-05.pkl",
    Path("/Users/byron/projects/.immunos/runs/scifact-bcell-2026-01-05.pkl"),
]
SCIFACT_NK_PATHS = [
    ANTIGENCE_ROOT / ".antigence/models/scifact-nk-2026-01-05.pkl",
    ANTIGENCE_ROOT / ".antigence/runs/scifact-nk-2026-01-05.pkl",
    Path("/Users/byron/projects/.immunos/runs/scifact-nk-2026-01-05.pkl"),
]
FROZEN_SCIFACT_BCELL_SHA256 = "157c70c63c073e01ed016d1b826345b75079300052f51c30e8087cbeb6549e8d"
FROZEN_SCIFACT_NK_SHA256 = "b5e30d43101e922b0c740006142347332aa555d516a392afa7f968bb3b48d4c3"
ANOMALY_THRESHOLD = 0.45
PROVENANCE_CANONICAL = "4a372a5c459ad60cd23b850709011cbfd0e516b4"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_text(text: str) -> str:
    s = unicodedata.normalize("NFKC", text or "")
    return re.sub(r"\s+", " ", s).strip().lower()


def _model_ids(name: str, sha256: str, detector_type: str, dataset: str, train_date: str, numpy_ver: str, git_sha: str) -> dict[str, str]:
    content = canonical_hash_v2({"model_bytes_sha256": sha256, "path": name})
    semantic = canonical_hash_v2(
        {
            "detector_type": detector_type,
            "source_dataset": dataset,
            "training_date": train_date,
            "numpy_version": numpy_ver,
            "antigence_git_sha": git_sha,
            "model_name": name,
        }
    )
    occurrence = canonical_hash_v2({"content_id": content, "git_sha": git_sha, "admitted_at": "2026-08-29"})
    transform = canonical_hash_v2({"operation": "TRAIN_EXPORT", "model": name, "dataset": dataset})
    return {
        "MODEL_CONTENT_ID": content,
        "MODEL_SEMANTIC_ID": semantic,
        "MODEL_OCCURRENCE_ID": occurrence,
        "TRAINING_TRANSFORMATION_ID": transform,
    }


def verify_manifest_and_build_identities() -> tuple[list[dict], dict]:
    manifest_path = ANTIGENCE_ROOT / "models/MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    numpy_ver = manifest.get("numpy_version", "unknown")
    entries: list[dict] = []
    verification: dict[str, str] = {}

    for item in manifest["entries"]:
        rel = item["path"]
        path = ANTIGENCE_ROOT / rel
        expected = item["sha256"]
        if not path.is_file():
            verification[rel] = "MISSING"
            continue
        actual = sha256_file(path)
        verification[rel] = "PASS" if actual == expected else "FAIL"
        name = Path(rel).stem.replace("_antibody", "")
        ids = _model_ids(
            name,
            actual,
            item.get("detector_type", "NegativeSelectionClassifier"),
            item.get("source_dataset", "unknown"),
            item.get("training_date", "unknown"),
            numpy_ver,
            FROZEN_ANTIGENCE_SHA,
        )
        entries.append(
            {
                "model_name": name,
                "admission_class": "CANONICAL_ANTIBODY",
                "canonical": bool(item.get("canonical", False)),
                "path": rel,
                "sha256": actual,
                "detector_type": item.get("detector_type"),
                "source_dataset": item.get("source_dataset"),
                "training_date": item.get("training_date"),
                "numpy_version": numpy_ver,
                "antigence_git_sha": FROZEN_ANTIGENCE_SHA,
                **ids,
            }
        )

    # Experimental SciFact cells — admit separately; do not promote substitutes
    for label, paths, detector in [
        ("scifact_bcell", SCIFACT_BCELL_PATHS, "BCellAgent"),
        ("scifact_nk", SCIFACT_NK_PATHS, "NKCellAgent"),
    ]:
        found = next((p for p in paths if p.is_file()), None)
        expected_sha = FROZEN_SCIFACT_BCELL_SHA256 if label == "scifact_bcell" else FROZEN_SCIFACT_NK_SHA256
        if found:
            actual = sha256_file(found)
            sha_ok = actual == expected_sha
            ids = _model_ids(
                label,
                actual,
                detector,
                "SciFact",
                "2026-01-05",
                numpy_ver,
                FROZEN_ANTIGENCE_SHA,
            )
            entries.append(
                {
                    "model_name": label,
                    "admission_class": "EXPERIMENTAL_TRAINED_CELL",
                    "canonical": False,
                    "path": str(found),
                    "sha256": actual,
                    "sha256_verified": sha_ok,
                    "admission_source": "immunos_runs_frozen_2026-01-05" if str(found).startswith("/Users/byron/projects/.immunos") else "antigence_repo",
                    "detector_type": detector,
                    "source_dataset": "SciFact",
                    "training_date": "2026-01-05",
                    "numpy_version": numpy_ver,
                    "antigence_git_sha": FROZEN_ANTIGENCE_SHA,
                    **ids,
                }
            )
            verification[label] = "PASS" if sha_ok else "FAIL_SHA256"
        else:
            verification[label] = "MISSING_CHECKPOINT"
            entries.append(
                {
                    "model_name": label,
                    "admission_class": "EXPERIMENTAL_TRAINED_CELL",
                    "admission_state": "BLOCKED",
                    "canonical": False,
                    "path": None,
                    "sha256": None,
                    "detector_type": detector,
                    "source_dataset": "SciFact",
                    "note": "Frozen checkpoint not on disk; no hallucination-model substitution",
                    "antigence_git_sha": FROZEN_ANTIGENCE_SHA,
                }
            )

    return entries, {"manifest_verification": verification, "frozen_git_sha": FROZEN_ANTIGENCE_SHA}


@dataclass
class AntigenceRuntime:
    citation_system: Any | None = None
    bcell: Any | None = None
    nk: Any | None = None
    embedder: Any | None = None
    model_sha256_bundle: str = ""
    load_errors: dict[str, str] = field(default_factory=dict)


def _install_immunos_mcp_compat() -> None:
    """Pickle checkpoints may reference pre-rename immunos_mcp module paths."""
    import types

    import antigence.algorithms.negsel as negsel

    pkg = types.ModuleType("immunos_mcp")
    algo = types.ModuleType("immunos_mcp.algorithms")
    sys.modules.setdefault("immunos_mcp", pkg)
    sys.modules.setdefault("immunos_mcp.algorithms", algo)
    sys.modules.setdefault("immunos_mcp.algorithms.negsel", negsel)


def load_runtime() -> AntigenceRuntime:
    rt = AntigenceRuntime()
    src = str(ANTIGENCE_ROOT / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    _install_immunos_mcp_compat()

    try:
        from antigence.agents.citation_antibodies import CitationAntibodySystem

        system = CitationAntibodySystem()
        ab_dir = ANTIGENCE_ROOT / ".antigence/antibodies"
        system.load_all(str(ab_dir))
        rt.citation_system = system
        shas = []
        for p in sorted(ab_dir.glob("*_antibody.pkl")):
            shas.append(sha256_file(p)[:16])
        rt.model_sha256_bundle = canonical_hash_v2({"canonical_antibody_shas": shas})
    except Exception as exc:  # pragma: no cover
        rt.load_errors["citation_antibodies"] = str(exc)

    try:
        from antigence.agents.bcell_agent import BCellAgent
        from antigence.agents.nk_cell_agent import NKCellAgent
        from antigence.core.antigen import Antigen

        for path in SCIFACT_BCELL_PATHS:
            if path.is_file():
                rt.bcell = BCellAgent.load_state(str(path))
                break
        for path in SCIFACT_NK_PATHS:
            if path.is_file():
                rt.nk = NKCellAgent.load_state(str(path))
                break
        try:
            from antigence.core.embeddings import SimpleTextEmbedder

            rt.embedder = SimpleTextEmbedder()
        except Exception:
            rt.embedder = None
        rt._Antigen = Antigen  # type: ignore[attr-defined]
    except Exception as exc:
        rt.load_errors["scifact_cells"] = str(exc)

    return rt


def _extract_doi(text: str) -> str | None:
    m = re.search(r"10\.\d{4,9}/\S+", text or "")
    return m.group(0).rstrip(".,)") if m else None


def _citation_vote(rt: AntigenceRuntime, text: str) -> dict[str, Any]:
    if not rt.citation_system:
        return {"available": False, "anomaly": False, "score": 0.0, "votes": {}}
    doi = _extract_doi(text)
    citation = {"doi": doi or "", "title": text[:200], "authors": "", "journal": "", "year": "", "pmid": ""}
    result = rt.citation_system.verify_citation(citation)
    d = result.to_dict()
    score = float(d.get("overall_confidence", 0.0))
    return {
        "available": True,
        "anomaly": bool(d.get("is_hallucinated")),
        "score": score,
        "votes": d.get("components", {}),
        "response": d.get("response"),
    }


def _scifact_votes(rt: AntigenceRuntime, text: str) -> dict[str, Any]:
    if not rt.bcell and not rt.nk:
        return {"available": False, "bcell_score": 0.0, "nk_score": 0.0, "anomaly": False}
    Antigen = getattr(rt, "_Antigen", None)
    if Antigen is None:
        return {"available": False, "bcell_score": 0.0, "nk_score": 0.0, "anomaly": False}
    antigen = Antigen.from_text(text, metadata={"domain": "protein-hinge"})
    emb = None
    if rt.embedder:
        try:
            emb = rt.embedder.embed(text)
        except Exception:
            emb = None
    bcell_score = 0.0
    nk_score = 0.0
    bcell_anomaly = False
    nk_anomaly = False
    if rt.bcell:
        rec = rt.bcell.recognize(antigen, antigen_embedding=emb)
        bcell_score = float(getattr(rec, "confidence", 0.0) or 0.0)
        bcell_anomaly = bcell_score < 0.55
    if rt.nk:
        res = rt.nk.detect_novelty(antigen, antigen_embedding=emb)
        nk_score = float(getattr(res, "anomaly_score", 0.0) or 0.0)
        nk_anomaly = bool(getattr(res, "is_anomaly", False))
    return {
        "available": True,
        "bcell_score": bcell_score,
        "nk_score": nk_score,
        "anomaly": bcell_anomaly or nk_anomaly,
        "bcell_anomaly": bcell_anomaly,
        "nk_anomaly": nk_anomaly,
    }


def detect_mutation_blind(
    mutated: dict[str, Any],
    baseline: dict[str, Any],
    object_type: str,
    rt: AntigenceRuntime,
) -> dict[str, Any]:
    """Detector path — MUST NOT read mutation truth / expected_* fields."""
    t0 = time.perf_counter()
    text = mutated.get("exact_text") or mutated.get("display_value") or mutated.get("doi") or json.dumps(mutated, sort_keys=True)
    base_text = baseline.get("exact_text") or baseline.get("display_value") or baseline.get("doi") or ""

    norm_m = normalize_text(str(text))
    norm_b = normalize_text(str(base_text))
    content_changed = mutated.get("CONTENT_ID") != baseline.get("CONTENT_ID")
    parent_changed = mutated.get("parent_id") != baseline.get("parent_id") and baseline.get("parent_id") is not None
    prov_changed = (
        mutated.get("source_commit") not in (None, baseline.get("source_commit"), PROVENANCE_CANONICAL)
        or mutated.get("source_blob_sha") != baseline.get("source_blob_sha")
    )

    cit = _citation_vote(rt, str(text))
    sci = _scifact_votes(rt, str(text))

    # Baseline-relative signals (allowed — not ground-truth labels)
    text_delta = norm_m != norm_b
    whitespace_only = text_delta and norm_m.replace(" ", "") == norm_b.replace(" ", "")

    signals: list[tuple[str, float]] = []
    if prov_changed:
        signals.append(("provenance", 0.95))
    if parent_changed:
        signals.append(("structure", 0.85))
    if content_changed and not whitespace_only:
        signals.append(("semantic_content", 0.75))
    elif whitespace_only:
        signals.append(("benign_whitespace", 0.15))
    if cit.get("anomaly"):
        signals.append(("citation", cit["score"]))
    if sci.get("available") and sci.get("anomaly"):
        signals.append(("scifact", max(sci.get("bcell_score", 0), sci.get("nk_score", 0))))

    anomaly_score = max((s for _, s in signals), default=0.1 if text_delta else 0.0)
    binary_anomaly = anomaly_score >= ANOMALY_THRESHOLD

    # Disposition from detector votes only
    if prov_changed:
        disposition = "PROVENANCE_BREAK"
    elif parent_changed and not content_changed:
        disposition = "STRUCTURE_CHANGE"
    elif whitespace_only and not content_changed:
        disposition = "PRESERVE_SEMANTIC"
    elif cit.get("anomaly") and object_type in {"Identifier", "Manifest"}:
        disposition = "ABSTAIN"
    elif sci.get("available") and sci.get("nk_anomaly") and "contradict" in str(text).lower():
        disposition = "CONTRADICTION_CHANGE"
    elif content_changed and binary_anomaly:
        disposition = "SEMANTIC_CHANGE"
    elif binary_anomaly:
        disposition = "ABSTAIN"
    else:
        disposition = "NO_CHANGE"

    # Distinct endpoints
    anomaly_detection = binary_anomaly or prov_changed or parent_changed or (content_changed and not whitespace_only)
    causal_localization = parent_changed or prov_changed or object_type == "SOT"
    claim_ceiling_disposition = "ELEVATE_REVIEW" if disposition in {"ABSTAIN", "SEMANTIC_CHANGE"} and "efficacy" in norm_m else "UNCHANGED"

    latency_ms = (time.perf_counter() - t0) * 1000.0
    model_sha = rt.model_sha256_bundle or FROZEN_ANTIGENCE_SHA
    return {
        "pipeline": "B4_ANTIGENCE_TRAINED_AIS",
        "anomaly_score": round(anomaly_score, 4),
        "binary_anomaly": binary_anomaly,
        "disposition": disposition,
        "terminal": disposition if sci.get("available") or cit.get("available") else "BLOCKED_PARTIAL_MODEL",
        "detector_votes": {
            "citation": cit,
            "scifact": sci,
            "signals": signals,
        },
        "threshold": ANOMALY_THRESHOLD,
        "latency_ms": round(latency_ms, 3),
        "model_git_sha": FROZEN_ANTIGENCE_SHA,
        "model_sha256": model_sha,
        "endpoints": {
            "ANOMALY_DETECTION": anomaly_detection,
            "SEMANTIC_DISPOSITION": disposition,
            "CAUSAL_LOCALIZATION": causal_localization,
            "CLAIM_CEILING_DISPOSITION": claim_ceiling_disposition,
        },
        "scifact_cells_available": sci.get("available", False),
    }


def score_b4_against_ground_truth(detection: dict[str, Any], gt: dict[str, Any]) -> dict[str, Any]:
    """Scoring layer — ground truth used only here, not in detect_mutation_blind."""
    from fcg_core.pipeline_baselines import _expected_disposition, _gt_flags

    expected = _expected_disposition(gt)
    flags = _gt_flags(gt)
    disp = detection["disposition"]

    disp_to_expected = {
        "PRESERVE_SEMANTIC": {"PRESERVE_SEMANTIC", "NO_CHANGE", "DUPLICATE_ALIAS"},
        "NO_CHANGE": {"NO_CHANGE", "PRESERVE_SEMANTIC", "DUPLICATE_ALIAS"},
        "ABSTAIN": {"ABSTAIN_OR_REJECT", "ABSTAIN"},
        "PROVENANCE_BREAK": {"PROVENANCE_BREAK"},
        "CONTRADICTION_CHANGE": {"CONTRADICTION_CHANGE"},
        "SEMANTIC_CHANGE": {"SEMANTIC_CHANGE"},
        "STRUCTURE_CHANGE": {"STRUCTURE_CHANGE"},
    }
    correct_semantic = expected in disp_to_expected.get(disp, set())

    return {
        **detection,
        "correct_semantic_disposition": correct_semantic,
        "correct_downstream_localization": detection["endpoints"]["CAUSAL_LOCALIZATION"]
        and (flags["structure"] or flags["provenance"] or bool(gt.get("expected_affected_SOT_ids"))),
        "false_semantic_promotion": flags["benign"] and disp not in {"PRESERVE_SEMANTIC", "NO_CHANGE"},
        "false_claim_acceptance": flags["unsupported"] and disp not in {"ABSTAIN", "REJECT", "INSUFFICIENT"},
        "anomaly_detection_correct": detection["endpoints"]["ANOMALY_DETECTION"]
        == (flags["semantic"] or flags["provenance"] or flags["contradiction"] or flags["structure"] or flags["unsupported"] or not flags["benign"]),
    }


def run_b4_antigence(mutated: dict[str, Any], baseline: dict[str, Any], object_type: str, rt: AntigenceRuntime, gt: dict[str, Any]) -> dict[str, Any]:
    detection = detect_mutation_blind(mutated, baseline, object_type, rt)
    return score_b4_against_ground_truth(detection, gt)
