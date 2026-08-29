# PROJECT_DOCUMENT_001_ATOMIZATION — Scope (AUD-FCG-DOCUMENT-LATTICE-001 extension)

**Status:** EXECUTING  
**Frozen source commit:** `4a372a5c459ad60cd23b850709011cbfd0e516b4`  
**Sealed submission PDF:** NOT mutated  
**Production seedgraph-neo4j (magicLABbox :7687):** NOT touched  

## Goal

Run the SeedGraph **atoms → interim SOT composition → sentence diagram / maps** pipeline for the NewInML manuscript, with full traceability receipts. This closes the gap between lattice-001 (structural FCG custody) and the downstream contract in `seedgraph/docs/FCO_FCG_FRAMEWORK.md`.

## In scope (this wave)

| Stage | SeedGraph module | Output |
|-------|------------------|--------|
| 1. Evidence import | `ingest/orchestrator.import_file` | `EvidenceSeed` + ledger + content store |
| 2. Atom extraction | `extract/orchestrator.extract_seed` | Sentence/Figure/Table/Entity/Equation atoms |
| 3. Atom sidecar | `atoms.snapshot.json` | Offline `SnapshotMappingReader` input |
| 4. S-P-O diagram | `extract/logic.SpoExtractor` | `spo` on PASS sentence atoms (phase 73) |
| 5. Interim SOT compose | biocustody bridge (PROMPT-020 STEP1 subset) | `SOT_ATOM_COMPOSITION.jsonl` — refuse if zero supporting atoms |
| 6. Maps | `maps/query.build_sentence_map`, `build_logic_map` | `SENTENCE_MAP.jsonl`, `LOGIC_MAP.jsonl` |
| 7. Lattice bridge | match by normalized text / CONTENT_ID | `LATTICE_ATOM_BRIDGE.jsonl` |

## Out of scope (explicit)

- PROMPT-020 full `:Claim` tier in live seedKG (not implemented in seedgraph `src/`)
- Draft **generation** from atoms (manuscript remains upstream source; atoms project **from** PDF)
- Production Neo4j mutation
- OpenReview / AntiCube public upload (blocked on operator PDF classification)
- `pdflatex` compile (not on host); uses `main_smoke.pdf` with byte hash receipt

## Runtime isolation

```
audits/AUD-FCG-DOCUMENT-LATTICE-001/seedgraph_runtime/
  config/signing_key.pem
  ledger.db
  store/
  neo4j-fallback/   (if audit Neo4j unavailable)
```

Neo4j target: `bolt://localhost:17687` (`seedgraph-neo4j-audit-lattice` container).

## Gates

| Gate | Pass criterion |
|------|----------------|
| `ATOM_IMPORT_GATE` | Evidence seed imported, ledger entry exists |
| `ATOM_EXTRACT_GATE` | `atoms.snapshot.json` written, atom count > 0 |
| `SOT_ATOM_COMPOSITION_GATE` | Every SOT row terminal: COMPOSED or REFUSED_NO_ATOMS |
| `SENTENCE_DIAGRAM_GATE` | SPO attempted on PASS sentences (may be partial without sciSpaCy) |
| `LATTICE_BRIDGE_GATE` | ≥1 lattice sentence linked to atom seed_id |

## Claim ceiling

`REPURPOSING_HYPOTHESIS` — atomization proves custody/traceability, not biological efficacy.
