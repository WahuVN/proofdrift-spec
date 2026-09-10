# ProofDrift Normative Specification v1

The key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are normative requirements.

## 1. Versioning and compatibility

Every wire object MUST contain `schema_version`. A v1 parser MUST accept syntactically valid `1.x.y` documents that satisfy the applicable schema. Unknown additive fields MUST be preserved or ignored without changing the meaning of known fields. A producer MUST NOT repurpose an existing field incompatibly inside major version 1. An evaluator receiving an unsupported major version MUST fail closed with an `unsupported_version` tool/configuration error; it MUST NOT guess semantics. Breaking wire changes require a new major version and migration notes.

## 2. Canonicalization and digest

`proofdrift-json-v1` is deterministic JSON canonicalization for digest inputs. The value being digested MUST first omit the digest field that is being computed, then be serialized as UTF-8 JSON with object keys sorted by Unicode code point, no insignificant whitespace, JSON literals in lowercase, strings escaped according to JSON, and array order preserved. Implementations MUST reject NaN and infinities. The digest is SHA-256 over those exact UTF-8 bytes and is represented as 64 lowercase hexadecimal characters, optionally prefixed by `sha256:` where the schema permits that form. Two semantically identical objects with different object-member ordering MUST produce the same digest. Array reordering is semantic and MUST change the digest unless that array is explicitly defined as order-insensitive by a higher-level contract.

## 3. EvidenceReference

`EvidenceReference` identifies evidence without embedding mutable content. `ref_id`, `kind`, `uri`, and `digest` are REQUIRED. `digest` MUST identify the bytes or canonical JSON content referenced by `uri`. Producers MUST NOT claim `verified` provenance merely because a URI exists; verification requires successful digest or equivalent attestation verification.

## 4. EvidenceEnvelope

An `EvidenceEnvelope` is the portable evidence boundary. It MUST contain `schema_version`, `subject`, `provenance`, `sequence`, `policy_context`, `capability_context`, `decision`, `evidence_refs`, and `digest`. `timestamp` SHOULD be present when wall-clock freshness matters. `sequence` MUST be monotonic within a subject/session stream. `provenance` MUST describe the origin of the evaluated subject. `policy_context` and `capability_context` MUST reflect the context actually used for evaluation, not a later reconstruction. Every security-relevant claim SHOULD be traceable through `evidence_refs`. The envelope digest MUST cover the envelope using `proofdrift-json-v1` with its own `digest` field omitted.

## 5. EvaluationDecision

An `EvaluationDecision` MUST contain `decision_id`, `subject`, `verdict`, `findings`, `evidence_refs`, and `digest`. `verdict` is one of `pass`, `warn`, or `block`. `block` means the evaluated operation MUST NOT proceed automatically. `warn` means policy permits continuation but the caller SHOULD surface the findings. `pass` means no blocking or warning drift was found under the supplied evidence and policy context; it is not a claim of global safety. The decision digest MUST cover all decision fields except its own `digest`.

## 6. DriftFinding

Each finding MUST contain exactly one normative `drift_class` from the six classes below, a `verdict`, human-readable `explanation`, traceable `evidence_refs`, and deterministic `fingerprint`. The fingerprint SHOULD be stable across runs for the same rule/class/subject/before/after evidence and MUST NOT depend on timestamps, map iteration order, random identifiers, or filesystem traversal order.

## 7. Six drift classes

### provenance drift
A change or contradiction in origin, revision, digest, attestation, dependency lineage, or provenance coverage. Positive example: the same artifact ID resolves from immutable commit A to unrelated commit B without an accepted migration. Negative example: only a display label changes while immutable revision and digest remain identical.

### capability drift
A change in what actions/resources a subject can access. Positive example: network scope expands from `github.com/api/**` to `**`. Negative example: capability ordering changes but the normalized capability set is identical.

### policy drift
A change in effective policy, policy digest, decision rule, enforcement coverage, or policy precedence. Positive example: an explicit deny becomes allow. Negative example: policy source formatting changes while its canonical policy digest and effective decision remain identical.

### runtime drift
A change in observed runtime behavior or enforcement relative to the declared/evaluated state. Positive example: an operation declared isolated executes at enforcement level L0. Negative example: event object keys are reordered but canonical content and sequence remain unchanged.

### patch-impact drift
A change in patch scope, affected sensitive surfaces, dependency impact, or blast radius. Positive example: a patch that formerly changed docs now modifies authentication code. Negative example: source files are renamed without changing normalized affected symbols/surfaces and the implementation can prove semantic equivalence.

### test-proof drift
A change in test evidence, coverage mapping, environment fingerprint, result integrity, or freshness sufficient to alter confidence. Positive example: a previously observed passing test becomes claimed-only or its tested artifact hash no longer matches. Negative example: test log formatting changes while command, tested artifact digest, result, environment fingerprint, and mapped tests remain identical.

## 8. Ordering and unknown fields

Object member order MUST NOT affect semantics. Array order is significant unless the field contract explicitly declares set semantics. For arrays modeled with `uniqueItems`, producers SHOULD emit a deterministic stable order. Parsers MUST ignore unknown additive fields in supported major versions unless local policy rejects them for resource or security limits; parsers MUST NOT reinterpret an unknown field as a known one.

## 9. Failure behavior

Malformed JSON, schema violations, invalid digests, unsupported major versions, duplicate IDs where uniqueness is required, broken evidence references, and impossible version negotiation MUST produce explicit errors and MUST NOT crash the parser/evaluator. Evaluators SHOULD fail closed when missing or invalid evidence could turn a block into a pass. Error text SHOULD identify the object, field/path, expected invariant, and observed problem.

## 10. Conformance levels

**Parser conformance** requires JSON/schema validation, supported-version negotiation, unknown-field behavior, canonicalization, digest verification, and deterministic error handling.

**Producer conformance** includes parser conformance plus emission of required fields, deterministic ordering where applicable, canonical digests, traceable evidence references, and no incompatible v1 field repurposing.

**Evaluator/runtime conformance** includes producer conformance plus classification of all six drift classes, deterministic pass/warn/block decisions, evidence-linked explanations, replay/staleness handling, and fail-closed behavior for security-relevant missing evidence.

## 11. Threat model

Implementations MUST consider forged provenance, stale evidence, capability escalation, policy downgrade, replay, and tampering. Digest verification alone proves integrity against accidental or detectable mutation but not authority; provenance trust requires an authenticated trust root or attestation policy. Freshness-sensitive evidence SHOULD carry timestamp and/or monotonic sequence context. Replayed approvals or decisions MUST NOT be accepted when policy defines them as single-use or superseded. A lower-trust policy or capability assertion MUST NOT silently override a higher-trust restrictive assertion.

## 12. External implementation checklist

An implementation is ready for independent interoperability when it can: parse every published valid example; reject every published invalid example; validate every schema; compute canonical digests identically; negotiate supported versions; ignore additive unknown v1 fields safely; preserve array semantics; classify each positive drift case and reject each negative control; emit deterministic findings/decisions; trace every security-relevant finding to evidence; and fail closed on tampered, replayed, stale, or unsupported security-relevant input.
