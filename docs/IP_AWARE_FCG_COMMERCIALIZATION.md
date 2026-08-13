# IP-Aware FCG Commercialization Path

**Updated:** 2026-08-13

## Current Goal

BioCustody / StateShift should route biopharma teams from public scientific
signals to evidence-bounded research hypotheses while keeping licensing,
patent, exclusivity, and freedom-to-operate status in a separate auditable lane.

The commercial product boundary is:

```text
BioCustody / StateShift = evidence custody + state-shift ranking + rights-aware routing
```

It is not:

```text
BioCustody / StateShift = ownership of a drug, peptide, indication, or patent claim
```

This is especially important for routes that begin with public sources such as
Open Targets, ChEMBL, PubMed / PMC OA, AlphaFold DB, CPJUMP1, or other public
biomedical records. Public data availability can support research and product
triage, but it does not prove that a molecule, use, formulation, method, or
commercial product is free of third-party IP, regulatory exclusivity, contract
limits, or licensing constraints.

Official Open Targets documentation currently marks Platform data with CC0 1.0,
but its terms also warn that original data may remain subject to third-party
rights. Record the source terms as evidence; do not convert source availability
into an FTO conclusion.

- Open Targets licence: <https://platform-docs.opentargets.org/licence>
- Open Targets terms of use: <https://platform-docs.opentargets.org/licence/terms-of-use>

## FCG Lanes

The Fractal Custody Graph must keep scientific evidence and rights evidence as
independent graph lanes that only join at a commercialization decision node.

```text
                         candidate entity
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
       scientific evidence lane          licensing / IP / FTO lane
              │                                 │
  protein, peptide, target, disease       source licence, patents,
  phenotype, assay, trial, model          exclusivity, rights holder,
  score, uncertainty, claim ceiling       contract limits, counsel review
              │                                 │
              └────────────────┬────────────────┘
                               ▼
                    commercialization route
```

Scientific evidence answers:

- What protein, pathway, phenotype, peptide, disease, or candidate relationship
  is supported?
- Which public or permitted source supports the relationship?
- What claim ceiling is allowed by the evidence?
- What source hash, transform hash, model version, and result hash reproduce it?

Rights evidence answers:

- What licence or terms governed each imported source at retrieval time?
- Is the entity a public data record, a public-domain research fact, a patented
  composition, an approved drug, an orphan-exclusivity asset, or an unknown?
- What patent, regulatory exclusivity, data-use, or contract review is needed?
- Which commercialization paths remain open without touching protected assets?

## Commercialization Statuses

Every candidate should carry one scientific status and one rights status. Never
collapse them into a single "go" score.

| Status | Lane | Meaning |
| --- | --- | --- |
| `SCIENTIFIC_SIGNAL` | scientific | Public or permitted evidence supports further investigation. |
| `PREDICTED_STATE_SHIFT` | scientific | StateShift ranks the candidate as moving toward the target phenotype or reference state. |
| `EVIDENCE_INSUFFICIENT` | scientific | The graph has too little support for a research claim. |
| `PUBLIC_DATA_AVAILABLE` | rights | Data can be read/used under recorded source terms. This is not FTO. |
| `LICENSE_REVIEW_REQUIRED` | rights | Source terms, provider output rights, or database reuse terms need review. |
| `PATENT_REVIEW_REQUIRED` | rights | Composition, method-of-use, formulation, synthesis, or indication claims may exist. |
| `EXCLUSIVITY_REVIEW_REQUIRED` | rights | Regulatory exclusivity, orphan exclusivity, data exclusivity, or market exclusivity may apply. |
| `FTO_REVIEW_REQUIRED` | rights | Counsel or a formal FTO workflow is required before commercialization. |
| `LICENSE_REQUIRED` | rights | A likely rights holder or licence path has been identified. |
| `NO_GO_WITHOUT_RIGHTS` | rights | Do not commercialize through this molecule/use without rights clearance. |
| `RESEARCH_SERVICE_PATH_OPEN` | commercialization | Sell custody, ranking, diligence, and evidence packaging without selling the protected asset. |
| `NOVEL_DISCOVERY_PATH_OPEN` | commercialization | Advance a new candidate only after novelty, inventorship, and FTO review. |

## Protein To Peptide To Rare Disease To Novel Drug Route

Use the FCG to make the route explicit:

```text
protein target
  -> peptide / molecular representation
  -> rare disease phenotype
  -> candidate intervention hypothesis
  -> scientific claim ceiling
  -> licensing / IP / FTO gate
  -> commercialization path
```

