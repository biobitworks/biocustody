# HydraDG transfer map

The hackathon repo should **transfer HydraDG ideas, not depend on HydraDB**.

| HydraDG lesson | BioCustody / StateShift implementation |
|---|---|
| Direction matters | perturbation and compound signatures are vectors |
| Flat similarity is insufficient | counter-direction + graph/evidence restriction |
| Continuous state has tolerance | reference-cloud model + empirical threshold |
| Small local changes can accumulate | drift/integral evaluator is a P1 extension |
| Graph nodes need exact identity | FCO digest is graph-node identity |
| Derived results need parent custody | FCO parent digests |
| Compare routes, not final values only | `route_compare` finds first divergent object |
| Append history | MMR-style peak accumulator for root summary |
| Missing adapters cannot silently pass | adapters return `not_configured` |
| Claim scope is independent from score | explicit claim ceiling |

## What is intentionally not transferred

- HydraDB as a runtime dependency.
- a claim that Bio-ΔG is thermodynamic free energy.
- a claim that a separately profiled compound experimentally rescued a genetic perturbation.
- a giant graph database before the local experiment works.

## A0 → A4 evaluation ladder

```text
A0  flat phenotype opposition
A1  + known target / graph restriction
A2  + reference-state cloud
A3  + route-comparable FCO/FCG
A4  + AWS policy / agent evaluation
```

This makes each added layer measurable rather than decorative.
