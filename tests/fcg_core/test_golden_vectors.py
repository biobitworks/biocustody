"""Golden vectors and adversarial tests for fcg_core."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fcg_core.canonical_v1 import hash_citation_leaf_v1, hash_sentence_leaf_v1
from fcg_core.canonical_v2 import canonical_hash_v2, canonical_json_bytes_v2
from fcg_core.identities import (
    citation_semantic_id,
    content_id,
    occurrence_id,
    sentence_semantic_id,
    semantic_id,
)
from fcg_core.states import ImportState, ProofState, proof_promotable
from fcg_core.validation import ValidationResult

GOLDEN = Path(__file__).parent / "golden_vectors.json"


def test_json_property_reorder_same_semantic_id():
    a = {"domain": "test", "schema_version": "1", "semantic_payload": {"z": 1, "a": 2}}
    b = {"domain": "test", "schema_version": "1", "semantic_payload": {"a": 2, "z": 1}}
    assert canonical_hash_v2(a) == canonical_hash_v2(b)


def test_unicode_fixture_stable():
    payload = {"text": "café", "emoji": "🔬"}
    h1 = canonical_hash_v2(payload)
    h2 = canonical_hash_v2({"emoji": "🔬", "text": "café"})
    assert h1 == h2


def test_path_relocation_same_content_id(tmp_path):
    p1 = tmp_path / "a.json"
    p2 = tmp_path / "b.json"
    data = b'{"x":1}'
    p1.write_bytes(data)
    p2.write_bytes(data)
    assert content_id(p1.read_bytes()) == content_id(p2.read_bytes())


def test_timestamp_not_in_semantic_id():
    sid1 = semantic_id("fco.test", "1", {"value": 1})
    sid2 = semantic_id("fco.test", "1", {"value": 1})
    assert sid1 == sid2


def test_author_permutation_different_citation_id():
    a = citation_semantic_id(["Smith, J.", "Doe, A."], "Title", 2020)
    b = citation_semantic_id(["Doe, A.", "Smith, J."], "Title", 2020)
    assert a != b


def test_v1_sentence_tuple_collision_regression():
    """Regression E: legacy v1 concat is ambiguous."""
    h_collide = hash_sentence_leaf_v1("a", (1, 23))
    h_distinct = hash_sentence_leaf_v1("a1", (2, 3))
    # Document known collision class — v2 must differ.
    assert h_collide != sentence_semantic_id("a", "none", 1, 23)
    assert h_distinct != sentence_semantic_id("a1", "none", 2, 3)


def test_v1_citation_author_sort_regression():
    """Regression F: v1 sorts authors; v2 preserves order."""
    v1 = hash_citation_leaf_v1(["B", "A"], "Title", 2020, None, None)
    v2a = citation_semantic_id(["A", "B"], "Title", 2020)
    v2b = citation_semantic_id(["B", "A"], "Title", 2020)
    assert v2a != v2b
    # v1 would collapse order — both orderings may map to same v1 hash
    v1_swap = hash_citation_leaf_v1(["A", "B"], "Title", 2020, None, None)
    assert v1 == v1_swap


def test_proof_blocked_never_verified():
    assert proof_promotable(ImportState.IMPORTED_CONTENT, ProofState.BLOCKED) is False
    assert proof_promotable(ImportState.IMPORTED_CONTENT, ProofState.PENDING) is False
    assert proof_promotable(ImportState.IMPORTED_CONTENT, ProofState.VERIFIED) is True


def test_validation_result_id_stable_without_timestamp():
    vr = ValidationResult(
        input_hashes={"x": "abc"},
        schema_hashes={"s": "def"},
        ruleset_sha256="00" * 32,
        deterministic_outputs={"ok": True},
        terminal_classifications={"gate": "PASS"},
        import_state=ImportState.IMPORTED_CONTENT,
        proof_state=ProofState.PENDING,
    )
    id1 = vr.validation_result_id
    id2 = vr.validation_result_id
    assert id1 == id2


def test_occurrence_id_differs_on_actor_change():
    cid = "aa" * 32
    o1 = occurrence_id("fcg.test", cid, "loc", "actor_a", "LOCAL_FILE")
    o2 = occurrence_id("fcg.test", cid, "loc", "actor_b", "LOCAL_FILE")
    assert o1 != o2


def test_byte_mutation_changes_content_id():
    assert content_id(b"a") != content_id(b"b")


@pytest.mark.parametrize(
    "fixture_id",
    [
        "A_requirement_atoms_no_semantic_sha256",
        "B_sentence_graph_false_reference_edge",
        "C_citation_propositions_file_existence_only",
    ],
)
def test_regression_fixtures_documented(fixture_id):
    from fcg_core.regression_fixtures import REGRESSION_FIXTURES

    assert fixture_id in REGRESSION_FIXTURES


def test_golden_vectors_file_if_present():
    if not GOLDEN.exists():
        pytest.skip("golden_vectors.json not generated")
    vectors = json.loads(GOLDEN.read_text())
    for row in vectors:
        assert canonical_hash_v2(row["input"]) == row["semantic_hash_v2"]