Build rules:

1. Start from public or explicitly permitted target and disease evidence.
2. Preserve protein identifiers, isoforms, species, disease ontology IDs, source
   record IDs, and retrieval timestamps as FCO leaves.
3. Treat peptide or molecular representations as custody evidence, not as an
   ownership claim.
4. When a path touches an approved drug, known peptide, formulation, indication,
   or named clinical asset, set the rights status to review-required until a
   dedicated patent, exclusivity, and licensing assessment exists.
5. Keep the default route-to-market as a research infrastructure/service path:
   BioCustody ranks and packages hypotheses; customers decide whether to
   license, invent around, validate, or discard.
6. For a novel drug path, require a separate novelty and inventorship workflow
   before any public disclosure claims that could affect patent strategy.

## Core Database Surfaces

The MVP can stay compact if each table records its custody metadata and lane.

| Surface | Required records |
| --- | --- |
| `entity_registry` | Stable IDs for proteins, peptides, diseases, phenotypes, molecules, evidence records, rights records, and commercialization routes. |
| `scientific_evidence` | Source, record ID, entity IDs, relationship type, score, uncertainty, claim ceiling, retrieved_at, source_hash, transform_hash. |
| `rights_evidence` | Source terms, licence label, provider terms, patent/exclusivity pointers, rights holder if known, review status, retrieved_at, source_hash. |
| `fcg_edges` | `from_entity`, `to_entity`, `lane`, `edge_type`, `evidence_id`, `confidence`, `claim_ceiling`, `fco_root`. |
| `commercialization_routes` | Candidate, scientific status, rights status, allowed next step, blocked next step, reviewer, decision timestamp. |
| `key_registry` | Public keys, public-key fingerprints, signer role, environment, activation window, rotation status. No private keys. |

## Example JSON Shape

```json
{
  "candidate_route_id": "route:test:protein-peptide-rare-disease-001",
  "scientific_lane": {
    "protein_id": "UniProt:EXAMPLE_TEST_ONLY",
    "peptide_id": "PEPTIDE:EXAMPLE_TEST_ONLY",
    "disease_id": "MONDO:EXAMPLE_TEST_ONLY",
    "claim_ceiling": "RESEARCH_HYPOTHESIS",
    "status": "SCIENTIFIC_SIGNAL"
  },
  "rights_lane": {
    "source_terms_status": "RECORDED",
    "patent_status": "PATENT_REVIEW_REQUIRED",
    "exclusivity_status": "EXCLUSIVITY_REVIEW_REQUIRED",
    "fto_status": "FTO_REVIEW_REQUIRED",
    "commercialization_status": "RESEARCH_SERVICE_PATH_OPEN"
  },
  "custody": {
    "fco_root": "sha256:example-test-only",
    "public_key_fingerprint": "sha256:example-test-only"
  }
}
```

## Key Management Boundary

FCOs can be signed by a private key and verified by a public key, but the repo
must never contain production private key material.

Allowed in this repository:

- public keys;
- public-key fingerprints;
- test-only key fingerprints;
- docs that show placeholder private-key paths;
- generated CI or local test fixtures clearly named `test`, `example`, or
  `fixture`.

Not allowed in this repository:

- production private keys;
- copied developer private keys;
- encrypted production keys;
- seed phrases;
- API tokens;
- cloud credentials;
- private keys embedded in JSON FCO payloads, logs, screenshots, slides, or
  notebooks.

Recommended runtime contract:

```text
BIOCUSTODY_SIGNING_PUBLIC_KEY=ed25519-public-key-or-fingerprint
BIOCUSTODY_SIGNING_PRIVATE_KEY_PATH=.secrets/local-test-ed25519
BIOCUSTODY_KEY_ENV=test
```

`.secrets/` must remain untracked. Production deployments should use an OS
keychain, HSM, cloud KMS, or equivalent secret manager. Any Google Drive, Gmail,
or shared-folder key flow is experimental and may only hold encrypted test keys
or public-key material until a security review approves otherwise.

## Team Acceptance Criteria

- A candidate can have strong scientific evidence and still be blocked on rights
  review.
- A candidate can have public data availability and still require FTO review.
- Every scientific edge and every rights edge has source metadata and an FCO
  receipt.
- No route produces a therapeutic, clinical, diagnostic, or infringement-safe
  claim.
- No private key or credential appears in git history, FCO payloads, logs, or
  generated artifacts.
