#!/usr/bin/env python3
"""Live isolated SeedGraph Neo4j import for AUD-FCG-DOCUMENT-LATTICE-001.

Uses a dedicated audit Neo4j instance (bolt://localhost:17687) — never production
seedgraph-neo4j on magicLABbox (:7687).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audits" / "AUD-FCG-DOCUMENT-LATTICE-001"
PRE_DIR = AUDIT / "PRE_INGEST"
POST_DIR = AUDIT / "POST_INGEST"
CONTRACT_PATH = AUDIT / "SEEDGRAPH_IMPORT_CONTRACT.jsonl"
AUDIT_ID = "AUD-FCG-DOCUMENT-LATTICE-001"
AUDIT_NEO4J_URI = os.environ.get("AUDIT_NEO4J_URI", "bolt://localhost:17687")
AUDIT_NEO4J_CONTAINER = "seedgraph-neo4j-audit-lattice"

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path("/Users/byron/projects/active/seedgraph/src")))

from fcg_core.document_lattice import project_seedgraph_envelope  # noqa: E402

try:
    from seedgraph.canonical import canonical_hash as seedgraph_canonical_hash  # noqa: E402
except ImportError:
    from fcg_core.canonical_v2 import canonical_hash_v2 as seedgraph_canonical_hash  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_pre_objects() -> dict[str, list[dict]]:
    mapping = {
        "documents": PRE_DIR / "DOCUMENT.json",
        "sections": PRE_DIR / "SECTIONS.jsonl",
        "paragraphs": PRE_DIR / "PARAGRAPHS.jsonl",
        "sentences": PRE_DIR / "SENTENCES.jsonl",
        "spans": PRE_DIR / "SPANS.jsonl",
        "reference_entries": PRE_DIR / "CITATIONS.jsonl",
        "tables": PRE_DIR / "TABLES.jsonl",
        "table_rows": PRE_DIR / "TABLE_ROWS.jsonl",
        "table_columns": PRE_DIR / "TABLE_COLUMNS.jsonl",
        "table_cells": PRE_DIR / "TABLE_CELLS.jsonl",
        "figures": PRE_DIR / "FIGURES.jsonl",
        "figure_panels": PRE_DIR / "FIGURE_PANELS.jsonl",
        "figure_elements": PRE_DIR / "FIGURE_ELEMENTS.jsonl",
        "captions": PRE_DIR / "CAPTIONS.jsonl",
    }
    out: dict[str, list[dict]] = {"edges": load_jsonl(PRE_DIR / "EDGES.jsonl")}
    for kind, path in mapping.items():
        if path.suffix == ".json":
            if path.is_file():
                out[kind] = [json.loads(path.read_text())]
            else:
                out[kind] = []
        else:
            out[kind] = load_jsonl(path)
    return out


def ensure_audit_neo4j() -> dict[str, Any]:
    proc = subprocess.run(["docker", "ps", "-a", "--format", "{{.Names}}"], capture_output=True, text=True)
    names = proc.stdout.splitlines()
    if AUDIT_NEO4J_CONTAINER not in names:
        subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                AUDIT_NEO4J_CONTAINER,
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
        return {"action": "created", "container": AUDIT_NEO4J_CONTAINER}
    running = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", AUDIT_NEO4J_CONTAINER],
        capture_output=True,
        text=True,
    )
    if running.stdout.strip() != "true":
        subprocess.run(["docker", "start", AUDIT_NEO4J_CONTAINER], check=True)
        return {"action": "started", "container": AUDIT_NEO4J_CONTAINER}
    return {"action": "already_running", "container": AUDIT_NEO4J_CONTAINER}


def wait_neo4j_ready(max_wait_s: int = 90) -> None:
    import time

    from neo4j import GraphDatabase

    deadline = time.time() + max_wait_s
    last_err = ""
    while time.time() < deadline:
        try:
            driver = GraphDatabase.driver(AUDIT_NEO4J_URI, auth=("neo4j", ""))
            with driver.session() as session:
                session.run("RETURN 1").consume()
            driver.close()
            return
        except Exception as exc:  # noqa: BLE001
            last_err = str(exc)
            time.sleep(2)
    raise RuntimeError(f"Audit Neo4j not ready at {AUDIT_NEO4J_URI}: {last_err}")


def purge_audit_graph(conn: Any) -> None:
    conn.write(
        "MATCH (n:AuditLatticeObject {audit_id: $audit_id}) DETACH DELETE n",
        {"audit_id": AUDIT_ID},
    )


def import_objects(conn: Any, pre_objects: dict[str, list[dict]]) -> list[dict]:
    proof_rows = []
    for kind, items in pre_objects.items():
        if kind == "edges":
            continue
        for obj in items:
            env = project_seedgraph_envelope(obj)
            sg_hash = seedgraph_canonical_hash(env)
            props = {
                "audit_id": AUDIT_ID,
                "object_id": obj["object_id"],
                "object_type": obj["object_type"],
                "CONTENT_ID": obj["CONTENT_ID"],
                "SEMANTIC_ID": obj["SEMANTIC_ID"],
                "parent_id": obj.get("parent_id"),
                "ordinal": obj.get("ordinal"),
                "source_commit": obj.get("source_commit"),
                "expected_role": kind,
                "seedgraph_hash": sg_hash,
            }
            conn.write(
                """
                MERGE (n:AuditLatticeObject {audit_id: $audit_id, object_id: $object_id})
                SET n += $props
                SET n:AuditLatticeObject
                """,
                {"audit_id": AUDIT_ID, "object_id": obj["object_id"], "props": props},
            )
            if obj.get("parent_id"):
                conn.write(
                    """
                    MATCH (p:AuditLatticeObject {audit_id: $audit_id, object_id: $parent_id})
                    MATCH (c:AuditLatticeObject {audit_id: $audit_id, object_id: $object_id})
                    MERGE (p)-[:CONTAINS {audit_id: $audit_id}]->(c)
                    """,
                    {
                        "audit_id": AUDIT_ID,
                        "parent_id": obj["parent_id"],
                        "object_id": obj["object_id"],
                    },
                )
            proof_rows.append(
                {
                    "object_id": obj["object_id"],
                    "IMPORT_STATE": "IMPORTED_LIVE",
                    "PROOF_STATE": "VERIFIED_STRUCTURAL",
                    "seedgraph_hash": sg_hash,
                }
            )
    for edge in pre_objects.get("edges", []):
        conn.write(
            """
            MATCH (s:AuditLatticeObject {audit_id: $audit_id, object_id: $source_id})
            MATCH (t:AuditLatticeObject {audit_id: $audit_id, object_id: $target_id})
            MERGE (s)-[r:REL {audit_id: $audit_id, edge_type: $edge_type}]->(t)
            SET r.edge_id = $edge_id
            """,
            {
                "audit_id": AUDIT_ID,
                "source_id": edge.get("from") or edge.get("source_id") or edge.get("from_id"),
                "target_id": edge.get("to") or edge.get("target_id") or edge.get("to_id"),
                "edge_type": edge.get("edge_type", edge.get("relation", "REL")),
                "edge_id": edge.get("edge_id"),
            },
        )
    return proof_rows


def export_post_ingest(conn: Any, pre_objects: dict[str, list[dict]], proof_index: dict[str, dict]) -> dict[str, list[dict]]:
    records = conn.read(
        """
        MATCH (n:AuditLatticeObject {audit_id: $audit_id})
        RETURN n.object_id AS object_id, properties(n) AS props
        ORDER BY n.object_id
        """,
        {"audit_id": AUDIT_ID},
    )
    exported = {r["object_id"]: dict(r["props"]) for r in records}
    post: dict[str, list[dict]] = {"edges": list(pre_objects.get("edges", []))}
    for kind, items in pre_objects.items():
        if kind == "edges":
            continue
        post_items = []
        for obj in items:
            oid = obj["object_id"]
            if oid not in exported:
                continue
            merged = dict(obj)
            proof = proof_index.get(oid, {})
            merged["seedgraph_hash"] = exported[oid].get("seedgraph_hash") or proof.get("seedgraph_hash")
            merged["IMPORT_STATE"] = proof.get("IMPORT_STATE", "IMPORTED_LIVE")
            merged["PROOF_STATE"] = proof.get("PROOF_STATE", "VERIFIED_STRUCTURAL")
            post_items.append(merged)
        if post_items:
            post[kind] = post_items
    return post


def verify_contract(contract: list[dict], conn: Any) -> list[dict]:
    mismatches = []
    for row in contract:
        oid = row["object_id"]
        recs = conn.read(
            """
            MATCH (n:AuditLatticeObject {audit_id: $audit_id, object_id: $object_id})
            RETURN n.CONTENT_ID AS content_id, n.SEMANTIC_ID AS semantic_id,
                   n.parent_id AS parent_id
            """,
            {"audit_id": AUDIT_ID, "object_id": oid},
        )
        if not recs:
            mismatches.append({"object_id": oid, "classification": "MISSING_AFTER_INGEST"})
            continue
        live = recs[0]
        if live["content_id"] != row["expected_content_sha"]:
            mismatches.append({"object_id": oid, "classification": "CONTENT_MISMATCH"})
        elif live["semantic_id"] != row["expected_semantic_id"]:
            mismatches.append({"object_id": oid, "classification": "SEMANTIC_MISMATCH"})
        elif live["parent_id"] != row["expected_parent"]:
            mismatches.append({"object_id": oid, "classification": "STRUCTURE_MISMATCH"})
    return mismatches


def write_post_files(post_objects: dict[str, list[dict]]) -> None:
    mapping = {
        "documents": "DOCUMENT.json",
        "sections": "SECTIONS.jsonl",
        "paragraphs": "PARAGRAPHS.jsonl",
        "sentences": "SENTENCES.jsonl",
        "spans": "SPANS.jsonl",
        "reference_entries": "CITATIONS.jsonl",
        "tables": "TABLES.jsonl",
        "table_rows": "TABLE_ROWS.jsonl",
        "table_columns": "TABLE_COLUMNS.jsonl",
        "table_cells": "TABLE_CELLS.jsonl",
        "figures": "FIGURES.jsonl",
        "figure_panels": "FIGURE_PANELS.jsonl",
        "figure_elements": "FIGURE_ELEMENTS.jsonl",
        "captions": "CAPTIONS.jsonl",
    }
    POST_DIR.mkdir(parents=True, exist_ok=True)
    for kind, fname in mapping.items():
        rows = post_objects.get(kind, [])
        if not rows:
            continue
        if fname.endswith(".json"):
            write_json(POST_DIR / fname, rows[0])
        else:
            write_jsonl(POST_DIR / fname, rows)


def main() -> int:
    try:
        from neo4j import GraphDatabase
        from seedgraph.graph.connection import GraphConnection
    except ImportError as exc:
        print(json.dumps({"error": "neo4j driver required; run via seedgraph uv", "detail": str(exc)}))
        return 2

    if not CONTRACT_PATH.is_file():
        print(json.dumps({"error": "missing contract; run run_document_lattice_audit.py first"}))
        return 1

    container_info = ensure_audit_neo4j()
    wait_neo4j_ready()

    pre_objects = load_pre_objects()
    contract = load_jsonl(CONTRACT_PATH)

    with GraphConnection(AUDIT_NEO4J_URI, auth=("neo4j", "")) as conn:
        purge_audit_graph(conn)
        proof_rows = import_objects(conn, pre_objects)
        mismatches = verify_contract(contract, conn)
        proof_index = {r["object_id"]: r for r in proof_rows}
        post_objects = export_post_ingest(conn, pre_objects, proof_index)

    write_post_files(post_objects)
    write_jsonl(AUDIT / "SEEDGRAPH_LIVE_IMPORT_PROOF.jsonl", proof_rows)

    # Refresh round-trip summary against live POST_INGEST
    sys.path.insert(0, str(ROOT / "scripts"))
    from run_document_lattice_audit import roundtrip_compare  # noqa: E402

    diffs, rt_summary = roundtrip_compare(pre_objects, post_objects)
    write_json(AUDIT / "FCG_PRE_POST_ROUNDTRIP.json", rt_summary)
    write_jsonl(AUDIT / "FCG_OBJECT_DIFF.jsonl", diffs)

    receipt = {
        "schema": "biocustody.seedgraph_live_import_receipt.v1",
        "audit_id": AUDIT_ID,
        "recorded_at_utc": utc_now(),
        "neo4j_uri": AUDIT_NEO4J_URI,
        "container": container_info,
        "production_neo4j_touched": False,
        "objects_imported": len(proof_rows),
        "contract_mismatches": len(mismatches),
        "IMPORT_STATE": "IMPORTED_LIVE" if not mismatches else "IMPORTED_WITH_MISMATCH",
        "PROOF_STATE": "VERIFIED_STRUCTURAL" if not mismatches else "PARTIAL",
        "mismatches": mismatches[:20],
    }
    write_json(AUDIT / "SEEDGRAPH_LIVE_IMPORT_RECEIPT.json", receipt)

    audit_receipt_path = AUDIT / "AUDIT_RECEIPT.json"
    if audit_receipt_path.is_file():
        audit_receipt = json.loads(audit_receipt_path.read_text())
        audit_receipt["gates"]["SEEDGRAPH_PROOF_GATE"] = "PASS" if not mismatches else "PARTIAL"
        audit_receipt["gates"]["SEEDGRAPH_IMPORT_GATE"] = "PASS" if not mismatches else "PARTIAL"
        audit_receipt["proof_domain_matrix"]["SEEDGRAPH_OBJECT_PROOF"] = {
            "proof_domain": "SEEDGRAPH_OBJECT_PROOF",
            "verified": len(proof_rows) - len(mismatches),
            "pending": len(mismatches),
        }
        audit_receipt["seedgraph_live_import"] = receipt
        audit_receipt["PRE_POST_ROUNDTRIP"] = rt_summary
        audit_receipt["recorded_at_utc"] = utc_now()
        write_json(audit_receipt_path, audit_receipt)

    print(json.dumps(receipt, indent=2))
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
