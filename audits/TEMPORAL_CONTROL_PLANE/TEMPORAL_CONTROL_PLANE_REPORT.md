# Temporal Control Plane Report

Generated: 2026-08-29T09:02:05Z  
Branch: `audit/custody-portability-core-20260829` (biocustody)  
Sealed NewInML PDF: **NOT MODIFIED**

## CURRENT_OPERATOR_BLOCKERS

- **MISTRAL_API_KEY** priority=P5 waits=1 blocks=MISTRAL_API_KEY value_logged=NO

## HydraDG context scoring

- Implementation found: **YES (scoped)** — `hydradg/hydralamp/context_score.py`
- Source SHA-256: `ec466ec31bb2dfb9cdd12954ed0b1fa8dd015a488725d6a33650e6b5cdaf35e6`
- Ruleset SHA-256: `17a88ab076c09fcb6a21de9902ba6d153724e8f752386c8c91279e7427b187d1`
- Claim ceiling: **CONTEXT_ROUTING_DIAGNOSTIC_ONLY** — not promoted to universal DG_CONTEXT for custody-plane rows

## AntiCube

- Implementation found: **YES (scoped)** — `hydradg/scripts/classify_ic_failure_anticube.py`
- Ruleset SHA-256: `d48e1daa8582cc1ee938b931c8a4852e0d2b759f4c39d80266d559af3a8681b4`
- Active rows default: **NOT_EVALUATED** until ClassificationReceipt

## PROJECT_DOCUMENT_001

- Sentences mapped: 24
- Table propositional cells: 7
- Figures: 1
- Citation keys: 8
- Unresolved sentence→SOT→AOK paths: 0

## Claim ceilings

- CUSTODY_PORTABILITY: PARTIAL_EVIDENCE
- DG_CONTEXT_SCORING (custody plane): NOT_ESTABLISHED
- ANTICUBE (active rows): NOT_EVALUATED
