from __future__ import annotations
import json, shutil, subprocess

def discover(query: str):
    exe = shutil.which("muni")
    if not exe:
        return {"status": "not_configured", "reason": "muni CLI not found"}
    p = subprocess.run(
        [exe, "tools", "-q", query, "--json"],
        capture_output=True, text=True
    )
    if p.returncode != 0:
        return {"status": "error", "stderr": p.stderr.strip()}
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"status": "ok", "raw": p.stdout}

def tool_inputs(tool_name: str):
    exe = shutil.which("muni")
    if not exe:
        return {"status": "not_configured", "reason": "muni CLI not found"}
    p = subprocess.run(
        [exe, "tool", tool_name, "--inputs"],
        capture_output=True, text=True
    )
    return {"status": "ok" if p.returncode == 0 else "error",
            "stdout": p.stdout, "stderr": p.stderr}
