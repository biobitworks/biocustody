# Origin text figures

These are designed to become slide/video figures later.

## Figure 1 — continuous biology, discrete custody

```text
BIOLOGICAL STATE SPACE

     reference cloud
      . . . . . .
    .     ● x1    .
   .  ● x2   ● x3  .
    .             .
      . . . . . .
             \
              \        ● perturbation
               \
                \ ← state boundary

exact bytes:
x1 hash != x2 hash != x3 hash

scientific state:
x1 ≈ x2 ≈ x3  → CONTINUOUS
perturbation   → TRANSITION
```

## Figure 2 — predicted counter-perturbation

```text
                    perturbation
control ●──────────────────────► ● P
        │
        │
        │  compound signature
        ◄─────────────────────── ● C

negative cosine:
opposition(P,C) ↑

claim:
PREDICTED COUNTER-PERTURBATION
not:
MEASURED RESCUE
```

## Figure 3 — molecular representation bridge

```text
        BILN / HELM
             │
       exact source FCO
             │
          pyPept
             │
       RDKit molecular graph
        ┌────┼─────────┐
        ▼    ▼         ▼
     SMILES  SDF    InChIKey
        │
   ┌────┼─────────────┐
   ▼    ▼             ▼
 muni  onepot        Rowan
        │             │
        └─────┬───────┘
              ▼
        provider-result FCO
```

## Figure 4 — FCO route

```text
Cell Painting profile
       │ hash
       ▼
Observation FCO
       │ NORMALIZED_BY
       ▼
State FCO
       │ COMPARED_TO
       ├──────────────► Reference-cloud FCO
       │
       ▼
Ranking FCO
       │ SUPPORTED_BY
       ├──► Open Targets FCO
       ├──► PubMed FCO
       └──► ChEMBL FCO
       │
       ▼
Claim FCO
```

## Figure 5 — exact failure localization

```text
RUN A                         RUN B
source A ─┐                   source A ─┐
          ├→ normalize                 ├→ normalize
config A ─┘                   config B ─┘
             │                           │
             ▼                           ▼
         state A                     state B

                    ▲
                    │
            first divergent node
                 CONFIG
```

## Figure 6 — local first, AWS second

```text
LOCAL SCIENCE CORE                  AWS CONTROL PLANE

StateShift                           Bedrock / Strands
FCO / FCG             ───────────►   AgentCore Gateway
Claim ceiling                       Policy
Synthetic + CPJUMP1                 Observability
Tests                               Evaluations
                                      │
                                      ▼
                                  Neptune stretch
```
