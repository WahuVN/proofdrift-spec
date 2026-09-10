#!/usr/bin/env python3
"""Validate normative ProofDrift semantic requirements and fixture traceability."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEMANTICS = ROOT / "contracts" / "semantics.json"
FIXTURES = ROOT / "contracts" / "fixtures"
ID_RE = re.compile(r"^PD-[A-Z][A-Z0-9_-]*-[0-9]{3}$")
ALLOWED_LEVELS = {"MUST", "MUST_NOT", "SHOULD", "SHOULD_NOT", "MAY"}


def canonical_digest(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    doc = json.loads(SEMANTICS.read_text(encoding="utf-8"))
    failures: list[str] = []
    if doc.get("schema_version") != "1.0.0":
        failures.append("schema_version must be 1.0.0")
    if doc.get("suite") != "proofdrift-semantic-requirements":
        failures.append("suite name is invalid")

    requirements = doc.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        failures.append("requirements must be a non-empty array")
        requirements = []

    seen: set[str] = set()
    traced_fixtures: set[str] = set()
    for index, requirement in enumerate(requirements):
        where = f"requirements[{index}]"
        if not isinstance(requirement, dict):
            failures.append(f"{where}: must be an object")
            continue
        rid = requirement.get("id")
        if not isinstance(rid, str) or not ID_RE.fullmatch(rid):
            failures.append(f"{where}: invalid requirement id {rid!r}")
            continue
        if rid in seen:
            failures.append(f"{where}: duplicate requirement id {rid}")
        seen.add(rid)

        level = requirement.get("level")
        if level not in ALLOWED_LEVELS:
            failures.append(f"{rid}: invalid normative level {level!r}")
        title = requirement.get("title")
        statement = requirement.get("statement")
        if not isinstance(title, str) or not title.strip():
            failures.append(f"{rid}: title must be non-empty")
        if not isinstance(statement, str) or not statement.strip():
            failures.append(f"{rid}: statement must be non-empty")
        else:
            keyword = str(level).replace("_", " ") if level in ALLOWED_LEVELS else ""
            if keyword and keyword not in statement:
                failures.append(f"{rid}: statement must contain normative keyword {keyword}")

        fixtures = requirement.get("fixtures")
        if not isinstance(fixtures, list) or not fixtures:
            failures.append(f"{rid}: fixtures must be a non-empty list")
            fixtures = []
        if len(fixtures) != len(set(fixtures)):
            failures.append(f"{rid}: duplicate fixture references")
        for name in fixtures:
            if not isinstance(name, str) or Path(name).name != name or not name.endswith(".json"):
                failures.append(f"{rid}: unsafe fixture reference {name!r}")
                continue
            fixture = FIXTURES / name
            if not fixture.is_file():
                failures.append(f"{rid}: fixture not found: {name}")
            else:
                traced_fixtures.add(name)

        evidence = requirement.get("evidence")
        if (
            not isinstance(evidence, list)
            or not evidence
            or not all(isinstance(item, str) and item for item in evidence)
        ):
            failures.append(f"{rid}: evidence must be a non-empty list of strings")
        elif len(evidence) != len(set(evidence)):
            failures.append(f"{rid}: duplicate evidence names")

    fixture_files = {path.name for path in FIXTURES.glob("*.json")}
    missing_trace = sorted(fixture_files - traced_fixtures)
    if missing_trace:
        failures.append(
            "fixtures without normative requirement trace: " + ", ".join(missing_trace)
        )
    trace_coverage = len(traced_fixtures) / len(fixture_files) if fixture_files else 1.0
    result = {
        "schema_version": "1",
        "suite": "proofdrift_semantic_requirement_validation",
        "requirements": len(requirements),
        "unique_requirement_ids": len(seen),
        "referenced_fixtures": len(traced_fixtures),
        "available_fixtures": len(fixture_files),
        "fixture_trace_coverage": trace_coverage,
        "semantic_digest": canonical_digest(doc),
    }

    if failures:
        print("semantic validation FAILED", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
