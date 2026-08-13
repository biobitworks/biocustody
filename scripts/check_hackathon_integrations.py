#!/usr/bin/env python
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
CONVOKE_MCP = "https://mcp.convoke.bio/mcp"
CONVOKE_RESOURCE_METADATA = "https://mcp.convoke.bio/.well-known/oauth-protected-resource/mcp"


def redacted_present(name: str) -> dict[str, object]:
    value = os.getenv(name, "")
    placeholders = {"paste_key_here", "paste_convoke_token_here", "..."}
    return {
        "name": name,
        "present": bool(value and value not in placeholders),
        "length": len(value) if value else 0,
    }


def check_openai() -> dict[str, object]:
    try:
        from openai import OpenAI

        client = OpenAI()
        models = client.models.list()
        ids = [m.id for m in models.data]
        return {
            "status": "PASS",
            "model_count": len(ids),
            "sample_models": ids[:5],
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "FAIL",
            "error_type": type(exc).__name__,
            "error": str(exc)[:500],
        }


def fetch_json(url: str, headers: dict[str, str] | None = None) -> tuple[int | None, dict[str, object] | None, str | None]:
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8")), None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        parsed = None
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            pass
        return exc.code, parsed, body[:500]
    except Exception as exc:  # noqa: BLE001
        return None, None, f"{type(exc).__name__}: {exc}"


def check_convoke() -> dict[str, object]:
    meta_status, meta_json, meta_error = fetch_json(CONVOKE_RESOURCE_METADATA)
    token = os.getenv("CONVOKE_MCP_TOKEN", "")
    headers = {"content-type": "application/json"}
    if token and token != "paste_convoke_token_here":
        headers["authorization"] = f"Bearer {token}"
    payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "biocustody-hackathon-smoke", "version": "0.2.0"},
            },
        }
    ).encode("utf-8")
    req = urllib.request.Request(CONVOKE_MCP, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            mcp_status = resp.status
            mcp_body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        mcp_status = exc.code
        body = exc.read().decode("utf-8", errors="replace")
        try:
            mcp_body = json.loads(body)
        except json.JSONDecodeError:
            mcp_body = {"body": body[:500]}
    except Exception as exc:  # noqa: BLE001
        mcp_status = None
        mcp_body = {"error_type": type(exc).__name__, "error": str(exc)[:500]}

    expected_auth_gate = mcp_status == 401 and not (token and token != "paste_convoke_token_here")
    return {
        "status": "PASS_AUTH_REQUIRED" if expected_auth_gate else ("PASS" if mcp_status == 200 else "CHECK"),
        "endpoint": CONVOKE_MCP,
        "resource_metadata_status": meta_status,
        "resource_metadata": meta_json,
        "resource_metadata_error": meta_error,
        "mcp_initialize_status": mcp_status,
        "mcp_initialize_response": mcp_body,
        "token_present": bool(token and token != "paste_convoke_token_here"),
        "note": "401 without CONVOKE_MCP_TOKEN is expected; MCP clients may complete OAuth automatically.",
    }


def main() -> int:
    load_dotenv(ROOT / ".env")
    result = {
        "schema": "biocustody.hackathon_integrations.v1",
        "env": [
            redacted_present("OPENAI_API_KEY"),
            redacted_present("CONVOKE_MCP_TOKEN"),
        ],
        "openai": check_openai(),
        "convoke_bio_mcp": check_convoke(),
    }
    out = ROOT / "deliverables" / "HACKATHON_INTEGRATIONS_STATUS.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["openai"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
