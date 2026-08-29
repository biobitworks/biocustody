"""Four separate custody identities — never concatenate variable-length fields directly."""

from __future__ import annotations

from typing import Any

from fcg_core.canonical_v2 import canonical_hash_v2


def content_id(source_bytes: bytes) -> str:
    """CONTENT_ID = SHA256(exact source bytes)."""
    import hashlib

    return hashlib.sha256(source_bytes).hexdigest()


def semantic_id(domain: str, schema_version: str, semantic_payload: dict[str, Any]) -> str:
    """SEMANTIC_ID = SHA256(RFC8785({domain, schema_version, semantic_payload}))."""
    envelope = {
        "domain": domain,
        "schema_version": schema_version,
        "semantic_payload": semantic_payload,
    }
    return canonical_hash_v2(envelope)


def occurrence_id(
    domain: str,
    content_id_value: str,
    source_locator: str,
    actor_ref: str,
    provider_ref: str,
    observation_context: dict[str, Any] | None = None,
) -> str:
    """OCCURRENCE_ID binds a content observation event (may differ across replays)."""
    envelope = {
        "domain": domain,
        "content_id": content_id_value,
        "source_locator": source_locator,
        "actor_ref": actor_ref,
        "provider_ref": provider_ref,
        "observation_context": observation_context or {},
    }
    return canonical_hash_v2(envelope)


def transformation_id(
    domain: str,
    ruleset_sha256: str,
    code_sha256: str,
    ordered_input_ids: list[str],
    canonical_parameters: dict[str, Any],
    runtime_ref: str,
    model_ref: str | None = None,
) -> str:
    """TRANSFORMATION_ID binds a deterministic ruleset + inputs + toolchain."""
    envelope = {
        "domain": domain,
        "ruleset_sha256": ruleset_sha256,
        "code_sha256": code_sha256,
        "ordered_input_ids": ordered_input_ids,
        "canonical_parameters": canonical_parameters,
        "runtime_ref": runtime_ref,
        "model_ref": model_ref or "",
    }
    return canonical_hash_v2(envelope)


def sentence_semantic_id(
    text: str,
    normalization: str,
    byte_start: int,
    byte_end: int,
) -> str:
    return semantic_id(
        "fco.sentence.v2",
        "1.0.0",
        {
            "normalization": normalization,
            "text": text,
            "byte_start": byte_start,
            "byte_end": byte_end,
        },
    )


def citation_semantic_id(
    authors_ordered: list[str],
    title: str,
    year: int,
    doi: str | None = None,
) -> str:
    """Author order is preserved — never sort authors for citation identity."""
    return semantic_id(
        "fco.citation.v2",
        "1.0.0",
        {
            "authors_ordered": authors_ordered,
            "title": title,
            "year": year,
            "doi": doi or "",
        },
    )


def figure_semantic_id(image_sha256: str, caption_semantic_id: str) -> str:
    return semantic_id(
        "fco.figure.v2",
        "1.0.0",
        {"image_sha256": image_sha256, "caption_semantic_id": caption_semantic_id},
    )
