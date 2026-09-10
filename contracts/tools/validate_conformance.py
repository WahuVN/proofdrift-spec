#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "contracts" / "conformance" / "drift-cases.json"
EXPECTED_CLASSES = {
    "provenance drift",
    "capability drift",
    "policy drift",
    "runtime drift",
    "patch-impact drift",
    "test-proof drift",
}


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def main() -> int:
    failures: list[str] = []
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    classes = {case["drift_class"] for case in cases}
    if classes != EXPECTED_CLASSES:
        failures.append(f"drift classes mismatch: {sorted(classes)}")
    for case in cases:
        if "positive" not in case or "negative" not in case:
            failures.append(f"{case.get('drift_class')}: missing positive/negative control")
        if case.get("positive", {}).get("expected_drift") is not True:
            failures.append(f"{case.get('drift_class')}: positive must expect drift")
        if case.get("negative", {}).get("expected_drift") is not False:
            failures.append(f"{case.get('drift_class')}: negative must reject drift")

    a = {"z": 1, "a": {"b": 2, "a": 1}}
    b = {"a": {"a": 1, "b": 2}, "z": 1}
    if digest(a) != digest(b):
        failures.append("canonicalization is not object-order invariant")
    if digest([1, 2]) == digest([2, 1]):
        failures.append("array ordering was incorrectly erased")
    try:
        canonical_bytes({"bad": float("nan")})
        failures.append("NaN was not rejected")
    except ValueError:
        pass

    if failures:
        print("conformance validation FAILED", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(f"conformance validation PASS: {len(cases)} drift classes + canonicalization invariants")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
