import copy
import numpy as np
from biocustody.fco import make_fco, verify_fco, FCO
from biocustody.opposition import opposition_score
from biocustody.merkle import MMRRootAccumulator

def test_fco_verifies():
    fco = make_fco(
        "observation",
        {"value": 1.0},
        {"public_data": True, "source": "synthetic"},
        created_at="2026-08-12T00:00:00+00:00",
    )
    assert verify_fco(fco)

def test_opposition():
    p = np.array([1., 0., -1.])
    c = -p
    assert opposition_score(p, c) > 0.99

def test_mmr_root_changes():
    m = MMRRootAccumulator()
    r1 = m.append("sha256:a")
    r2 = m.append("sha256:b")
    assert r1 != r2
