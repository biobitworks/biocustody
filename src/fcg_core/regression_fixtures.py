"""Regression fixtures A–M preserved as explicit failing/passing contracts."""

from __future__ import annotations

REGRESSION_FIXTURES: dict[str, dict] = {
    "A_requirement_atoms_no_semantic_sha256": {
        "repo": "protein-hinge",
        "path": "paper/newinml2026/submission/FINAL_REQUIREMENT_ATOMS.jsonl",
        "defect": "human atom_id without individual canonical SHA-256 per atom",
        "expected_gate": "FAIL until semantic_id per atom",
    },
    "B_sentence_graph_false_reference_edge": {
        "repo": "protein-hinge",
        "defect": "page-limit sentence linked to REQ-REF-* because substring 'references'",
        "expected_gate": "FAIL on semantic edge validation",
    },
    "C_citation_propositions_file_existence_only": {
        "repo": "protein-hinge",
        "gate": "ALL_CITATION_PROPOSITIONS_MAPPED",
        "defect": "PASS if CITATION_EVIDENCE_MAP.csv exists",
    },
    "D_sentence_integrity_bibtex_key_only": {
        "repo": "protein-hinge",
        "defect": "FINAL_SENTENCE_CITATION_INTEGRITY proves bib key existence only",
    },
    "E_seedgraph_sentence_tuple_concat": {
        "repo": "seedgraph",
        "path": "src/seedgraph/merkle/atoms.py:hash_sentence_leaf",
        "defect": "('a1',2,3) vs ('a',12,3) collision risk",
    },
    "F_seedgraph_citation_author_sort": {
        "repo": "seedgraph",
        "defect": "sorted(authors) collapses author-order distinctions",
    },
    "G_seedgraph_import_proof_decoupling": {
        "repo": "seedgraph",
        "defect": "IMPORTED_CONTENT while proof_state pending_proof/blocked",
    },
    "H_seedgraph_manifest_path_only": {
        "repo": "protein-hinge",
        "defect": "SEEDGRAPH_SUBMISSION_DELTA_MANIFEST.jsonl path-only pre-import",
    },
    "I_seedgraph_head_replayability": {
        "repo": "seedgraph",
        "sha": "6807b1960dd1e981afbf13e79c2f29c3d803b79a",
        "defect": "execution receipt must bind exact source-tree custody",
    },
    "J_project_control_stale": {
        "repo": "protein-hinge",
        "defect": "PROJECT_CONTROL derived state stale vs latest seal",
    },
    "K_ci_receipt_missing_semantic_binding": {
        "repo": "protein-hinge",
        "defect": "FINAL_CI_OPERATOR_RECEIPT lacks citation/sentence audit SHA bindings",
    },
    "L_python_requirements_unlocked": {
        "repo": "protein-hinge",
        "defect": "requirements.txt unpinned",
    },
    "M_ci_mutable_environment": {
        "repo": "protein-hinge",
        "defect": "ubuntu-latest, action majors, mutable package mirrors",
    },
}
