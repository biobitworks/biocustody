# Slide deck structure — 7-slide core + appendix

Use the text figures in `TEXT_FIGURES.md` as the first visual source. Do not spend build time polishing slides before the demo works.

## Slide 1 — The gap

**Title:** Biological state is continuous. AI claims are discrete.

**Text:**
- measurements vary even when the underlying state is effectively unchanged;
- exact hashing alone cannot decide biological continuity;
- probabilistic tolerance alone cannot prove provenance.

**Figure:** Text Figure 1.

**Bottom line:** BioCustody separates exact identity from scientific state identity.

---

## Slide 2 — StateShift

**Title:** Detect state change without fuzzy custody

**Text:**
- exact bytes always get exact SHA-256 identities;
- control replicates define a reference cloud;
- median/MAD → PCA → shrinkage covariance;
- empirical acceptance threshold;
- state = CONTINUOUS / TRANSITION / UNRESOLVED.

**Callout:** thresholds are versioned policy objects, not universal 2σ rules.

---

## Slide 3 — Phenotypic restoration, not fake rescue

**Title:** Rank return toward the reference phenotype

**Text:**
- genetic and compound perturbations are independently observed;
- rank compounds by covariance-aware distance back toward the reference cloud;
- score: `R_i = 1 - D(candidate, reference) / (D(perturbed, reference) + epsilon)`;
- optional counterfactual combination is explicitly model-based;
- claim ceiling stops at predicted phenotypic restoration unless rescue is directly measured.

**Figure:** Text Figure 2.

---

## Slide 4 — SMILES + BILN bridge

**Title:** Small molecules and complex peptides keep their native identity

**Text:**
- SMILES for small-molecule exchange;
- BILN/HELM retained for complex peptides;
- pyPept converts BILN → RDKit graph → SMILES/SDF;
- each conversion is a custody transform.

**Figure:** Text Figure 3.

**Tool lane:** muni → OnePot / Rowan; CC3D later receives validated effect parameters.

---

## Slide 5 — FCO/FCG custody

**Title:** Why is this claim admissible?

**Text:**
- every source/transform/output is an FCO;
- parent hashes define route;
- graph preserves SUPPORTS / DERIVED_FROM / CONTRADICTS / CONTINUOUS_WITH;
- route comparison localizes first divergence;
- claim ceiling is independent from confidence.

**Figure:** Text Figures 4 and 5.

---

## Slide 6 — AWS implementation

**Title:** AI proposes. Deterministic controls adjudicate.

**Text:**
- S3 evidence/FCOs;
- Bedrock + Strands/HCLS tools;
- StateShift/FCO as deterministic Gateway/Lambda tool;
- AgentCore Policy gates publish action;
- Observability records what the agent did;
- Evaluations score agent + custody rules;
- Neptune only after the core works.

**Figure:** Text Figure 6.

---

## Slide 7 — Evaluation + demo result

**Title:** Test the scientific boundary, not just the chatbot

Show actual measured values:

- restoration ranking on a tiny CPJUMP1 public subset;
- optional Hits@K / MRR on known chemical-gene relationships where labels permit it;
- false continuity rate;
- false break rate;
- hash reproducibility;
- custody completeness;
- claim-ceiling violations;
- tamper test.

**Closing line:**

> BioCustody does not turn an AI prediction into a biological fact. It makes the boundary between prediction and evidence explicit, measurable, and tamper-evident.

---

# Appendix

A1. HydraDG → StateShift transfer map  
A2. BILN / HELM / SMILES representation strategy  
A3. onepot / muni / Rowan / CC3D continuation  
A4. Public-data policy  
A5. Rietman Gibbs-network motivation  
A6. Future wet-lab co-treatment validation
