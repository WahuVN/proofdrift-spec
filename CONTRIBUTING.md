# Contributing

Contract changes require both generated artifacts and validation evidence.

```sh
python -m pip install -r requirements.txt
python contracts/tools/generate_contracts.py
python contracts/tools/validate_examples.py
```

For a breaking change, document the migration path and use a new major schema version. Do not repurpose an existing field with incompatible semantics.

Do not include real credentials, private repository data or machine-specific paths in fixtures.
