from __future__ import annotations
import os

def search_core(smiles_list, max_results=10, include_chemistry_risk_score=True):
    """
    Optional onepot CORE query. Never embeds credentials or assumes returned
    records are publishable under hackathon terms.
    """
    api_key = os.getenv("ONEPOT_API_KEY")
    if not api_key:
        return {"status": "not_configured", "reason": "ONEPOT_API_KEY is unset"}
    try:
        from onepot import Client
    except ImportError:
        return {"status": "not_configured", "reason": "Install the onepot client first"}

    client = Client(api_key=api_key)
    return client.search(
        smiles_list=list(smiles_list),
        max_results=max_results,
        include_chemistry_risk_score=include_chemistry_risk_score,
    )
