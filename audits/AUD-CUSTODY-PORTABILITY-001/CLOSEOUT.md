# AUD-CUSTODY-PORTABILITY-001 Closeout

**Branch:** `audit/custody-portability-core-20260829` (biocustody)  
**Claim under test:** custody protocol reusable across actors/models/runtimes/providers/data  
**Claim ceiling:** `PARTIAL_EVIDENCE` — **NOT VERIFIED**

## What was built

- `src/fcg_core/` — four identities, dual canonicalization profiles, import/proof separation, validation result/occurrence split, BibTeX custody, provider adapter contract
- `schemas/fcg_core/` — versioned JSON Schema objects with SHA-256 registry
- `tests/fcg_core/` — golden/adversarial pytest suite + regression fixture registry (A–M)
- `node/fcg_core/` — Node canonicalization parity tests (canonicalize + ajv)

## Canonicalization profiles (immutable history preserved)

| Profile | Label | Use |
|---------|-------|-----|
| v1 | `seedgraph_canonical_v1` | Legacy SeedGraph/FCO leaf hashes — **never recompute under v2** |
| v2 | `rfc8785_jcs_v2` | New semantic objects (sentence, citation, occurrence, transformation) |

## Blockers to VERIFIED portability claim

1. Cross-runtime Python↔Node hash parity not lockstep-proven for full JCS edge cases
2. Provider adapters GITHUB/CROSSREF/HF/PyPI/npm/OCI are contract-only
3. PDF/OCR adapter pipeline design-only
4. Linux x86_64 replay not executed
5. Upstream repos (seedgraph, protein-hinge, gsigmad) not yet consuming fcg_core

## Integration targets (no production mutation)

| Repo | Integration |
|------|-------------|
| seedgraph | Replace `merkle/atoms.py` v2 paths; keep v1 exports frozen |
| protein-hinge | Bind FINAL_CI receipt to semantic audit SHA-256s |
| gettingsciencedone | Align `execution_discipline/hashing.py` with fcg_core v2 |
| fractal-custody-objects | Interop exports only; gated builder untouched |

## Do not merge

Per operator gate: **do not merge to main** until OpenReview upload completes (protein-hinge submission lane).
