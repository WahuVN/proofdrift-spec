#!/usr/bin/env python3
"""Fail-closed release gate for the public ProofDrift contract repository."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "contracts"
SCHEMAS = CONTRACTS / "schemas"
VALID = CONTRACTS / "examples" / "valid"
INVALID = CONTRACTS / "examples" / "invalid"
FIXTURES = CONTRACTS / "fixtures"
CONFORMANCE = CONTRACTS / "conformance"
SEMANTICS = CONTRACTS / "semantics.json"
CRITICAL_FIXTURES = {
    "approval-replay.json",
    "bundle-corrupted-byte.json",
    "policy-digest-changed.json",
    "provenance-missing-edge.json",
    "mcp-tool-schema-drift.json",
    "secret-egress-attempt.json",
}
MUTABLE_ID_TOKENS = (
    "raw.githubusercontent.com/",
    "/main/",
    "/master/",
    "refs/heads/",
)


def digest_tree(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for path in sorted(paths):
        h.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def contract_files() -> list[Path]:
    files = (
        list(SCHEMAS.glob("*.json"))
        + list(VALID.glob("*.json"))
        + list(INVALID.glob("*.json"))
        + list(FIXTURES.glob("*.json"))
        + list(CONFORMANCE.rglob("*.json"))
    )
    if SEMANTICS.is_file():
        files.append(SEMANTICS)
    return files


def main() -> int:
    index = json.loads((SCHEMAS / "index.json").read_text(encoding="utf-8-sig"))
    indexed = set(index["schemas"])
    actual = {p.name for p in SCHEMAS.glob("*.schema.json")}
    if indexed != actual:
        raise SystemExit(
            f"schema index mismatch: indexed={sorted(indexed)} actual={sorted(actual)}"
        )

    schema_names = {p.removesuffix(".schema.json") for p in indexed}
    schema_ids = index.get("schema_ids")
    if not isinstance(schema_ids, dict) or set(schema_ids) != schema_names:
        raise SystemExit("schema_ids must cover every public schema exactly once")
    for name in sorted(schema_names):
        expected = f"urn:proofdrift:schema:{index['schema_version']}:{name}"
        if schema_ids[name] != expected:
            raise SystemExit(f"non-canonical schema id for {name}: {schema_ids[name]!r}")
        document = json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8-sig"))
        if document.get("$id") != expected:
            raise SystemExit(f"schema $id mismatch for {name}")
        encoded = json.dumps(document, sort_keys=True)
        if any(token in encoded for token in MUTABLE_ID_TOKENS):
            raise SystemExit(f"mutable schema identity/reference found in {name}")

    valid = {p.name.removesuffix(".valid.json") for p in VALID.glob("*.valid.json")}
    if valid != schema_names:
        raise SystemExit("every public schema must have exactly one named valid example")

    missing = CRITICAL_FIXTURES - {p.name for p in FIXTURES.glob("*.json")}
    if missing:
        raise SystemExit(f"missing critical security fixtures: {sorted(missing)}")

    invalid_count = len(list(INVALID.glob("*.invalid.json")))
    if invalid_count < len(indexed):
        raise SystemExit(
            f"negative example coverage too low: {invalid_count} invalid / {len(indexed)} schemas"
        )
    if not SEMANTICS.is_file():
        raise SystemExit("contracts/semantics.json is required for release")
    if not any(CONFORMANCE.glob("*.json")):
        raise SystemExit("at least one normative conformance vector set is required")

    evidence = {
        "gate": "proofdrift_spec_security_release_gate",
        "status": "pass",
        "schema_version": index["schema_version"],
        "canonicalization": index["canonicalization"],
        "schemas": len(indexed),
        "immutable_schema_ids": len(schema_ids),
        "valid_examples": len(valid),
        "invalid_examples": invalid_count,
        "fixtures": len(list(FIXTURES.glob("*.json"))),
        "critical_fixtures": sorted(CRITICAL_FIXTURES),
        "conformance_documents": len(list(CONFORMANCE.rglob("*.json"))),
        "semantic_contract": SEMANTICS.relative_to(ROOT).as_posix(),
        "contract_tree_sha256": digest_tree(contract_files()),
    }
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
