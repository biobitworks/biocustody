from __future__ import annotations
import os

def status():
    """
    Direct Rowan integration is optional because the API evolves.
    For a one-day build, muni's Rowan tools are the preferred stable orchestration surface.
    """
    return {
        "status": "configured" if os.getenv("ROWAN_API_KEY") else "not_configured",
        "recommended_hackday_path": "Use `muni tools -q rowan` then inspect exact tool inputs.",
        "direct_api_note": "If using Rowan directly, pin the Rowan client/API version in the run FCO."
    }
