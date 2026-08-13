# SMILES / BILN / HELM integration

## Decision

Use a **representation registry**, not one universal string.

### Small molecules

Primary exchange:

- source SMILES;
- canonical isomeric SMILES;
- InChIKey where RDKit can generate it.

This is the path best supported by onepot, muni chemistry nodes/tools, and Rowan's small-molecule workflows.

### Complex peptides

Keep **BILN** as a first-class source representation.

BILN was designed as a human-readable notation for complex peptides, including cycles, branches and non-natural monomers. pyPept can parse BILN/HELM and produce an RDKit molecular graph, SMILES, SDF, and approximate 3D structures.

Recommended bridge:

```text
BILN
 │ exact source FCO
 ▼
pyPept
 │ transform FCO
 ├── canonical SMILES
 ├── InChIKey
 └── SDF / optional conformer
```

The transformation never replaces the BILN source object.

## Where it fits

### muni

muni has `chem` nodes that render SMILES and a tools catalog containing OnePot and Rowan chemistry tools. Therefore:

```text
BILN → pyPept → SMILES → muni chem/tool node
```

is a reasonable bridge.

### onepot

onepot's current API/search lane is SMILES-first and targets its make-on-demand small-molecule CORE space.

For complex peptides, treat onepot as **not applicable unless the converted entity actually falls inside the supported chemical/synthesis scope**. Do not assume BILN peptide synthesis support.

### Rowan

Rowan workflows accept SMILES for many small-molecule calculations, conformer workflows, docking, descriptors, pKa, FEP setup, etc.

For a modified peptide converted from BILN, validate size/element/method applicability before sending it to a small-molecule workflow.

### CompuCell3D

CompuCell3D does not need SMILES or BILN directly.

Pass an interpreted/cross-validated **effect parameter object** into an Antimony/SBML/CellML submodel or tissue model. Keep molecular representation and tissue simulation as separate custody layers.

## Other representation options

- **HELM:** strongest alternative/companion for complex biopolymers and explicit monomer/connectivity semantics; pyPept can convert HELM ↔ BILN.
- **FASTA:** simple and useful for natural linear peptides, but cannot represent many modifications/cycles/branches.
- **SELFIES:** useful for robust small-molecule generative ML, but not a replacement for BILN/HELM for complex peptide topology.
- **SDF/molfile:** practical atom-level exchange for geometry-aware tools.
- **PDB/mmCIF:** 3D structure exchange, not sufficient by itself as the source chemical notation.

## Custody rule

A format conversion is a **typed transform**, not an equivalence assertion without evidence.

Record:

```text
source notation
converter + version
monomer library version
output notation
output hash
conversion validation
```
