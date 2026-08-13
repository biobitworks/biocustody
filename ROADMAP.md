# Bio-Delta-G Hackday Roadmap

## Priority Override

AWS BIOPHARMA HACK - PRIORITY OVERRIDE

Pause all nonessential Hydra/Vithia/LongMemEval work. Do not delete or modify those artifacts; preserve them as frozen inputs/reference work.

The priority deliverable is a one-day AWS Biopharma hackathon MVP called Bio-Delta-G.

Goal: demonstrate that we can take a public biological perturbation dataset, define a reference cellular phenotype, measure how far a perturbation moves away from that reference, identify candidate interventions that move the phenotype back toward the reference, and preserve an auditable evidence chain for the resulting ranking.

## Critical Path

```text
public Cell Painting data
  -> control/reference state
  -> perturbed state
  -> candidate restoration ranking
  -> compact biological evidence graph
  -> FCO-style provenance/custody
  -> simple demo UI
  -> optional AWS wrapper
```

## Claim Boundary

Allowed wording:

- phenotypic restoration
- return toward the reference phenotype
- predicted restoration candidate
- evidence-bounded AI for biopharma

Prohibited wording:

- demonstrated biological rejuvenation
- therapeutic efficacy
- clinical, diagnostic, or treatment claim
- measured rescue unless a combined/sequential treatment dataset is actually used

## MVP Outputs

| Output | Status | Owner | Notes |
| --- | --- | --- | --- |
| One untreated/reference phenotype with replicate mean/variance | working | Kaggle + local | CPJUMP1 control wells are the reference cloud. |
| One clearly shifted perturbation | working | Kaggle | COMT ORF on `BR00117006` is classified `TRANSITION` in the bounded sweep. |
| 10-50 candidate profiles | working | Kaggle + local | Display ranking is bounded; sweep evaluated 260 compound profiles from three plates. |
| Multivariate distance to reference | working | local | Robust scale, PCA, LedoitWolf covariance, empirical threshold. |
| Restoration score | working | local | `R_i = 1 - D(candidate, reference) / (D(perturbed, reference) + epsilon)`. |
| Compact ranking | working | Kaggle + local | Top morphology candidate: desonide/PLA2G1B. Gene-linked row: U-0521/COMT. |
| Compound -> target -> pathway/evidence graph | working with caveat | Kaggle + local | Uses CPJUMP1 target metadata plus tiny MVP pathway map; unverified pathways say `not_verified_in_tiny_mvp`. |
| Provenance fields and hashes | working | Kaggle + local | FCO source/transform/result receipt plus subset hash and plate/well identifiers. |
| Tamper/provenance failure | working | Kaggle + local | Kaggle result FCO verifies; tampered score fails verification. |
| Reproducible run command + README | working | local | `HACKDAY_STATUS.md` is the operating surface. |
| 90-second demo script | working | Kaggle + local | Final script updated with COMT benchmark and conservative claim language. |

## Phases

### Phase 0 - Freeze Scope

Goal: prevent expansion.

Tasks:

- Keep HydraDG, Vithia, LongMemEval, full Antigence, full SeedGraph ingestion, full KG imports, HealthOmics, and CC3D off the critical path.
- Preserve existing artifacts as frozen reference inputs.
- Treat AWS as a demo wrapper only when it improves judging fit.

Exit: `ROADMAP.md`, `PLAN.md`, and `HACKDAY_STATUS.md` all name Bio-Delta-G as the priority.

### Phase 1 - Data

Goal: one public feature matrix.

Tasks:

- Load precomputed CPJUMP1 well-level profiles from Cell Painting Gallery.
- Select one control/reference set, one ORF/gene perturbation, and 10-50 compound candidate profiles.
- Persist only a tiny local subset under `data/external/cpjump1_tiny/`.
- Record dataset keys, plate IDs, well IDs, preprocessing recipe, and subset hash.

Kaggle/Magic Studio overnight candidates:

