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
```

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
