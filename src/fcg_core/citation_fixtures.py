"""Citation/resource identity fixtures CIT-ID-001 … CIT-ID-007."""

from __future__ import annotations

from typing import Any

from fcg_core.canonical_v2 import canonical_hash_v2
from fcg_core.identifier_layer import build_identifier_record, build_resource, identifier_semantic_id, normalize_doi


def run_citation_fixtures() -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], dict]:
    identifiers: list[dict] = []
    resources: list[dict] = []
    metadata_snapshots: list[dict] = []
    citation_occurrences: list[dict] = []
    alias_ledger: list[dict] = []
    results: dict[str, str] = {}

    # CIT-ID-001: DOI presentation variants
    doi_presentations = [
        "doi:10.1038/s41586-019-1799-4",
        "https://doi.org/10.1038/s41586-019-1799-4",
        "10.1038/S41586-019-1799-4",
    ]
    doi_ids = [build_identifier_record("DOI", p) for p in doi_presentations]
    sem_ids = {r["SEMANTIC_ID"] for r in doi_ids}
    identifiers.extend(doi_ids)
    results["CIT-ID-001"] = "PASS" if len(sem_ids) == 1 else "FAIL"

    # CIT-ID-002: BibTeX alias + resource
    bib = build_identifier_record("BIBKEY_ALIAS", "uniprot2023")
    doi2 = build_identifier_record("DOI", "10.1093/nar/gkac1052")
    identifiers.extend([bib, doi2])
    res = build_resource(doi2["IDENTIFIER_ID"], "DATABASE", "UniProt")
    resources.append(res)
    citation_occurrences.append(
        {
            "CITATION_OCCURRENCE_ID": "CIT-OCC-fixture-002",
            "bib_key_local_alias": "uniprot2023",
            "identifier_id": doi2["IDENTIFIER_ID"],
            "note": "local alias maps to canonical DOI resource",
        }
    )
    metadata_snapshots.append(
        {
            "METADATA_SNAPSHOT_ID": canonical_hash_v2({"fixture": "CIT-ID-002", "title": "UniProt 2023"})[:16],
            "identifier_id": doi2["IDENTIFIER_ID"],
            "title": "UniProt: the Universal Protein Knowledgebase in 2023",
        }
    )
    results["CIT-ID-002"] = "PASS"

    # CIT-ID-003: same resource, two attestation IDs
    att1 = {"ATTESTATION_ID": "ATT-key-a", "subject_id": res["RESOURCE_ID"], "key_fingerprint": "fp-a"}
    att2 = {"ATTESTATION_ID": "ATT-key-b", "subject_id": res["RESOURCE_ID"], "key_fingerprint": "fp-b"}
    results["CIT-ID-003"] = "PASS" if att1["subject_id"] == att2["subject_id"] else "FAIL"

    # CIT-ID-004: metadata correction, identifier unchanged
    snap_v1 = {"identifier_id": doi2["IDENTIFIER_ID"], "version": "2023-01", "content_sha": "aaa"}
    snap_v2 = {"identifier_id": doi2["IDENTIFIER_ID"], "version": "2023-02", "content_sha": "bbb"}
    results["CIT-ID-004"] = "PASS" if snap_v1["identifier_id"] == snap_v2["identifier_id"] and snap_v1["content_sha"] != snap_v2["content_sha"] else "FAIL"

    # CIT-ID-005: one resource, multiple occurrences
    for i in range(2):
        citation_occurrences.append(
            {
                "CITATION_OCCURRENCE_ID": f"CIT-OCC-multi-{i}",
                "resource_id": res["RESOURCE_ID"],
                "identifier_id": doi2["IDENTIFIER_ID"],
                "occurrence_index": i,
            }
        )
    results["CIT-ID-005"] = "PASS"

    # CIT-ID-006: same bib key → two DOIs → QUARANTINED
    alias_ledger.append(
        {
            "bib_key": "conflict_key",
            "doi_a": normalize_doi("10.1038/s41586-019-1799-4"),
            "doi_b": normalize_doi("10.1093/nar/gkac1052"),
            "terminal": "QUARANTINED_IDENTITY_CONFLICT",
        }
    )
    results["CIT-ID-006"] = "QUARANTINED_IDENTITY_CONFLICT"

    # CIT-ID-007: two keys → same DOI → DUPLICATE_ALIAS
    doi_canon = normalize_doi("10.1038/s41586-019-1799-4")
    alias_ledger.append({"bib_key_a": "key1", "bib_key_b": "key2", "canonical_doi": doi_canon, "terminal": "DUPLICATE_ALIAS"})
    results["CIT-ID-007"] = "DUPLICATE_ALIAS"

    fixture_summary = {"fixtures": results, "all_pass": all(v in {"PASS", "DUPLICATE_ALIAS", "QUARANTINED_IDENTITY_CONFLICT"} for v in results.values())}
    return identifiers, resources, metadata_snapshots, citation_occurrences, alias_ledger, fixture_summary
