# ProofDrift Spec

[![Spec CI](https://github.com/WahuVN/proofdrift-spec/actions/workflows/ci.yml/badge.svg)](https://github.com/WahuVN/proofdrift-spec/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Versioned public data contracts for ProofDrift. This repository contains deterministic JSON Schemas, canonical positive/negative examples, reusable fixtures, and the generator/validator used to keep the contract reproducible.

## Contract set

The v1 set covers artifact identity, evidence values, capabilities, agent events, policy requests/decisions, findings, patch impact, test evidence, provenance edges, trust reports, evidence bundle manifests, baseline snapshots and trust diffs.

Schemas use JSON Schema Draft 2020-12. Additive object fields are permitted where forward compatibility is intentional; security-relevant fields remain constrained by required keys, enums, digest formats, ranges and path rules.

## Validate

```sh
python -m pip install -r requirements.txt
python contracts/tools/validate_examples.py
python contracts/tools/conformance.py self-test
python contracts/tools/validate_semantics.py
```

## Normative semantics

`contracts/semantics.json` defines stable `PD-*-NNN` requirements for passive discovery, evidence integrity, approval binding, enforcement strength, policy binding, provenance, test proof, bundle safety, capability drift, MCP schema drift, nested shells and secret egress. Every checked-in fixture is referenced by at least one normative requirement, and CI requires **100% fixture trace coverage**.

## Cross-implementation conformance

The repository now includes an implementation-neutral JSONL conformance protocol. It emits checked-in positive and negative contract vectors with **opaque vector IDs and no expected labels or valid/invalid path hints**, so another implementation can validate them independently and return only its accept/reject decisions.

```sh
python contracts/tools/conformance.py emit > proofdrift-conformance-vectors.jsonl
# External implementation writes one row per vector:
# {"vector_id":"vector-0123456789abcdef0123","accepted":true}
python contracts/tools/conformance.py score external-results.jsonl --require-perfect
```

The scorer records a deterministic `suite_digest` so an external result can be tied to the exact vector set. CI also validates the same opaque vectors with **Ajv 8.20.0 on Node 24** and requires a perfect score from that independent JSON Schema implementation. A passing Python self-test still verifies only the harness; interoperability evidence is the independently produced Ajv result.

Schema `$id` values are versioned immutable URNs such as `urn:proofdrift:schema:1.0.0:agent-event`; they do not point at a mutable `main` branch. `contracts/schemas/index.json` records the filename-to-URN map for consumers.

## Regenerate

```sh
python contracts/tools/generate_contracts.py
python contracts/tools/validate_examples.py
```

Generation is deterministic. A clean regeneration should not create an unexplained diff.

## Versioning

- `schema_version` is semantic-version shaped.
- Additive compatible fields may land in minor/patch v1 revisions.
- Breaking wire changes require a new major version and explicit migration notes.
- Consumers may enforce stricter resource limits than the schema ceiling, but must not silently weaken schema invariants.

The executable implementation lives in [WahuVN/proofdrift](https://github.com/WahuVN/proofdrift). Security/adversarial cases live in [WahuVN/proofdrift-bench](https://github.com/WahuVN/proofdrift-bench).

## License

Apache License 2.0. See [LICENSE](LICENSE).
