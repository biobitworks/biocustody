# Hackathon data policy

## Admission rule

Allowed:

- synthetic data generated in this repository;
- public open datasets;
- sample datasets whose terms permit public hackathon use;
- properly de-identified data explicitly permitted for this purpose.

Rejected by default:

- PHI or private patient records;
- confidential sponsor or employer materials;
- restricted-access research datasets;
- local clinical data;
- proprietary data whose sharing/use rights have not been checked;
- secrets, API keys, access tokens, credentials.
- production private keys, developer private keys, seed phrases, encrypted
  production keys, or any private key copied into source files, FCO payloads,
  logs, slides, notebooks, or generated artifacts.

## Required source metadata

Every imported dataset or provider result should record:

```json
{
  "public_data": true,
  "contains_phi": false,
  "access_restricted": false,
  "usage_rights_verified": true,
  "source": "...",
  "source_record_id": "...",
  "dataset_version": "...",
  "license_or_terms": "...",
  "retrieved_at": "...",
  "payload_sha256": "..."
}
```

## Provider-output rule

onepot, Rowan, muni, and similar services may return account-scoped or access-controlled information. Those outputs can be used locally if permitted, but **do not automatically publish them in a public hackathon repository**.

Treat them as:

```text
provider_output
  ↓
rights checked?
  ├── yes → eligible for public evidence FCO
  └── no  → local-only / redacted pointer
```

The code must never copy secrets into an FCO payload.

## Licensing / IP / FTO rule

Source availability and commercialization freedom are separate facts.

Public records from Open Targets, ChEMBL, PubMed / PMC OA, AlphaFold DB,
CPJUMP1, and similar sources may support scientific evidence only under their
recorded source terms. They do not prove that any protein, peptide, molecule,
method of use, formulation, disease indication, or commercialization route is
free of third-party patent rights, regulatory exclusivity, contract limits, or
licensing requirements.

Every imported source should preserve:

```json
{
  "source_terms_url": "...",
  "license_or_terms": "...",
  "rights_status": "PUBLIC_DATA_AVAILABLE",
  "patent_status": "PATENT_REVIEW_REQUIRED",
  "exclusivity_status": "EXCLUSIVITY_REVIEW_REQUIRED",
  "fto_status": "FTO_REVIEW_REQUIRED"
}
```

The FCG must keep scientific evidence and licensing / IP / FTO evidence in
separate lanes until a commercialization decision is explicitly reviewed.

## Key material rule

Allowed in the repository:

- public keys;
- public-key fingerprints;
- placeholder private-key paths;
- generated test keys;
- fixtures clearly named `test`, `example`, or `fixture`.

Not allowed in the repository:

- production private keys;
- developer private keys;
- private keys for shared accounts;
- encrypted production keys;
- seed phrases;
- API tokens or cloud credentials.

Use an untracked local path for test signing keys, for example
`.secrets/local-test-ed25519`. Production signing must use a real secret manager,
OS keychain, HSM, or cloud KMS.
