# Bio-Delta-G Backbone MVP

## Priority override

Pause nonessential Hydra/Vithia/LongMemEval work. Preserve those artifacts as
frozen references. The critical path is Bio-Delta-G: public Cell Painting
profiles -> reference phenotype -> shifted perturbation -> restoration ranking
-> compact evidence graph -> provenance/custody -> simple demo UI.

## Demo question

> Which candidate profile most strongly returns a shifted cellular phenotype
> toward the untreated/reference distribution, what evidence supports that
> ranking, and what is the strongest claim the result permits?

## P0 — must work locally

1. public-data admission check;
2. canonicalize + hash source artifact;
3. fit reference state from control replicates;
4. compute perturbation state;
5. rank candidate compound profiles by return-toward-reference score;
6. create candidate FCO;
7. calculate claim ceiling;
8. show route / graph;
9. demonstrate tamper invalidation;
10. run deterministic tests.

Core score:

```text
R_i = 1 - D(x_i, x_ref) / (D(x_perturbed, x_ref) + epsilon)
```

Use Mahalanobis or equivalent covariance-aware distance. Directional opposition
can remain an analysis side metric, but the primary judge-facing result is
phenotypic restoration / return toward reference.

## P1 — real public benchmark

CPJUMP1:

- use processed well-level profiles;
- select a tiny subset;
- use known chemical-gene relationships as optional benchmark evidence;
- evaluate Hits@K / MRR / enrichment over shuffled labels.

## P2 — evidence enrichment

Top few candidates only:

- one compact compound -> target -> pathway path for top candidate(s);
- CPJUMP1 public metadata first;
- Open Targets / PubMed / ChEMBL only for top few candidates if time permits;
- no giant KG import.

## P3 — provider / chemistry lane

- onepot availability/makeability;
- Rowan chemistry;
- muni orchestration.

Provider outputs remain local-only until rights are checked.

## P4 — AWS

- S3 artifact wrapper first;
- Strands/Bedrock agent after local demo works;
- deterministic tool via Lambda/AgentCore Gateway;
- AgentCore Policy;
- Evaluations;
- Observability;
- Neptune stretch only.

## Exit condition

A working demo is complete when:

```text
one query
→ one ranked candidate
→ one exact FCO route
→ one bounded claim
→ one tamper failure
→ one evaluation report
```
