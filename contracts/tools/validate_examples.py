#!/usr/bin/env python3
"""Independently validate generated schemas/examples/fixtures with jsonschema."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "contracts" / "schemas"
VALID = ROOT / "contracts" / "examples" / "valid"
INVALID = ROOT / "contracts" / "examples" / "invalid"
FIXTURES = ROOT / "contracts" / "fixtures"


def load(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    schemas: dict[str, dict] = {}
    resources: list[tuple[str, Resource]] = []
    failures: list[str] = []

    for path in sorted(SCHEMAS.glob("*.schema.json")):
        document = load(path)
        try:
            Draft202012Validator.check_schema(document)
        except Exception as exc:  # validator provides rich exception types
            failures.append(f"SCHEMA {path.name}: {exc}")
            continue
        name = path.name.removesuffix(".schema.json")
        schemas[name] = document
        resources.append((document["$id"], Resource.from_contents(document)))

    registry = Registry().with_resources(resources)

    valid_count = 0
    for path in sorted(VALID.glob("*.valid.json")):
        name = path.name.removesuffix(".valid.json")
        if name not in schemas:
            failures.append(f"VALID {path.name}: no matching schema {name}")
            continue
        validator = Draft202012Validator(schemas[name], registry=registry)
        errors = sorted(validator.iter_errors(load(path)), key=lambda e: list(e.path))
        if errors:
            failures.append(f"VALID {path.name}: unexpectedly rejected: {errors[0].message}")
        else:
            valid_count += 1

    invalid_count = 0
    for path in sorted(INVALID.glob("*.invalid.json")):
        wrapper = load(path)
        name = wrapper.get("$expected_schema")
        document = wrapper.get("$document")
        if name not in schemas:
            failures.append(f"INVALID {path.name}: no matching schema {name}")
            continue
        validator = Draft202012Validator(schemas[name], registry=registry)
        errors = list(validator.iter_errors(document))
        if not errors:
            failures.append(f"INVALID {path.name}: unexpectedly accepted")
        else:
            invalid_count += 1

    fixture_validator = Draft202012Validator(schemas["fixture-case"], registry=registry)
    fixture_count = 0
    ids: set[str] = set()
    for path in sorted(FIXTURES.glob("*.json")):
        document = load(path)
        errors = list(fixture_validator.iter_errors(document))
        if errors:
            failures.append(f"FIXTURE {path.name}: {errors[0].message}")
            continue
        fixture_id = document["fixture_id"]
        if fixture_id in ids:
            failures.append(f"FIXTURE {path.name}: duplicate fixture_id {fixture_id}")
            continue
        ids.add(fixture_id)
        fixture_count += 1

    if failures:
        print("contract validation FAILED", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(
        f"contract validation PASS: {len(schemas)} schemas, "
        f"{valid_count} valid examples, {invalid_count} negative examples, "
        f"{fixture_count} fixtures"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
