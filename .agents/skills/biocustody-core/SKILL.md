---
name: biocustody-core
description: Build and verify deterministic FCOs, state decisions, counter-perturbation rankings, claim ceilings, and route comparisons.
---

# BioCustody core skill

Read `AGENTS.md`, `DATA_POLICY.md`, and `docs/MVP_BACKBONE.md` first.

Required order:

1. validate data admission;
2. canonicalize input;
3. compute exact FCO;
4. compute state/ranking deterministically;
5. calculate bounded claim ceiling;
6. attach evidence;
7. generate explanation last.

Never use model confidence as a substitute for provenance verification.
