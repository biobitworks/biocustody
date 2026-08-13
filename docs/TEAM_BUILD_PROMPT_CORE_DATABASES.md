# Team Build Prompt: Core Databases

Use this prompt for the team member building the BioCustody / StateShift core
databases.

```text
Project: BioCustody / StateShift.

Goal:
Build the core database layer for an IP-aware Fractal Custody Graph (FCG) that
routes public scientific evidence into commercialization decisions without
mixing scientific confidence with licensing, patent, exclusivity, or
freedom-to-operate status.

Primary route:
protein -> peptide -> rare disease -> novel drug hypothesis

Product boundary:
BioCustody / StateShift sells evidence custody, state-shift ranking, rights-aware
routing, and reproducible diligence packages. It does not claim ownership of any
specific molecule, indication, formulation, method of use, or therapeutic asset.

Required design:
1. Create a compact entity registry that can represent:
   - proteins and isoforms;
   - peptides and molecular representations;
   - rare diseases and phenotypes;
   - drug or novel-candidate hypotheses;
   - public source records;
   - rights records;
   - FCO receipts.

2. Build two independent graph lanes:
   - Scientific evidence lane:
     protein, target, peptide, phenotype, disease, assay, morphology,
     model output, uncertainty, source record, claim ceiling, FCO root.
   - Licensing / IP / FTO lane:
     source terms, licence label, provider-output rights, patent review status,
     exclusivity review status, rights holder if known, FTO status,
     commercialization path, FCO root.

3. Do not let a public source record imply commercialization freedom.
   Open Targets, ChEMBL, PubMed, PMC OA, AlphaFold DB, CPJUMP1, and similar
   records can support research evidence only under their recorded terms.
   FTO, patent, exclusivity, and licence conclusions require a separate rights
   record and reviewer.

4. Use conservative statuses:
   Scientific statuses:
   - SCIENTIFIC_SIGNAL
   - PREDICTED_STATE_SHIFT
   - EVIDENCE_INSUFFICIENT

   Rights statuses:
   - PUBLIC_DATA_AVAILABLE
   - LICENSE_REVIEW_REQUIRED
   - PATENT_REVIEW_REQUIRED
   - EXCLUSIVITY_REVIEW_REQUIRED
   - FTO_REVIEW_REQUIRED
   - LICENSE_REQUIRED
   - NO_GO_WITHOUT_RIGHTS

   Commercialization statuses:
   - RESEARCH_SERVICE_PATH_OPEN
   - NOVEL_DISCOVERY_PATH_OPEN
   - BLOCKED_PENDING_RIGHTS_REVIEW

5. Key management:
   - Commit public keys and public-key fingerprints only.
   - Never commit production private keys, developer private keys, API tokens,
     seed phrases, cloud credentials, encrypted production keys, or credentials
     copied into logs.
   - If tests require a private key, generate it at test runtime or store only a
     fixture clearly named TEST ONLY / EXAMPLE ONLY.
   - Use environment variables or a local untracked path such as:
     BIOCUSTODY_SIGNING_PUBLIC_KEY=ed25519-public-key-or-fingerprint
     BIOCUSTODY_SIGNING_PRIVATE_KEY_PATH=.secrets/local-test-ed25519
     BIOCUSTODY_KEY_ENV=test
   - The database may store key fingerprints and signer roles. It must not store
     private key material.

6. Minimum schema surfaces:
   - entity_registry
   - scientific_evidence
   - rights_evidence
   - fcg_edges
   - commercialization_routes
   - fco_receipts
   - key_registry

7. Every imported record needs:
   - source;
   - source_record_id;
   - source URL or accession;
   - dataset version where available;
   - licence_or_terms;
   - retrieved_at;
   - payload_sha256;
   - transform_hash if transformed;
   - claim_ceiling;
   - fco_root.

8. Acceptance tests:
   - A candidate can be SCIENTIFIC_SIGNAL but BLOCKED_PENDING_RIGHTS_REVIEW.
   - A candidate can be PUBLIC_DATA_AVAILABLE but still FTO_REVIEW_REQUIRED.
   - The query for "commercially routeable candidates" excludes candidates with
     PATENT_REVIEW_REQUIRED, EXCLUSIVITY_REVIEW_REQUIRED, or FTO_REVIEW_REQUIRED
     unless the route is only RESEARCH_SERVICE_PATH_OPEN.
   - No database row, fixture, log, or FCO payload contains private key material.
   - The protein -> peptide -> rare disease -> novel drug path can be reproduced
     from source hashes and FCO receipts.

Deliverables:
- schema migration;
- small seed dataset with example/test-only IDs;
- query examples for scientific path, rights path, and joined commercialization
  decision;
- tests for the acceptance cases above;
- README note showing how to run locally with generated test keys only.
```
