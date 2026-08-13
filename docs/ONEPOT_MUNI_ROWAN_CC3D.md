# What we learned from onepot.ai and how to reuse it

The transferable lesson is not merely "search a compound library."

## 1. Makeability is a first-class ranking axis

A candidate that scores well computationally but cannot be obtained or synthesized is less useful.

Use a two-axis result:

```text
biological / phenotypic score
           ×
makeability / chemistry feasibility
```

Do not collapse them into one opaque number.

## 2. Negative results matter

onepot's public technology description emphasizes failed/partial reactions in its reaction data. Apply the same principle to the scientific custody graph:

- failed tool calls;
- no-hit searches;
- conflicting evidence;
- candidates rejected by chemistry risk;
- simulation failures;

all remain provenance objects rather than disappearing.

## 3. muni is the best one-day orchestration surface

muni's CLI is JSON-friendly and can discover/run tools while leaving outputs in a project space.

For this hackathon:

```text
local deterministic core
       ↓
canonical SMILES
       ↓
muni tool discovery
   ├─ OnePot: makeability / analog search
   └─ Rowan: descriptors / conformers / docking where useful
       ↓
provider result FCO
```

Use `muni tools -q ...` and inspect inputs dynamically instead of hardcoding a fast-moving tool contract.

## 4. Rowan is a bounded chemistry sidecar

Use Rowan only where the question needs physics/chemistry:

- descriptors;
- conformer search;
- docking;
- pKa / solubility;
- strain / electronic properties;
- FEP after a credible bound-pose/analogue set exists.

Do not run expensive chemistry merely to decorate a morphology ranking.

## 5. CompuCell3D is the virtual-tissue continuation

A future candidate can be injected into CC3D only after you define a scientifically defensible mapping from molecular/phenotypic result to intracellular/tissue parameters.

The immediate bridge is a versioned `candidate_effect.json`, not raw SMILES.
