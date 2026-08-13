---
name: molecule-bridge
description: Preserve and convert molecular representations across SMILES, BILN, HELM, SDF, muni, onepot, Rowan, and CompuCell3D handoff.
---

# Molecule bridge skill

Use `docs/MOLECULAR_REPRESENTATIONS.md`.

- Small molecule default: canonical isomeric SMILES.
- Complex peptide source: retain BILN/HELM.
- Convert BILN/HELM with pyPept in the isolated environment.
- Record converter and monomer-library provenance.
- Before onepot/Rowan calls, verify method applicability.
- For CC3D, generate `candidate_effect.json`; do not pass raw SMILES as if it were a tissue-model parameter.
