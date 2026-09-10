# Contracts

- `schemas/` contains generated JSON Schemas.
- `examples/valid/` contains canonical valid examples.
- `examples/invalid/` contains negative examples that must be rejected.
- `fixtures/` contains reusable cross-component regression fixtures.
- `tools/generate_contracts.py` is the deterministic source generator.
- `tools/validate_examples.py` independently validates schemas, examples and fixtures.

Edit the generator, regenerate, validate, and commit both generator and generated artifacts in the same change.
