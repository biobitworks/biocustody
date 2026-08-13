#!/usr/bin/env python
import argparse, json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--biln", required=True)
parser.add_argument("--prefix", required=True)
args = parser.parse_args()

from pyPept.sequence import Sequence, correct_pdb_atoms
from pyPept.molecule import Molecule
from rdkit import Chem
from rdkit.Chem import inchi

seq = correct_pdb_atoms(Sequence(args.biln))
mol = Molecule(seq)
romol = mol.get_molecule(fmt="ROMol")

smiles = Chem.MolToSmiles(romol, canonical=True, isomericSmiles=True)
inchikey = inchi.MolToInchiKey(romol)

prefix = Path(args.prefix)
prefix.parent.mkdir(parents=True, exist_ok=True)
(prefix.with_suffix(".smi")).write_text(smiles + "\n", encoding="utf-8")
writer = Chem.SDWriter(str(prefix.with_suffix(".sdf")))
writer.write(romol)
writer.close()
(prefix.with_suffix(".representation.json")).write_text(json.dumps({
    "source_format": "BILN",
    "source_text": args.biln,
    "canonical_smiles": smiles,
    "inchikey": inchikey,
    "note": "Original BILN is retained as a custody leaf; SMILES/SDF are derived representations."
}, indent=2), encoding="utf-8")
print(smiles)
