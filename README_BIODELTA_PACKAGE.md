# BioCustody / StateShift — AWS Biopharma Hack Day bootstrap

**Version:** 0.2.0  
**Purpose:** one-day, public-data-only MVP for variance-aware scientific custody and phenotypic restoration ranking.

## AWS Biopharma Hack priority

The current priority deliverable is **Bio-Delta-G**:

```text
public Cell Painting data
  -> control/reference state
  -> shifted perturbation
  -> candidate restoration ranking
  -> biological evidence graph
  -> provenance/custody
  -> simple demo UI
```

HydraDG, Vithia, LongMemEval, full Antigence, full SeedGraph ingestion, HealthOmics,
large KG imports, Neptune, and CompuCell3D are not on the critical path.
Preserve related artifacts as frozen reference work; do not delete or mutate them
for the hack.

## Core claim

Biological measurements are continuous and noisy, while hashes, audit records, and AI policy decisions are discrete.

This repo keeps those two concepts separate:

1. **Exact custody identity** — every exact observation or artifact gets a deterministic SHA-256 identity.
2. **Scientific state identity** — a versioned statistical model determines whether a changed observation remains within the same reference state, crosses a state boundary, or is unresolved.
3. **Claim custody** — an evidence graph and claim ceiling limit what an agent is allowed to say.

The biological demo is intentionally bounded:

> Given public Cell Painting profiles, define a reference phenotype, measure a
> shifted perturbation, and rank candidate profiles by how strongly they return
> toward the reference distribution.

It does **not** claim experimental rescue unless a dataset actually contains the combined/sequential treatment. Use **phenotypic restoration** or **return toward the reference phenotype**, not therapeutic efficacy.

## Fastest local start

```bash
cd biocustody-stateshift-aws-bootstrap-v0.2.0
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[demo]"
python scripts/demo_synthetic.py
python scripts/demo_cpjump1_benchmark.py
streamlit run ui/app.py
```

The synthetic demo is included so the core can work before any AWS service, external API, or large dataset is configured.

## Kaggle CPJUMP1 benchmark

The private Kaggle kernel is the current real-data benchmark source:

```text
https://www.kaggle.com/code/biobitworks/bio-delta-g-cpjump1-sweep
```

It streams public CPJUMP1 processed profiles, sweeps a tiny plate/gene set, and writes:

```text
runs/kaggle_output/cpjump1_best_result.json
runs/kaggle_output/cpjump1_best_ranking.csv
runs/kaggle_output/cpjump1_selection_sweep_results.csv
runs/kaggle_output/evidence_table_draft.csv
```

Pull or refresh outputs:

```bash
.venv/bin/pip install kaggle
.venv/bin/kaggle kernels output biobitworks/bio-delta-g-cpjump1-sweep -p runs/kaggle_output -o
```

Current selected benchmark: COMT ORF on plate `BR00117006`, classified `TRANSITION`. Top morphology candidate is desonide/PLA2G1B; the gene-linked benchmark row is U-0521/COMT. This is a phenotypic restoration-distance benchmark, not measured rescue.

## What transfers from HydraDG

This package transfers the useful **design principles**, not a dependency on HydraDB:

- graph-restricted ranking;
- exact-vs-continuous identity;
- probability-cloud / covariance-aware state membership;
- directional state movement;
- typed FCO nodes and FCG edges;
- route comparison to the first divergent object;
- append-only Merkle/MMR-style root accumulation;
- bounded claims and fail-closed `not_configured` adapters.

See `docs/HYDRADG_TRANSFER.md`.

## Molecular representation bridge

Small molecules use **canonical SMILES** as the default exchange format.

Complex peptides can enter as **BILN** or HELM through a separate pyPept environment:

```text
BILN / HELM
   ↓ pyPept
RDKit molecular graph
   ├── canonical SMILES → muni / onepot / Rowan-compatible small-molecule lane where appropriate
   ├── SDF              → geometry / structure lane
   └── FCO               → provenance + exact representation
```

BILN is kept as a first-class source representation. We do **not** discard it after conversion.

See `docs/MOLECULAR_REPRESENTATIONS.md`.

## Main repo map

```text
src/biocustody/       deterministic core
data/synthetic/       out-of-box demo data
eval/                 deterministic test scenarios
ui/                   local Streamlit demo
adapters/             onepot / muni / Rowan / CC3D / AWS boundary docs
models/cc3d/          optional tissue-model sidecar, not critical path
aws/                   day-of AWS deployment notes
docs/                  MVP, video, slides, figures, sources
envs/                  separate environments for incompatible scientific stacks
.agents/skills/        repo-local agent instructions
```

## Public-hackathon constraint

Do not ingest private patient data, PHI, restricted sponsor data, or confidential research materials. Provider-generated results (e.g., onepot/Rowan/muni) should be treated as shareable **only when their terms allow it**.

See `DATA_POLICY.md`.

## Recommended build order

1. Run synthetic tests.
2. Run the local UI.
3. Pull a **small** CPJUMP1 processed-profile subset.
4. Rank candidate profiles by Bio-Delta-G restoration score.
5. Create FCOs + local FCG.
6. Add one compact compound -> target -> pathway evidence graph.
7. Add one S3/AWS wrapper only if it reduces work or improves judging fit.
8. Add Bedrock / AgentCore only after the local demo works.
9. Add Neptune only after the demo works.
10. Add CompuCell3D only as a bounded tissue-scale sidecar.
