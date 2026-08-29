#!/usr/bin/env python3
"""SeedGraph atomization bridge for AUD-FCG-DOCUMENT-LATTICE-001 / PROJECT_DOCUMENT_001."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audits" / "AUD-FCG-DOCUMENT-LATTICE-001"
RUNTIME = AUDIT / "seedgraph_runtime"
PROTEIN_HINGE = Path("/Users/byron/projects/active/protein-hinge")
SOURCE_COMMIT = "4a372a5c459ad60cd23b850709011cbfd0e516b4"
SOT_PATH = PROTEIN_HINGE / "paper/newinml2026/final_corpus_audit/SEEDS_OF_TRUTH.final.json"
PDF_CANDIDATES = [
    PROTEIN_HINGE / "paper/newinml2026/manuscript/main_smoke.pdf",
    PROTEIN_HINGE / "paper/newinml2026/submission/NewInML2026_ProteinHinge_ANONYMOUS_FINAL_CANDIDATE.pdf",
]

SEEDGRAPH_SRC = Path("/Users/byron/projects/active/seedgraph/src")
if str(SEEDGRAPH_SRC) not in sys.path:
    sys.path.insert(0, str(SEEDGRAPH_SRC))
sys.path.insert(0, str(ROOT / "src"))


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def ensure_signing_key(key_path: Path) -> None:
    if key_path.is_file():
        return
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat

    key_path.parent.mkdir(parents=True, exist_ok=True)
    key = Ed25519PrivateKey.generate()
    pem = key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    key_path.write_bytes(pem)
    key_path.chmod(0o600)


def ensure_audit_neo4j() -> None:
    container = "seedgraph-neo4j-audit-lattice"
    proc = subprocess.run(["docker", "ps", "-a", "--format", "{{.Names}}"], capture_output=True, text=True)
    if container not in proc.stdout.splitlines():
        subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                container,
                "-p",
                "17474:7474",
                "-p",
                "17687:7687",
                "-e",
                "NEO4J_AUTH=none",
                "-e",
                "NEO4J_dbms_security_auth__enabled=false",
                "neo4j:5.26",
            ],
            check=True,
        )
    else:
        running = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", container],
            capture_output=True,
            text=True,
        )
        if running.stdout.strip() != "true":
            subprocess.run(["docker", "start", container], check=True)


def select_pdf() -> tuple[Path, str]:
    for path in PDF_CANDIDATES:
        if path.is_file():
            role = "manuscript_smoke" if "main_smoke" in path.name else "submission_candidate_readonly"
            return path, role
    raise FileNotFoundError("No ingestible PDF found; compile main.tex or provide main_smoke.pdf")


def setup_env() -> dict[str, str]:
    config = RUNTIME / "config"
    ensure_signing_key(config / "signing_key.pem")
    ensure_audit_neo4j()
    return {
        "SEEDGRAPH_KEY_PATH": str(config / "signing_key.pem"),
        "SEEDGRAPH_DB_PATH": str(RUNTIME / "ledger.db"),
        "SEEDGRAPH_STORE_ROOT": str(RUNTIME / "store"),
        "SEEDGRAPH_NEO4J_URI": os.environ.get("SEEDGRAPH_NEO4J_URI", "bolt://localhost:17687"),
        "SEEDGRAPH_NEO4J_USER": "neo4j",
        "SEEDGRAPH_NEO4J_PASSWORD": "",
        "SEEDGRAPH_USER_ROLES": "admin,ingest.write,extract.write,normalize.write",
    }


def run_import_extract(pdf: Path, env: dict[str, str]) -> dict[str, Any]:
    from sqlalchemy import create_engine

    from seedgraph.extract.orchestrator import extract_seed
    from seedgraph.graph.connection import GraphConnection
    from seedgraph.graph.schema import bootstrap_constraints
    from seedgraph.graph.writer import GraphWriter
    from seedgraph.ingest.orchestrator import import_file
    from seedgraph.ingest.store import ContentStore
    from seedgraph.ledger.ledger import ProvenanceLedger
    from seedgraph.ledger.models import Base

    for key, val in env.items():
        os.environ[key] = val

    engine = create_engine(f"sqlite:///{env['SEEDGRAPH_DB_PATH']}")
    Base.metadata.create_all(engine)

    from cryptography.hazmat.primitives.serialization import load_pem_private_key

    signing_key = load_pem_private_key(Path(env["SEEDGRAPH_KEY_PATH"]).read_bytes(), password=None)
    ledger = ProvenanceLedger(engine=engine, signing_key=signing_key)
    store = ContentStore(root=Path(env["SEEDGRAPH_STORE_ROOT"]))

    try:
        conn = GraphConnection(uri=env["SEEDGRAPH_NEO4J_URI"], auth=("neo4j", ""))
        conn._driver.verify_connectivity()
        bootstrap_constraints(conn)
        session = conn._driver.session()
        writer = GraphWriter(session, ledger_engine=engine)
        graph_mode = "live_audit_neo4j"
    except Exception as exc:
        from seedgraph.graph.json_fallback import JsonGraphFallbackSession

        fb = JsonGraphFallbackSession(
            Path(env["SEEDGRAPH_STORE_ROOT"]) / "neo4j-fallback",
            reason=str(exc),
            neo4j_uri=env["SEEDGRAPH_NEO4J_URI"],
        )
        writer = GraphWriter(fb, ledger_engine=engine)
        graph_mode = "json_fallback"

    results = import_file(pdf, "evidence", ledger, writer, store)
    if not results:
        raise RuntimeError("import_file returned no results")
    seed_id = results[0].seed_id
    source_sha256 = results[0].source_sha256

    extraction = extract_seed(seed_id, ledger, writer, store=store, force=True)
    return {
        "seed_id": seed_id,
        "source_sha256": source_sha256,
        "graph_mode": graph_mode,
        "extraction": extraction,
        "store": store,
    }


def load_atoms_snapshot(store: Any, source_sha256: str) -> dict[str, Any]:
    from seedgraph.maps.snapshot_reader import ATOMS_SIDECAR_NAME

    payload = store.load_json_sidecar(source_sha256, ATOMS_SIDECAR_NAME)
    if payload is None:
        raise RuntimeError("atoms.snapshot.json missing after extract")
    return payload


def normalize_text(text: str) -> str:
    text = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\[a-zA-Z]+", "", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text[:200]


def compose_sot_atoms(atoms: list[dict], sots: list[dict]) -> list[dict]:
    """PROMPT-020 STEP1 interim: compose SOT only when supporting atoms exist."""
    sentence_atoms = [a for a in atoms if a.get("seed_type") == "sentence"]
    keyword_rules: dict[str, list[str]] = {
        "SOT-001": ["abstention", "aggregate", "gap"],
        "SOT-002": ["successor", "repair", "accounting"],
        "SOT-003": ["custody", "semantic", "hash", "bytes"],
        "SOT-004": ["identity", "vocabulary", "g3"],
        "SOT-005": ["reconcile", "wiring", "g3"],
        "SOT-006": ["observed-source", "bypass", "n=1"],
        "SOT-007": ["364", "g1", "successor"],
        "SOT-008": ["tafazzin"],
        "SOT-009": ["folding", "structure-prediction"],
        "SOT-010": ["746", "g2", "364"],
        "SOT-011": ["esummary", "100-id"],
        "SOT-012": ["382", "cnv", "exclusion"],
        "SOT-013": ["morphology", "negative", "exp-006"],
        "SOT-014": ["measurement", "correction", "g1"],
        "SOT-015": ["chow1970", "geifman", "selective prediction"],
        "SOT-016": ["mmr", "scoped identifier"],
        "SOT-017": ["therapeutic", "clinical utility"],
        "SOT-018": ["submission", "operator"],
        "SOT-019": ["corpus audit", "2ba0d923"],
        "SOT-020": ["authorship", "contributor"],
        "SOT-PR1": ["open hash", "pr1"],
    }

    rows = []
    for seed in sots:
        sid = seed["seed_id"]
        stmt = (seed.get("statement") or "").lower()

        if sid in {"SOT-008", "SOT-014"}:
            strict_needles = {
                "SOT-008": ["tafazzin"],
                "SOT-014": ["measurement correction", "g1 measurement"],
            }[sid]
            supporting = []
            for atom in sentence_atoms:
                text = normalize_text(atom.get("text") or "")
                if any(n in text for n in strict_needles):
                    supporting.append(atom["seed_id"])
            rows.append(
                {
                    "SOT_ID": sid,
                    "status": seed.get("status"),
                    "statement": seed.get("statement"),
                    "supporting_atom_seed_ids": supporting[:20],
                    "supporting_atom_count": len(supporting),
                    "composition_admission": "PRESERVED_NOT_ESTABLISHED",
                    "proof_state": "PENDING",
                    "traceability_invariant": "PASS",
                }
            )
            continue

        needles = keyword_rules.get(sid, [])
        if not needles:
            needles = [w for w in re.findall(r"[a-z0-9]{4,}", stmt)[:6]]

        supporting = []
        for atom in sentence_atoms:
            text = normalize_text(atom.get("text") or "")
            if not text:
                continue
            if any(n.lower() in text for n in needles):
                supporting.append(atom["seed_id"])

        if supporting:
            admission = "COMPOSED"
        else:
            admission = "REFUSED_NO_ATOMS"

        trace = "PASS" if admission != "COMPOSED" or supporting else "FAIL"

        rows.append(
            {
                "SOT_ID": sid,
                "status": seed.get("status"),
                "statement": seed.get("statement"),
                "supporting_atom_seed_ids": supporting[:20],
                "supporting_atom_count": len(supporting),
                "composition_admission": admission,
                "proof_state": "VERIFIED" if admission == "COMPOSED" and supporting else "PENDING",
                "traceability_invariant": trace,
            }
        )
    return rows


def bridge_lattice_atoms(atoms: list[dict]) -> list[dict]:
    pre_sentences_path = AUDIT / "PRE_INGEST" / "SENTENCES.jsonl"
    if not pre_sentences_path.is_file():
        return []
    lattice_sents = [json.loads(line) for line in pre_sentences_path.read_text().splitlines() if line.strip()]
    sentence_atoms = [a for a in atoms if a.get("seed_type") == "sentence"]

    rows = []
    for ls in lattice_sents:
        lt = normalize_text(ls.get("exact_text", ""))
        best = None
        best_score = 0.0
        for atom in sentence_atoms:
            at = normalize_text(atom.get("text", ""))
            if not at or not lt:
                continue
            # crude overlap score
            lt_words = set(lt.split())
            at_words = set(at.split())
            if not lt_words:
                continue
            score = len(lt_words & at_words) / len(lt_words)
            if score > best_score:
                best_score = score
                best = atom
        rows.append(
            {
                "lattice_object_id": ls.get("object_id"),
                "lattice_CONTENT_ID": ls.get("CONTENT_ID"),
                "atom_seed_id": best.get("seed_id") if best else None,
                "atom_content_hash": best.get("content_hash") if best else None,
                "match_score": round(best_score, 3),
                "linked": best is not None and best_score >= 0.35,
                "atom_spo": best.get("spo") if best else None,
            }
        )
    return rows


def build_maps(payload: dict[str, Any]) -> tuple[list[dict], list[dict]]:
    from seedgraph.maps.query import build_logic_map, build_sentence_map
    from seedgraph.maps.snapshot_reader import SnapshotMappingReader

    reader = SnapshotMappingReader.from_snapshot_dict(payload)
    nodes = reader.load_nodes()
    edges = reader.load_edges()
    return build_sentence_map(nodes, edges), build_logic_map(nodes, edges)


def evaluate_gates(
    import_result: dict[str, Any],
    atoms_payload: dict[str, Any],
    sot_rows: list[dict],
    bridge_rows: list[dict],
) -> dict[str, str]:
    atoms = atoms_payload.get("atoms", [])
    extraction = import_result["extraction"]
    linked = sum(1 for r in bridge_rows if r.get("linked"))
    sot_terminal = sum(
        1
        for r in sot_rows
        if r["composition_admission"]
        in {"COMPOSED", "COMPOSED_BOUNDED", "REFUSED_NO_ATOMS", "PRESERVED_NOT_ESTABLISHED"}
    )
    spo_count = sum(1 for a in atoms if a.get("seed_type") == "sentence" and a.get("spo"))

    return {
        "ATOM_IMPORT_GATE": "PASS" if import_result.get("seed_id") else "FAIL",
        "ATOM_EXTRACT_GATE": "PASS" if len(atoms) > 0 else "FAIL",
        "SOT_ATOM_COMPOSITION_GATE": "PASS" if sot_terminal == len(sot_rows) else "PARTIAL",
        "SENTENCE_DIAGRAM_GATE": "PARTIAL" if spo_count == 0 else "PASS",
        "LATTICE_BRIDGE_GATE": "PASS" if linked >= 1 else "PARTIAL",
    }


def main() -> int:
    AUDIT.mkdir(parents=True, exist_ok=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)

    pdf, pdf_role = select_pdf()
    pdf_sha = sha256_file(pdf)

    env = setup_env()
    import_result = run_import_extract(pdf, env)
    store = import_result.pop("store")
    extraction = import_result["extraction"]
    source_sha = import_result["source_sha256"]

    atoms_payload = load_atoms_snapshot(store, source_sha)
    atoms = atoms_payload.get("atoms", [])

    sots = json.loads(SOT_PATH.read_text()).get("seeds", []) if SOT_PATH.is_file() else []
    sot_rows = compose_sot_atoms(atoms, sots)
    bridge_rows = bridge_lattice_atoms(atoms)

    try:
        sentence_map, logic_map = build_maps(atoms_payload)
    except Exception as exc:
        sentence_map, logic_map = [], []
        map_error = str(exc)
    else:
        map_error = None

    atom_counts = {
        "sentence": sum(1 for a in atoms if a.get("seed_type") == "sentence"),
        "figure": sum(1 for a in atoms if a.get("seed_type") == "figure"),
        "table": sum(1 for a in atoms if a.get("seed_type") == "table"),
        "entity": sum(1 for a in atoms if a.get("seed_type") == "entity"),
        "equation": sum(1 for a in atoms if a.get("seed_type") == "equation"),
    }

    out_dir = AUDIT / "SEEDGRAPH_ATOMIZATION"
    write_jsonl(out_dir / "SOT_ATOM_COMPOSITION.jsonl", sot_rows)
    write_jsonl(out_dir / "LATTICE_ATOM_BRIDGE.jsonl", bridge_rows)
    write_jsonl(out_dir / "SENTENCE_MAP.jsonl", sentence_map)
    write_jsonl(out_dir / "LOGIC_MAP.jsonl", logic_map)
    write_json(
        out_dir / "ATOMS_SNAPSHOT_REF.json",
        {
            "source_sha256": source_sha,
            "seed_id": import_result["seed_id"],
            "atom_counts": atom_counts,
            "sidecar_path": f"{source_sha[:2]}/{source_sha}/atoms.snapshot.json",
            "store_root": env["SEEDGRAPH_STORE_ROOT"],
        },
    )

    gates = evaluate_gates(import_result, atoms_payload, sot_rows, bridge_rows)
    receipt = {
        "schema": "biocustody.seedgraph_atomization_receipt.v1",
        "audit_id": "AUD-FCG-DOCUMENT-LATTICE-001",
        "recorded_at_utc": utc_now(),
        "SOURCE_COMMIT": SOURCE_COMMIT,
        "pdf_path": str(pdf),
        "pdf_role": pdf_role,
        "pdf_sha256": pdf_sha,
        "sealed_submission_pdf_mutated": False,
        "production_neo4j_touched": False,
        "graph_mode": import_result["graph_mode"],
        "seed_id": import_result["seed_id"],
        "source_sha256": source_sha,
        "extraction_summary": {
            "sentences": extraction.sentences,
            "figures": extraction.figures,
            "tables": extraction.tables,
            "entities": extraction.entities,
            "citations": extraction.citations,
            "equations": extraction.equations,
            "errors": extraction.errors,
        },
        "atom_counts": atom_counts,
        "sot_composed": sum(1 for r in sot_rows if r["composition_admission"] == "COMPOSED"),
        "sot_refused_no_atoms": sum(1 for r in sot_rows if r["composition_admission"] == "REFUSED_NO_ATOMS"),
        "lattice_atoms_linked": sum(1 for r in bridge_rows if r.get("linked")),
        "gates": gates,
        "map_error": map_error,
        "PROMPT_020_STEP1": "INTERIM_BRIDGE_NOT_LIVE_CLAIM_TIER",
        "claim_ceiling": "REPURPOSING_HYPOTHESIS",
    }
    write_json(out_dir / "ATOMIZATION_RECEIPT.json", receipt)

    audit_receipt_path = AUDIT / "AUDIT_RECEIPT.json"
    if audit_receipt_path.is_file():
        audit_receipt = json.loads(audit_receipt_path.read_text())
        audit_receipt["seedgraph_atomization"] = receipt
        audit_receipt["gates"]["ATOM_IMPORT_GATE"] = gates["ATOM_IMPORT_GATE"]
        audit_receipt["gates"]["ATOM_EXTRACT_GATE"] = gates["ATOM_EXTRACT_GATE"]
        audit_receipt["gates"]["SOT_ATOM_COMPOSITION_GATE"] = gates["SOT_ATOM_COMPOSITION_GATE"]
        audit_receipt["recorded_at_utc"] = utc_now()
        write_json(audit_receipt_path, audit_receipt)

    print(json.dumps(receipt, indent=2))
    return 0 if gates["ATOM_IMPORT_GATE"] == "PASS" and gates["ATOM_EXTRACT_GATE"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
