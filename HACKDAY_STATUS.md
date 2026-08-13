# Hackday Status - Bio-Delta-G

**Updated:** 2026-08-13  
**Priority:** AWS Biopharma Hack one-day MVP  
**Current claim ceiling:** Kaggle CPJUMP1 run reaches `PREDICTED_PHENOTYPIC_RESTORATION` for a public morphology-distance benchmark. This is not measured rescue, therapeutic efficacy, clinical utility, or biological rejuvenation.

## What Currently Works

- Local Python 3.12 virtual environment exists at `.venv/`.
- Core environment check passed for Python, numpy, pandas, scikit-learn, networkx, streamlit, and muni.
- Synthetic demo runs and writes `runs/local/synthetic_demo_result.json`.
- Unit tests passed previously: `3 passed`.
- Muni is installed and logged in under the default profile.
- Muni tool visibility confirmed:
  - `onepot` visible.
  - Rowan tools visible, including `rowan_descriptors`.
- Local real CPJUMP1 script runs and writes `runs/local/cpjump1_benchmark_result.json`.
- Private Kaggle CPJUMP1 sweep completed:
  - kernel: `biobitworks/bio-delta-g-cpjump1-sweep`
  - URL: `https://www.kaggle.com/code/biobitworks/bio-delta-g-cpjump1-sweep`
  - version pulled locally: `2`
  - status: `COMPLETE`
  - pulled output directory: `runs/kaggle_output/`
- Best Kaggle CPJUMP1 selection:
  - batch: `2020_11_04_CPJUMP1`
  - compound plates: `BR00116991`, `BR00116992`, `BR00116993`
  - ORF plate: `BR00117006`
  - perturbation: `COMT`
  - perturbation decision: `TRANSITION`
  - perturbation D2: `37.1077`
  - threshold D2: `21.2755`
  - top morphology candidate: `desonide|PLA2G1B|BRD-K21528677-001-04-4`
  - top restoration score: `0.5005`
  - gene-linked benchmark candidate: `U-0521|COMT|BRD-K08953028-001-09-6`
  - gene-linked restoration score: `0.3352`
  - compact ranking rows: `50`
  - candidate profiles evaluated in sweep: `260`
- Kaggle result FCO verifies and tamper demo fails verification.
- Streamlit UI now prefers `runs/kaggle_output/cpjump1_best_result.json`, then `runs/kaggle/cpjump1_best_result.json`, then local CPJUMP1, then synthetic fallback.
- Browser smoke test passed on 2026-08-13 from the active checkout:
  - URL: `http://127.0.0.1:8501`
  - loaded source: `runs/kaggle_output/cpjump1_best_result.json`
  - visible perturbation: `COMT`
  - visible state: `TRANSITION`
  - visible claim ceiling: `PREDICTED_PHENOTYPIC_RESTORATION`
  - visible FCO verification: `True`
  - visible tamper verification: `False`
- API readiness note exists at `deliverables/API_READINESS_20260813.md`.
- Muni live balance checked on 2026-08-13: `12.464793` credits, so Muni credits are not exhausted.
- Provider incorporation boundary checked on 2026-08-13:
  - Bio-Delta-G CPJUMP1 ranking is driven by public CPJUMP1 morphology profiles and JUMP metadata, not Boltz, Rowan, or OnePot scores.
  - OnePot and Rowan are visible through Muni and can be used as optional chemistry sidecars.
  - Existing Boltz/Rowan/Muni banks live in XenoDisorder/FCO support lanes and are not required for the hack demo ranking.
- Convoke Bio MCP endpoint is configured in `.mcp.json` as `convoke-bio`.
- Convoke Bio OAuth-protected resource metadata rechecked on 2026-08-13:
  - metadata endpoint returned `200`
  - unauthenticated MCP initialize returned `401`, which is expected until the MCP client completes OAuth or a valid bearer token is present
- OpenAI SDK auth smoke test passed through `scripts/check_hackathon_integrations.py`.
- Bright Data setup is operator-reported as available, but this active Codex session has not exposed a Bright Data MCP tool, CLI, or repo smoke test yet. Do not make Bright Data-backed claims until a concrete command/tool is verified.

## Exact Demo Path

Local demo path:

```bash
cd /Users/byron/projects/active/biocustody
source .venv/bin/activate
streamlit run ui/app.py
```

Regenerate the local CPJUMP1 fallback:

```bash
python scripts/demo_cpjump1_benchmark.py
```

Regenerate the synthetic fallback:

```bash
python scripts/demo_synthetic.py
```

Pull the completed Kaggle outputs again:

```bash
.venv/bin/kaggle kernels output biobitworks/bio-delta-g-cpjump1-sweep -p runs/kaggle_output -o
```

## Missing Blockers

- Bright Data should be smoke-tested once the intended local MCP tool, CLI, or environment contract is visible.
- Pathway labels remain a tiny MVP map; unverified rows correctly say `not_verified_in_tiny_mvp`.

## Datasets Downloaded / Accessed

Synthetic:

- `data/synthetic/controls.csv`
- `data/synthetic/perturbation.csv`
- `data/synthetic/candidates.csv`

Public CPJUMP1 accessed from Cell Painting Gallery public S3:

- Batch: `2020_11_04_CPJUMP1`
- Kaggle compound plates: `BR00116991`, `BR00116992`, `BR00116993`
- Kaggle ORF plates swept: `BR00117006`, `BR00118049`, `BR00118050`, `BR00118039`
- Metadata paths:
  - `workspace/metadata/platemaps/2020_11_04_CPJUMP1/barcode_platemap.csv`
  - `workspace/metadata/platemaps/2020_11_04_CPJUMP1/platemap/JUMP-Target-1_compound_platemap.txt`
  - `workspace/metadata/platemaps/2020_11_04_CPJUMP1/platemap/JUMP-Target-1_orf_platemap.txt`
  - `workspace/metadata/external_metadata/JUMP-Target-1_compound_metadata_targets.tsv`
  - `workspace/metadata/external_metadata/JUMP-Target-1_orf_metadata.tsv`

Kaggle outputs:

- `runs/kaggle_output/cpjump1_best_result.json`
- `runs/kaggle_output/cpjump1_best_ranking.csv`
- `runs/kaggle_output/cpjump1_selection_sweep_results.csv`
- `runs/kaggle_output/cpjump1_selection_sweep_summary.md`
- `runs/kaggle_output/evaluation_sanity_summary.csv`
- `runs/kaggle_output/evaluation_sanity_summary.md`
- `runs/kaggle_output/evidence_table_draft.csv`
- `runs/kaggle_output/DEMO_SCRIPT_90S_DRAFT.md`
- `runs/kaggle_output/SLIDE_OUTLINE_DRAFT.md`

## AWS Resources Configured

AWS is not needed for the current local demo path.

Current status:

- In this active checkout, `.venv/bin/aws` is not installed.
- Do not claim S3 or any other AWS resource is configured until STS succeeds in the environment being used for the demo.

Minimum target if time permits:

- one S3 prefix containing CPJUMP1 tiny subset, result JSON, ranking CSV, and FCO receipt.

Optional only after local demo works:

- Lambda/Gateway wrapper around deterministic calculation.
- Bedrock/Strands agent.
- AgentCore Policy gate for claim publishing.
- AgentCore Evaluations for custody/tamper/claim tests.

## Licensing / Redistribution Boundary

- Repository source code: Apache License 2.0, recorded in `LICENSE`, `NOTICE`, `pyproject.toml`, and `package.json`.
- Restrictive boundary: Apache 2.0 applies to this repo's source code only. It does not relicense third-party datasets, public database records, provider outputs, API responses, credentials, or evidence records.
- Data/provider rule: follow `DATA_POLICY.md`; provider outputs from onepot, Rowan, muni, Convoke, Boltz, or similar services are local-only/redacted until usage and redistribution rights are verified.
- Team sharing note: share the GitHub repo freely for code review, but do not publish copied provider output or restricted data unless the source terms have been checked.

## Commands To Reproduce Locally

```bash
cd /Users/byron/projects/active/biocustody
/Users/byron/.pyenv/versions/3.12.12/bin/python -m venv .venv
.venv/bin/pip install -e ".[demo]"
.venv/bin/pip install kaggle
.venv/bin/python scripts/check_env.py
.venv/bin/pytest -q
.venv/bin/python scripts/demo_synthetic.py
.venv/bin/python scripts/demo_cpjump1_benchmark.py
.venv/bin/python scripts/check_hackathon_integrations.py
.venv/bin/streamlit run ui/app.py
```

## Tasks That Can Safely Be Cut

- full Gibbs formalism
- full HydraDG benchmark
- Vithia training
- LongMemEval
- HealthOmics
- full Antigence
- full SeedGraph ingestion
- large ChEMBL/Open Targets/BioGRID imports
- Neptune
- CompuCell3D
- broad Rowan/OnePot execution
- any AWS component beyond S3 if cloud setup slows the local demo

## Final Presentation Claims

Allowed:

- "Bio-Delta-G ranks candidate profiles by return toward a measured reference phenotype."
- "The result is evidence-bounded and reproducible from public Cell Painting profiles."
- "The COMT ORF profile is outside the fitted reference cloud in this tiny CPJUMP1 slice."
- "Desonide is the top morphology-distance candidate in this run; U-0521 is a COMT-linked benchmark row with a positive restoration score."
- "FCO-style custody records source IDs, hashes, transformations, calculation version, and result."
- "The system prevents unsupported claim escalation by separating measurement, custody, and claim ceiling."

Prohibited / Unsupported:

- demonstrated biological rejuvenation
- therapeutic efficacy
- clinical utility
- diagnostic claim
- measured rescue without combined/sequential treatment data
- comprehensive pathway/KG coverage
- AWS resource configured unless verified by command output

## Overnight Compute / Offload Status

- Kaggle primary CPJUMP1 sweep: complete and pulled locally.
- `magicstudiobox`: existing Daisy-related loop observed on `xenodisorder`; no new hack-critical training was started from this package.
- `magicstudiobox`: Ollarma selection refresh was offloaded to Studio at `2026-08-13T15:08Z` because magicPRObox may be offline; receipt/log root is `/Users/byron/projects/active/ollarma/.planning/quick/260813-ollarma-selection-refresh-offload/`.
- MagicStudio remains suitable only for bounded free-local helper tasks such as screenshot text, summary review, and claim-language linting.