- Kaggle primary sweep already completed and selected COMT.
- MagicStudio may review the pulled Kaggle output for consistency and claim language only.
- Do not download the whole dataset.

### Phase 2 - Calculation

Goal: restoration score works independently of any agent.

Tasks:

- Fit reference mean/variance plus covariance-aware state model.
- Compute perturbation distance from reference.
- Compute candidate distance from reference.
- Rank candidates by `R_i = 1 - D_i / (D_perturbed + epsilon)`.
- Emit result JSON, top ranking, state decision, plot points, and FCO receipt.

Kaggle/Magic Studio overnight candidates:

- Use completed Kaggle sweep as the primary deterministic parameter sweep.
- Run additional label sanity summaries only if they do not threaten the UI/S3 path.
- Flag failures; do not reinterpret biological meaning.

### Phase 3 - Visualization

Goal: judge can see control cloud -> shifted perturbation -> candidate return.

Tasks:

- Update Streamlit to load `runs/local/cpjump1_benchmark_result.json` when present.
- Show PCA scatter/control cloud, perturbed point, top candidates, ranking table, evidence graph, and FCO/tamper status.
- Keep synthetic fallback working.

Magic Studio overnight candidates:

- Generate static screenshot-ready JSON/table artifacts from the run output.
- Draft slide-ready text labels for the visualization; local agent must review for claim ceiling.

### Phase 4 - Evidence + Provenance

Goal: one evidence path and one custody receipt.

Tasks:

- Build a small compound -> target -> pathway graph for top candidate(s).
- Attach source files and record IDs.
- Show exact source hash, transformation recipe, calculation version, result, claim ceiling, and tamper failure.

Magic Studio overnight candidates:

- Draft a small target/pathway evidence table for top candidates from public metadata and lightweight public sources.
- Produce a review list of unsupported claims to avoid.
- Do not ingest giant ChEMBL/Open Targets/BioGRID dumps.

### Phase 5 - AWS Wrapper

Goal: enough AWS integration to improve the demo, not to create architecture drag.

Tasks:

- Minimum: one S3 prefix for input/output artifacts if AWS credentials are configured.
- Optional: expose deterministic Bio-Delta-G calculation as a Lambda/Gateway tool.
- Optional: Bedrock/Strands agent calls the deterministic tool.
- Optional: AgentCore Policy gates `publish_scientific_claim()`.
- Optional: AgentCore Evaluations for expected tool sequence and custody/tamper assertions.
- Neptune is stretch only after the local demo works.

Magic Studio overnight candidates:

- Draft AWS deployment checklist and policy/evaluation test cases from local artifacts.
- Do not create cloud resources or spend paid compute without explicit operator approval.

### Phase 6 - Pitch

Goal: simple, defensible story.

Tasks:

- Use the 2x2: custody/governance versus scientific state awareness.
- Lead with "Evidence-bounded AI for biopharma".
- Keep the pitch: "Did this intervention return the measured cellular state toward reference, why do we believe that, and can another scientist reproduce the evidence chain?"

Magic Studio overnight candidates:

- Draft a 90-second script and seven-slide outline.
- Draft a judge-fit table for internal README only.

## Cut List

Cut without debate if the complete demo is not working:

- full Gibbs formalism
- full HydraDG benchmark
- Vithia training
- LongMemEval
- full Antigence
- full SeedGraph ingestion
- HealthOmics
- large KG imports
- Neptune
- CompuCell3D
- broad Rowan/OnePot chemistry calls

## Overnight Offload Rule

Kaggle is the primary CPJUMP1 execution lane for this hack. `magicstudiobox` may run bounded deterministic/free-local tasks only: data-shape checks, result summarization, label-shuffle sanity checks, screenshot/table generation, and draft pitch text. It must not generate substrate data, promote claims, approve cloud spend, write secrets, mutate frozen Hydra/Vithia artifacts, or publish anything.
