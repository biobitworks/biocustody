#!/usr/bin/env python
import sys, json
from biocustody.adapters.muni_adapter import discover
q = " ".join(sys.argv[1:]) or "onepot rowan docking"
print(json.dumps(discover(q), indent=2, default=str))
