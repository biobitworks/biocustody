# Architecture

```text
                         PUBLIC / SYNTHETIC DATA
                     CPJUMP1 · ChEMBL · Open Targets
                              · PubMed / PMC OA
                                   │
                                   ▼
                        ┌────────────────────┐
                        │  deterministic     │
                        │  ingest + FCO      │
                        └─────────┬──────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
             STATE COMPUTATION             EVIDENCE LANE
        normalize / reduce / cloud      target / paper / assay
                    │                           │
                    ▼                           ▼
          perturbation signatures       evidence FCOs
                    │                           │
                    └─────────────┬─────────────┘
                                  ▼
                             CLAIM OBJECT
                         claim ceiling + FCG
                                  │
                   ┌──────────────┴──────────────┐
                   ▼                             ▼
               LOCAL DEMO                     AWS
              Streamlit / JSON          Bedrock / AgentCore
                                               │
                                       Policy / Observability
                                               │
                                       Neptune (stretch)
```

## Molecular side lane

```text
SMILES ───────────────┐
                     │
BILN / HELM           │
   ↓ pyPept           │
RDKit graph           │
   ↓                  │
canonical SMILES ─────┼──> muni
SDF / 3D ─────────────┼──> Rowan / structure workflow
                     ├──> onepot similarity / makeability
                     └──> evidence FCO

candidate-effect JSON ───> CompuCell3D / Antimony sidecar
```

CompuCell3D is not used as a SMILES engine. It receives **bounded, versioned candidate-effect parameters** derived from a prior molecular/evidence layer.

## IP-aware commercialization lane

BioCustody / StateShift must not collapse scientific evidence and rights status
into one score. The FCG joins two independently sourced lanes only at a
commercialization decision node.

```text
protein target
  -> peptide / molecular representation
  -> rare disease phenotype
  -> candidate intervention hypothesis
  -> scientific claim ceiling
  -> licensing / patent / exclusivity / FTO gate
  -> allowed commercialization route
```

```text
candidate
  ├── scientific_evidence lane
  │     └── target, phenotype, disease, assay, score, uncertainty, claim ceiling
  └── rights_evidence lane
        └── source terms, licence, patent review, exclusivity review, FTO status
```

The default open commercialization route is the research service path:
BioCustody packages evidence, custody, ranking, and diligence. It does not sell
or imply rights to a protected molecule, method, formulation, or indication.

See `docs/IP_AWARE_FCG_COMMERCIALIZATION.md` for the required statuses and
database surfaces.
