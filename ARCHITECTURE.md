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
