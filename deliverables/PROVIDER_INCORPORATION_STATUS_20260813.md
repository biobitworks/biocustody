# Provider Incorporation Status - 2026-08-13

## Bio-Delta-G Hack Demo

The Bio-Delta-G CPJUMP1 result is currently independent of Boltz, Rowan, OnePot, and Muni provider outputs.

- Core ranking source: public CPJUMP1 precomputed Cell Painting profiles plus JUMP compound/ORF metadata.
- Ranking files: `runs/kaggle_output/cpjump1_best_result.json`, `runs/kaggle_output/cpjump1_best_ranking.csv`.
- Evidence table: `runs/kaggle_output/evidence_table_draft.csv`.
- Evidence source currently used: CPJUMP1 compound target metadata plus a tiny local pathway map.
- Claim ceiling: predicted phenotypic restoration / return toward reference phenotype only.

## Muni

Checked live with the Muni CLI on 2026-08-13.

- Account: `byron@biobitworks.com`.
- Balance: `12.464793` credits.
- Conclusion: Muni credits are not exhausted.
- OnePot tool visibility: present.
- Rowan tool visibility: present, including descriptors, ADMET, docking, pKa, solubility, RBFE, conformer, and related chemistry tools.

## Rowan

Rowan is configured and has downloaded/materialized artifacts in XenoDisorder support lanes, but those data are not joined into the Bio-Delta-G CPJUMP1 ranking.

Observed XenoDisorder Rowan status:

- Download receipt: `/Users/byron/projects/active/xenodisorder/.planning/rowan/muni_downloads/ROWAN_MUNI_DOWNLOAD_RECEIPT_20260804T041014Z.json`.
- Remediation delta: `/Users/byron/projects/active/xenodisorder/.planning/quick/260802-xd-v2-rowan-package-readiness/XD_V2_ROWAN_REMEDIATION_DELTA_20260802.json`.
- Reconciled Rowan panel state: `PASS_RECONCILED_PARTIAL_ONLY_KNOWN_MISSING_CLASSES`.
- Known holds remain: unresolved SMILES keys, failed workflow keys, final v2 release approval, Cloudmer partial-stage final seal.

## Boltz

Boltz API spend is done/closed for new runs, but already downloaded Boltz data are locally banked in XenoDisorder support lanes.

Observed XenoDisorder Boltz incorporation:

- Continuous validation: `/Users/byron/projects/active/watchtower/.planning/quick/260802-ollarma-approved-daisy-handoff/XD_CLOUDMER_BOLTZ_CONTINUOUS_VALIDATION_20260802.json`.
- Blackbox bank reconciliation: `/Users/byron/projects/active/xenodisorder/.planning/boltz/reconciliation/BLACKBOX_BOLTZ_BANK_DAISY_RECON_20260804T040841Z.json`.
- Reconciliation result: `APPLY_OK`.
- Already indexed before reconciliation: `9030`.
- Rows appended from downloaded bank: `31774`.
- Fold index target: `/Users/byron/projects/active/xenodisorder/.planning/boltz/fold_index.jsonl`.
- Boundary: no new Boltz API calls or spend; claim ceiling remains computational-proxy only.

## Current Selection Refresh

Ollarma selection refresh was moved to `magicstudiobox` so it can continue if magicPRObox loses internet.

- Offload root: `/Users/byron/projects/active/ollarma/.planning/quick/260813-ollarma-selection-refresh-offload/`.
- Active offload id at handoff: `studio_selection_refresh_offload_20260813T150833Z`.
- Purpose: clear `SELECTION_STALE` by running the local code-suite benchmark and report/verify steps on Studio.
- This is an Ollarma routing refresh only; it does not write to canonical KG, publish claims, or start new paid provider work.
