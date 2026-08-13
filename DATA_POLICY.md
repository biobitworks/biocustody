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
