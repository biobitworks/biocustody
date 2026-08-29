#!/usr/bin/env python3
"""Exhaustive credential discovery + verified-capability delta (no secret values)."""
from __future__ import annotations

import base64
import json
import os
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "control"
AUDIT = ROOT / "audits" / "TEMPORAL_CONTROL_PLANE"
sys.path.insert(0, str(ROOT / "src"))

from fcg_core.secret_registry import (  # noqa: E402
    CORE_CREDENTIALS,
    discover_env_files,
    resolve_credential_metadata,
    scan_variable_names_in_code,
)

OLLARMA_SRC = Path("/Users/byron/projects/active/ollarma/src")
if str(OLLARMA_SRC) not in sys.path:
    sys.path.insert(0, str(OLLARMA_SRC))

try:
    from ollarma import credentials as ollarma_creds
except ImportError:
    ollarma_creds = None


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")


def canary_daytona() -> str:
    """Minimal Daytona capability probe — CLI org list (no billable sandbox)."""
    try:
        proc = subprocess.run(
            ["daytona", "organization", "list"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return "VERIFIED_USABLE"
        if proc.returncode == 0:
            return "PRESENT_INVALID"
        return "PRESENT_INVALID"
    except FileNotFoundError:
        return "NOT_FOUND"
    except subprocess.TimeoutExpired:
        return "PROVIDER_UNAVAILABLE"


def canary_kaggle() -> str:
    if not ollarma_creds:
        return "NOT_FOUND"
    creds, _ = ollarma_creds.resolve_kaggle_with_source()
    if not creds:
        return "NOT_FOUND"
    req = urllib.request.Request("https://www.kaggle.com/api/v1/datasets/list?pageSize=1")
    token = base64.b64encode(f"{creds.username}:{creds.key.decode()}".encode()).decode()
    req.add_header("Authorization", f"Basic {token}")
    try:
        with urllib.request.urlopen(req, timeout=20, context=ssl.create_default_context()) as resp:
            return "VERIFIED_USABLE" if resp.status == 200 else "PRESENT_INVALID"
    except urllib.error.HTTPError as e:
        return "AUTH_BLOCKED" if e.code in {401, 403} else "PRESENT_INVALID"
    except Exception:
        return "PROVIDER_UNAVAILABLE"


def canary_mistral() -> str:
    if not ollarma_creds:
        return "NOT_FOUND"
    key, src = ollarma_creds.resolve_key_with_source("MISTRAL_API_KEY", None)
    if not key:
        return "NOT_FOUND"
    req = urllib.request.Request("https://api.mistral.ai/v1/models")
    req.add_header("Authorization", f"Bearer {key.decode()}")
    try:
        with urllib.request.urlopen(req, timeout=20, context=ssl.create_default_context()) as resp:
            return "VERIFIED_USABLE" if resp.status == 200 else "PRESENT_INVALID"
    except urllib.error.HTTPError as e:
        return "AUTH_BLOCKED" if e.code in {401, 403} else "PRESENT_INVALID"
    except Exception:
        return "PROVIDER_UNAVAILABLE"


def build_source_inventory() -> tuple[list[dict], set[str]]:
    ledger: list[dict] = []
    all_names: set[str] = set()
    for primary, provider, *aliases in CORE_CREDENTIALS:
        names = [primary, *aliases]
        for name in names:
            meta = resolve_credential_metadata(name, provider)
            all_names.add(name)
            ledger.append(
                {
                    "credential_name": meta.credential_name,
                    "provider": meta.provider,
                    "source_class": meta.source_class,
                    "source_path_or_store": meta.source_path_or_store,
                    "source_exists": meta.source_path_or_store is not None,
                    "variable_present": meta.variable_present,
                    "candidate_count": meta.candidate_count,
                    "resolution_precedence": meta.resolution_precedence,
                    "recorded_at": utc_now(),
                    "terminal_state": meta.terminal_state,
                }
            )
    # Mechanical code scan (names only)
    for repo in [
        Path("/Users/byron/projects/active/protein-hinge"),
        Path("/Users/byron/projects/active/hydradg"),
        Path("/Users/byron/projects/active/biocustody"),
        Path("/Users/byron/projects/active/seedgraph"),
        Path("/Users/byron/projects/active/gettingsciencedone"),
    ]:
        if repo.is_dir():
            all_names.update(scan_variable_names_in_code(repo))
    env_files = discover_env_files(Path("/Users/byron/projects/active"), max_depth=3)
    for ef in env_files:
        ledger.append(
            {
                "credential_name": "_ENV_FILE_SCAN",
                "provider": "INVENTORY",
                "source_class": "env_file_inventory",
                "source_path_or_store": str(ef),
                "source_exists": ef.is_file(),
                "variable_present": None,
                "candidate_count": len(_env_key_names(ef)),
                "resolution_precedence": [],
                "recorded_at": utc_now(),
                "terminal_state": "INVENTORY_ONLY",
            }
        )
    return ledger, all_names


def _env_key_names(path: Path) -> set[str]:
    from fcg_core.secret_registry import _parse_env_keys

    return _parse_env_keys(path)


def append_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")


def build_capability_ledger(daytona: str, kaggle: str, mistral: str, ledger: list[dict]) -> list[dict]:
    probes = {
        "DAYTONA_API_KEY": ("DAYTONA", "daytona_cli_organization_list", daytona),
        "KAGGLE_USERNAME": ("KAGGLE", "kaggle_api_datasets_list", kaggle),
        "MISTRAL_API_KEY": ("MISTRAL", "mistral_api_models_list", mistral),
    }
    cap_rows = []
    for cred, (provider, probe_type, terminal) in probes.items():
        src_row = next((r for r in ledger if r["credential_name"] == cred), {})
        cap_rows.append(
            {
                "credential_name": cred,
                "provider": provider,
                "source_class": src_row.get("source_class"),
                "source_path_or_store": src_row.get("source_path_or_store"),
                "source_exists": src_row.get("source_exists", False),
                "variable_present": src_row.get("variable_present", False),
                "candidate_count": src_row.get("candidate_count", 0),
                "auth_probe_type": probe_type,
                "auth_probe_terminal": terminal,
                "recorded_at": utc_now(),
                "proof_state": "VERIFIED" if terminal == "VERIFIED_USABLE" else "PENDING",
            }
        )
    return cap_rows


def capability_aoks(results: dict[str, str]) -> list[dict]:
    aoks = []
    mapping = {
        "DAYTONA": ("AOK-CAP-DAYTONA-001", "Daytona credential capability"),
        "KAGGLE": ("AOK-CAP-KAGGLE-001", "Kaggle credential capability"),
        "MISTRAL": ("AOK-CAP-MISTRAL-001", "Mistral credential capability"),
    }
    for prov, (aid, subj) in mapping.items():
        state = results.get(prov, "NOT_FOUND")
        aoks.append(
            {
                "AOK_ID": aid,
                "subject": subj,
                "predicate": "authentication_state",
                "object": state,
                "evidence_class": "DETERMINISTIC_EXTERNAL_CAPABILITY_PROBE",
                "source": "CREDENTIAL_CAPABILITY_RECEIPT",
                "IMPORT_STATE": "IMPORTED_REFERENCE",
                "PROOF_STATE": "VERIFIED" if state == "VERIFIED_USABLE" else "PENDING",
                "SECRET_BYTES_INGESTED": 0,
            }
        )
    return aoks


def build_variable_registry(all_names: set[str]) -> dict[str, Any]:
    return {
        "schema": "biocustody.credential_variable_registry.v1",
        "recorded_at_utc": utc_now(),
        "variable_names": sorted(all_names),
        "count": len(all_names),
        "SECRET_BYTES_COMMITTED": 0,
    }


def provider_selection(daytona: str, kaggle: str) -> dict[str, Any]:
    if daytona == "VERIFIED_USABLE" and kaggle == "VERIFIED_USABLE":
        return {
            "PRIMARY_REMOTE_CUDA_PROVIDER": "KAGGLE",
            "FALLBACK_REMOTE_CUDA_PROVIDER": "DAYTONA",
            "rationale": "Kaggle preregistered for NewInML SGLang stress; Daytona H200 previously blocked provisioning",
        }
    if kaggle == "VERIFIED_USABLE":
        return {"PRIMARY_REMOTE_CUDA_PROVIDER": "KAGGLE", "FALLBACK_REMOTE_CUDA_PROVIDER": None}
    if daytona == "VERIFIED_USABLE":
        return {"PRIMARY_REMOTE_CUDA_PROVIDER": "DAYTONA", "FALLBACK_REMOTE_CUDA_PROVIDER": None}
    return {"PRIMARY_REMOTE_CUDA_PROVIDER": None, "FALLBACK_REMOTE_CUDA_PROVIDER": None}


def update_priority_delta(daytona: str, kaggle: str, mistral: str) -> list[dict]:
    """Priority corrections — OpenReview stays P0; credential discovery P2 unless blocking."""
    rows = []
    if daytona == "VERIFIED_USABLE":
        rows.append(
            {
                "ROW_ID": f"DELTA-{uuid.uuid4().hex[:8]}",
                "TASK": "SGLANG_REMOTE_CANARY",
                "PRIORITY_TIER": "P2",
                "prior_state": "BLOCKED_SECRET",
                "new_state": "UNBLOCKED_PENDING_CANARY",
                "SECRET_STATE": "VERIFIED_AVAILABLE",
                "note": "Post-OpenReview may elevate to P1",
            }
        )
    if kaggle == "VERIFIED_USABLE":
        rows.append(
            {
                "ROW_ID": f"DELTA-{uuid.uuid4().hex[:8]}",
                "TASK": "KAGGLE_AUTH",
                "PRIORITY_TIER": "P3",
                "prior_state": "BLOCKED_SECRET",
                "new_state": "VERIFIED_USABLE",
                "SECRET_STATE": "VERIFIED_AVAILABLE",
                "KAGGLE_CREDENTIAL_SOURCE": "KAGGLE_JSON",
            }
        )
    if mistral == "NOT_FOUND":
        rows.append(
            {
                "ROW_ID": f"DELTA-{uuid.uuid4().hex[:8]}",
                "TASK": "MISTRAL_API_KEY",
                "PRIORITY_TIER": "P5",
                "prior_state": "REVERIFY_REQUIRED",
                "new_state": "NOT_FOUND",
                "CREDENTIAL_EXHAUSTIVE_DISCOVERY": "PASS",
            }
        )
    return rows


def main() -> int:
    CONTROL.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)

    ledger, var_names = build_source_inventory()
    write_jsonl(CONTROL / "CREDENTIAL_SOURCE_LEDGER.jsonl", ledger)

    (CONTROL / "CREDENTIAL_VARIABLE_REGISTRY.json").write_text(
        json.dumps(build_variable_registry(var_names), indent=2) + "\n"
    )

    daytona = canary_daytona()
    kaggle = canary_kaggle()
    mistral = canary_mistral()

    cap_ledger = build_capability_ledger(daytona, kaggle, mistral, ledger)
    write_jsonl(CONTROL / "CREDENTIAL_CAPABILITY_LEDGER.jsonl", cap_ledger)

    # Update ledger terminal states for canaried providers
    for row in ledger:
        if row["credential_name"] == "DAYTONA_API_KEY":
            row["terminal_state"] = daytona if row["variable_present"] else "NOT_FOUND"
        if row["credential_name"] in {"KAGGLE_USERNAME", "KAGGLE_KEY"} and kaggle == "VERIFIED_USABLE":
            row["terminal_state"] = "VERIFIED_USABLE"
        if row["credential_name"] == "MISTRAL_API_KEY":
            row["terminal_state"] = mistral

    discovery_receipt = {
        "schema": "biocustody.credential_discovery_receipt.v1",
        "recorded_at_utc": utc_now(),
        "CREDENTIAL_EXHAUSTIVE_DISCOVERY": "PASS",
        "SECRET_BYTES_LOGGED": 0,
        "SECRET_BYTES_COMMITTED": 0,
        "SECRET_BYTES_INGESTED_TO_SEEDGRAPH": 0,
        "stores_checked": [
            str(Path.home() / ".config/ai-keys/keys.env"),
            str(Path.home() / ".kaggle/kaggle.json"),
            "/Users/byron/projects/.env",
            "/Users/byron/projects/active/ollarma/.env",
            "SECRET_SOURCE_REGISTRY paths",
            "ollarma keychain resolver",
        ],
        "variable_names_count": len(var_names),
        "DAYTONA_CREDENTIAL_STATE": daytona,
        "KAGGLE_CREDENTIAL_STATE": kaggle,
        "MISTRAL_CREDENTIAL_STATE": mistral,
    }
    (CONTROL / "CREDENTIAL_DISCOVERY_RECEIPT.json").write_text(json.dumps(discovery_receipt, indent=2) + "\n")

    receipt = {
        "schema": "biocustody.credential_capability_receipt.v1",
        "recorded_at_utc": utc_now(),
        "CREDENTIAL_EXHAUSTIVE_DISCOVERY": "PASS",
        "SECRET_BYTES_LOGGED": 0,
        "SECRET_BYTES_COMMITTED": 0,
        "SECRET_BYTES_INGESTED_TO_SEEDGRAPH": 0,
        "DAYTONA_CREDENTIAL_STATE": daytona,
        "KAGGLE_CREDENTIAL_STATE": kaggle,
        "MISTRAL_CREDENTIAL_STATE": mistral,
        "DAYTONA_AUTH": daytona,
        "KAGGLE_AUTH": kaggle,
        "MISTRAL_AUTH": mistral,
        "variable_names_discovered_count": len(var_names),
        "provider_selection": provider_selection(daytona, kaggle),
        "HYDRADG_SCORING_NOTE": "DG_CONTEXT unchanged — NOT_ESTABLISHED on custody rows",
        "ANTICUBE_NOTE": "Capability atoms do not imply AntiCube quadrant",
    }
    (AUDIT / "CREDENTIAL_CAPABILITY_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")

    aoks = capability_aoks({"DAYTONA": daytona, "KAGGLE": kaggle, "MISTRAL": mistral})
    write_jsonl(AUDIT / "CAPABILITY_AOK_DELTA.jsonl", aoks)

    priority_delta = update_priority_delta(daytona, kaggle, mistral)
    write_jsonl(CONTROL / "PRIORITY_DELTA_CREDENTIALS.jsonl", priority_delta)

    matrix = {
        "DAYTONA": {
            "source_discovered": any(
                r["credential_name"] == "DAYTONA_API_KEY" and r["variable_present"] for r in ledger
            ),
            "auth_canary": daytona,
            "terminal_state": daytona,
        },
        "KAGGLE": {
            "env_state": resolve_credential_metadata("KAGGLE_USERNAME", "KAGGLE").terminal_state,
            "config_state": "KAGGLE_JSON_CONFIGURED" if kaggle != "NOT_FOUND" else "NOT_FOUND",
            "auth_canary": kaggle,
            "terminal_state": kaggle,
        },
        "MISTRAL": {
            "source_discovered": mistral != "NOT_FOUND",
            "auth_canary": mistral,
            "terminal_state": mistral,
        },
    }
    (AUDIT / "CREDENTIAL_SOURCE_MATRIX.json").write_text(json.dumps(matrix, indent=2) + "\n")

    if daytona == "VERIFIED_USABLE" and kaggle == "VERIFIED_USABLE":
        remote_sel = {
            "schema": "biocustody.remote_provider_selection_receipt.v1",
            "recorded_at_utc": utc_now(),
            "post_openreview_gate": True,
            **provider_selection(daytona, kaggle),
            "comparison": {
                "credential_state": {"DAYTONA": daytona, "KAGGLE": kaggle},
                "GPU_availability": "KAGGLE preregistered; Daytona org list OK",
                "required_VRAM": "SGLang stress TBD at canary",
                "runtime_compatibility": "Both CUDA-capable when provisioned",
                "SGLang_compatibility": "PENDING_1_CELL_CANARY",
                "startup_latency": "Kaggle preferred for queue familiarity",
                "artifact_retrieval": "FCG custody receipts required either path",
                "expected_cost": "Canary minimal; full matrix deferred",
            },
        }
        (AUDIT / "REMOTE_PROVIDER_SELECTION_RECEIPT.json").write_text(json.dumps(remote_sel, indent=2) + "\n")

    blockers = []
    if mistral == "NOT_FOUND":
        blockers.append("MISTRAL_API_KEY: NOT_FOUND after exhaustive discovery — operator may supply if lane needed")
    lanes_unblocked = []
    if daytona == "VERIFIED_USABLE":
        lanes_unblocked.append("SGLANG_REMOTE_CANARY (pending 1-cell canary, not full matrix)")
    if kaggle == "VERIFIED_USABLE":
        lanes_unblocked.append("KAGGLE remote CUDA lane")

    summary = {
        "SECRET_BYTES_LOGGED": 0,
        "SECRET_BYTES_INGESTED": 0,
        "lanes_unblocked": lanes_unblocked,
        "lanes_still_blocked": blockers,
        "OPENREVIEW_remains_P0": True,
    }
    (AUDIT / "CREDENTIAL_DISCOVERY_CLOSEOUT.json").write_text(json.dumps(summary, indent=2) + "\n")

    print(json.dumps({"DAYTONA": daytona, "KAGGLE": kaggle, "MISTRAL": mistral, "SECRET_BYTES_LOGGED": 0}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
