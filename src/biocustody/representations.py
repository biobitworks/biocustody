from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class MoleculeRepresentation:
    source_format: str
    source_text: str
    canonical_smiles: str | None = None
    inchikey: str | None = None
    note: str | None = None

def canonicalize_smiles(smiles: str) -> MoleculeRepresentation:
    try:
        from rdkit import Chem
        from rdkit.Chem import inchi
    except ImportError as e:
        raise RuntimeError(
            "RDKit is optional. Install with: pip install -e '.[chem]' "
            "or use a conda RDKit environment."
        ) from e

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError("Invalid SMILES")
    canonical = Chem.MolToSmiles(mol, canonical=True, isomericSmiles=True)
    key = inchi.MolToInchiKey(mol)
    return MoleculeRepresentation(
        source_format="SMILES",
        source_text=smiles,
        canonical_smiles=canonical,
        inchikey=key,
    )

def biln_to_smiles(biln: str) -> MoleculeRepresentation:
    """
    Requires the isolated pyPept environment.
    Preserves BILN as the source representation while emitting canonical SMILES.
    """
    try:
        from pyPept.sequence import Sequence, correct_pdb_atoms
        from pyPept.molecule import Molecule
        from rdkit import Chem
        from rdkit.Chem import inchi
    except ImportError as e:
        raise RuntimeError(
            "BILN conversion requires pyPept + RDKit. "
            "Create envs/pypept/environment.yml first."
        ) from e

    seq = correct_pdb_atoms(Sequence(biln))
    mol = Molecule(seq)
    romol = mol.get_molecule(fmt="ROMol")
    canonical = Chem.MolToSmiles(romol, canonical=True, isomericSmiles=True)
    key = inchi.MolToInchiKey(romol)
    return MoleculeRepresentation(
        source_format="BILN",
        source_text=biln,
        canonical_smiles=canonical,
        inchikey=key,
        note="Converted with pyPept; retain the original BILN as a custody leaf.",
    )
