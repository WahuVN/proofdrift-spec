# Contracts

- `schemas/` contains generated JSON Schemas.
- `examples/valid/` contains canonical valid examples.
- `examples/invalid/` contains negative examples that must be rejected.
- `fixtures/` contains reusable cross-component regression fixtures.
- `semantics.json` contains stable normative requirement IDs (`PD-*-NNN`) with MUST/MUST NOT semantics and fixture/evidence traceability.
- `tools/generate_contracts.py` is the deterministic source generator.
- `tools/validate_examples.py` independently validates schemas, examples and fixtures.
- `tools/validate_semantics.py` validates requirement IDs, normative wording, evidence declarations and 100% fixture reference coverage.
- `tools/conformance.py` emits opaque implementation-neutral schema vectors and scores external accept/reject decisions.

Edit the generator, regenerate, validate, and commit both generator and generated artifacts in the same change.
