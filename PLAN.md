# Bio-Delta-G Execution Plan

## Objective

Build the smallest complete vertical slice for the AWS Biopharma hack:

```text
public CPJUMP1 profiles
  -> reference phenotype
  -> shifted perturbation
  -> restoration ranking
  -> compact evidence graph
  -> FCO/custody receipt
  -> simple demo UI
  -> optional AWS wrapper
```

## Working Definition

For candidate `i`:

```text
R_i = 1 - D(x_i, x_ref) / (D(x_perturbed, x_ref) + epsilon)
```

Where `D` is the covariance-aware distance from the fitted reference-state model. A higher `R_i` means the candidate profile is closer to the reference phenotype than the perturbed profile. This is a phenotypic restoration score, not a therapeutic or rescue claim.

## Immediate Local Tasks

1. Review the completed Kaggle CPJUMP1 result.
   - Kernel: `biobitworks/bio-delta-g-cpjump1-sweep`.
   - Output: `runs/kaggle_output/cpjump1_best_result.json`.
   - Current selected benchmark: COMT ORF on `BR00117006`, classified `TRANSITION`.
   - Must keep the distinction between top morphology candidate and gene-linked benchmark candidate.

2. Smoke-test UI.
   - Load `runs/kaggle_output/cpjump1_best_result.json` when present.
   - Keep synthetic fallback.
   - Show: control cloud, perturbation, top candidates, ranking, evidence graph, FCO, tamper failure.

3. Finalize status and demo docs.
   - `HACKDAY_STATUS.md`
   - 90-second script
   - README command block

4. Verify.
   - `.venv/bin/python scripts/check_env.py`
   - `.venv/bin/pytest -q`
   - `.venv/bin/python scripts/demo_synthetic.py`
   - `.venv/bin/python scripts/demo_cpjump1_benchmark.py`
   - `.venv/bin/kaggle kernels status biobitworks/bio-delta-g-cpjump1-sweep`
   - `.venv/bin/kaggle kernels output biobitworks/bio-delta-g-cpjump1-sweep -p runs/kaggle_output -o`

## Overnight Kaggle Primary Lane

Kaggle is the primary CPJUMP1 lane for tomorrow because it already completed the bounded public-data sweep.

Kernel path:

```text
https://www.kaggle.com/code/biobitworks/bio-delta-g-cpjump1-sweep
```

Repo source:

```text
kaggle/bio_delta_g_cpjump1/kernel.py
kaggle/bio_delta_g_cpjump1/kernel-metadata.json
```

Outputs to review:

- `runs/kaggle_output/cpjump1_selection_sweep_summary.md`
- `runs/kaggle_output/cpjump1_selection_sweep_results.csv`
- `runs/kaggle_output/cpjump1_best_result.json`
- `runs/kaggle_output/cpjump1_best_ranking.csv`
- `runs/kaggle_output/evaluation_sanity_summary.md`
- `runs/kaggle_output/evidence_table_draft.csv`
- `runs/kaggle_output/DEMO_SCRIPT_90S_DRAFT.md`
- `runs/kaggle_output/SLIDE_OUTLINE_DRAFT.md`

## Overnight Magic Studio Offload

Use `magicstudiobox` only for bounded, deterministic, free-local work. Preferred access is the Tailscale SSH alias `magicstudiobox`. Do not start paid API/GPU jobs. Do not write secrets. Do not mutate frozen Hydra/Vithia/LongMemEval artifacts.

### Offload 1 - Kaggle Output Review

Prompt:

```text
Project: Bio-Delta-G AWS Biopharma hack.
Working directory: /Users/byron/projects/inbox/biocustody-stateshift-aws-bootstrap-v0.2.0 if present on Studio, otherwise use the pulled Kaggle output files.

Run bounded deterministic checks only against runs/kaggle_output. Confirm:
- COMT perturbation source, plate, control count, feature count;
- TRANSITION decision values;
- top morphology candidate and gene-linked COMT benchmark row;
- FCO verification and tamper failure;
- no prohibited claim language in draft scripts.

Do not download full datasets. Do not use paid APIs. Do not make therapeutic claims. Write a compact review report only.
```

Expected output: `runs/studio/kaggle_output_review.md`.

### Offload 2 - Evaluation Sanity Checks

Prompt:

```text
Using the generated Bio-Delta-G CPJUMP1 result JSON, run deterministic evaluation checks:
- hash reproducibility;
- tamper failure;
- candidate ranking schema completeness;
- shuffled-label baseline for target-match enrichment if labels permit;
- Hits@K/MRR only where target labels make the benchmark meaningful.

Return PASS/WARN/FAIL rows with exact commands and file paths. Do not expand into full KG ingestion.
```

Expected output: `runs/studio/evaluation_sanity_summary.md`.

### Offload 3 - Evidence Table Draft

Prompt:

```text
From the top Bio-Delta-G candidates, draft a tiny evidence table:
compound -> target -> pathway family -> public source field.

Use only CPJUMP1 metadata and lightweight public-source lookups if already available. If a pathway is not verified, write "not_verified_in_tiny_mvp" rather than filling it in. Keep claim language conservative.
```

Expected output: `runs/studio/evidence_table_draft.csv` and `runs/studio/evidence_table_notes.md`.

### Offload 4 - Pitch Draft

Prompt:

```text
Draft a 90-second demo script and a seven-slide outline for Bio-Delta-G.

Positioning:
- Evidence-bounded AI for biopharma.
- Auditable, variance-aware, tamper-evident, human-governed.
- Novelty: combines scientific state awareness with custody/governance.

Forbidden:
- rejuvenation claims;
- therapeutic efficacy;
- clinical/diagnostic language;
- pretending independent candidate profiles are measured rescue.
```

Expected output: `deliverables/DEMO_SCRIPT_90S_DRAFT.md` and `deliverables/SLIDE_OUTLINE_DRAFT.md`.

## Local Review Gates For Studio Outputs

Every Studio output must be reviewed locally before use:

- Data claims: source IDs and counts match local files.
- Scientific claims: no rescue/therapy/clinical language.
- Provenance: source, transformation, hash, calculation version, and result are present.
- AWS claims: no resource is marked configured unless verified locally.
- Presentation: judge-facing wording says "return toward reference phenotype" or "phenotypic restoration".

## AWS Path

Minimum AWS deliverable:

- S3 bucket/prefix containing input subset, result JSON, and FCO receipt, if credentials are configured.

Optional after local demo works:

- Lambda/Gateway wrapper for the deterministic calculation.
- Bedrock/Strands agent that invokes the deterministic tool.
- AgentCore Policy gate for `publish_scientific_claim()`.
- AgentCore Evaluations for expected tool sequence, claim ceiling, custody completeness, and tamper tests.

Stop AWS work if it threatens the local demo.

## Done Criteria

- CPJUMP1 real-data run produces a ranking.
- UI can show real-data result or synthetic fallback.
- Evidence graph exists for at least one top candidate.
- FCO verifies and tamper demo fails verification.
- `HACKDAY_STATUS.md` reports current state, blockers, datasets, AWS resources, reproduce commands, cuts, allowed claims, and prohibited claims.
- 90-second pitch script exists.
