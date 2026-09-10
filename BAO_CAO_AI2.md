# Summary

AI 2 upgraded `proofdrift-spec` from a schema repository into an implementation-independent normative contract. The branch adds explicit MUST/SHOULD/MAY semantics, deterministic canonicalization/digest rules, version negotiation and unknown-field behavior, six normative drift classes with positive/negative controls, three conformance levels, a threat model, and additive wire schemas for evidence and evaluation outputs.

# Files changed

- `SPECIFICATION.md`: normative v1 contract, failure behavior, versioning, canonicalization, six drift classes, conformance levels, threat model, external implementation checklist.
- `README.md`: links the normative specification.
- `contracts/tools/generate_contracts.py`: adds four additive schemas and registers them in deterministic generation.
- `contracts/schemas/evidence-reference.schema.json`: evidence reference wire contract.
- `contracts/schemas/evidence-envelope.schema.json`: portable evidence envelope.
- `contracts/schemas/drift-finding.schema.json`: normative six-class drift finding.
- `contracts/schemas/evaluation-decision.schema.json`: pass/warn/block decision envelope.
- `contracts/schemas/index.json`: generated schema index now lists 19 schemas.
- `contracts/conformance/drift-cases.json`: positive and negative controls for all six drift classes.
- `contracts/tools/validate_conformance.py`: checks six-class coverage and canonicalization invariants.
- `.github/workflows/ci.yml`: runs conformance validation in CI.

# Tests added

- Positive/negative conformance pair for each of: provenance drift, capability drift, policy drift, runtime drift, patch-impact drift, test-proof drift.
- Canonicalization object-member-order invariance.
- Array-order significance.
- NaN rejection.

# Commands run + exact result

- `python contracts/tools/validate_examples.py` before changes: `contract validation PASS: 15 schemas, 15 valid examples, 16 negative examples, 24 fixtures`.
- `python contracts/tools/generate_contracts.py`: `generated 19 schemas, 15 valid examples, 16 invalid examples, 24 fixtures`.
- `python contracts/tools/validate_examples.py`: `contract validation PASS: 19 schemas, 15 valid examples, 16 negative examples, 24 fixtures`.
- `python contracts/tools/validate_conformance.py`: `conformance validation PASS: 6 drift classes + canonicalization invariants`.
- `python -m compileall -q contracts/tools`: exit 0.
- `git diff --check`: exit 0; only Git CRLF normalization warnings, no whitespace errors.
- Re-run generator with SHA-256 comparison of all schema files: `deterministic regeneration PASS`.

# Public API/schema changes

Additive only. Four new schemas were introduced: `EvidenceReference`, `EvidenceEnvelope`, `DriftFinding`, and `EvaluationDecision`. Existing 15 schemas and their required fields/enums were not removed or repurposed. Normative drift class names are exactly: `provenance drift`, `capability drift`, `policy drift`, `runtime drift`, `patch-impact drift`, `test-proof drift`.

# Compatibility risks

- Engine/CLI implementations must align their public drift-class spelling and pass/warn/block output with the normative schema before claiming evaluator/runtime conformance.
- `proofdrift-json-v1` is now specified precisely; implementations using a different JSON canonicalization algorithm may produce different digests and require migration/adaptation.
- Additive v1 fields are allowed by current schemas. Strict consumers that reject unknown fields are not conformant with the new parser rules unless a local resource/security policy explicitly requires rejection.

# Known remaining issues

- The existing legacy domain schemas still use some broad `additionalProperties: true` and unconstrained free-form objects. Tightening those would be potentially breaking and was intentionally not done on this additive AI 2 branch.
- Cross-repo implementation compatibility must be validated by AI 5 after AI 1/AI 4 public outputs settle.
- The conformance drift pairs define expected classification semantics but do not implement the evaluator; execution against engine outputs belongs to the engine/quality-gate repos.

# Merge notes

Merge/review this branch before accepting incompatible public API changes from engine/CLI work. Because changes are additive, normal merge is preferred. If AI 5 also edits CI, retain both the conformance validation step and AI 5 security/quality steps. Do not rename the six normative drift classes during conflict resolution.

# Score before/after theo thang 10 va bang chung

- Before: 8.5/10. Evidence: strong deterministic JSON Schema corpus and validation existed, but normative semantics, drift taxonomy, canonicalization algorithm, conformance levels, version negotiation, and threat model were missing or underspecified.
- After: 9.7/10 for the spec repository in isolation. Evidence: 19 validated schemas, explicit normative contract, six-class positive/negative conformance controls, deterministic canonicalization tests, CI integration, version/failure semantics, external implementation checklist, and threat model. The remaining 0.3 depends on cross-repo independent implementation proof and compatibility gating owned by AI 5 / downstream implementations.
