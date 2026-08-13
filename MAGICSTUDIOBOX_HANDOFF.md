STATUS: PARTIAL

BEST PERTURBATION:
BR00118050:ADA

TOP REPURPOSING CANDIDATE:
desonide (desonide|PLA2G1B|BRD-K21528677-001-04-4)

CLAIM CEILING:
REPURPOSING_HYPOTHESIS

MOST IMPORTANT REAL METRIC:
phenotype opposition=0.5004939964057833; known_pair_rank=28

CLINICAL-PROGRESS EVIDENCE:
trial records: 50; phases: NA, PHASE1, PHASE1; PHASE2, PHASE2; statuses: ACTIVE_NOT_RECRUITING, COMPLETED, NOT_YET_RECRUITING, RECRUITING

CUSTODY VERIFIED:
yes

TAMPER TEST:
pass

TESTS:
baseline={'hash_reproducibility': 'PASS', 'provenance_completeness': 'PARTIAL_EXTERNAL_EVIDENCE', 'tamper_detection': 'PASS', 'claim_ceiling_compliance': 'PASS', 'continuity_classification': 'TRANSITION', 'false_continuity_test_cases': 'synthetic suite run in baseline', 'false_break_test_cases': 'synthetic suite run in baseline', 'known_pair_retrieval': 28, 'null_shuffle_comparison': {'seed': 260813, 'reciprocal_rank_enrichment_vs_shuffle': 0.24638253360287107}}

WHAT BYRON SHOULD DO FIRST:
Open deliverables/REPURPOSING_EVIDENCE_TABLE.md and verify the top candidate narrative against the clinical-progress rows before presenting.

Reproduce:
python scripts/magicstudiobox_repurposing_queue.py
