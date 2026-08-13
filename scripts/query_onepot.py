#!/usr/bin/env python
import sys, json
from biocustody.adapters.onepot_adapter import search_core

if len(sys.argv) < 2:
    raise SystemExit("usage: query_onepot.py '<SMILES>'")
result = search_core([sys.argv[1]], max_results=10)
print(json.dumps(result, indent=2, default=str))
