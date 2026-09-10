#!/usr/bin/env python3
"""Implementation-neutral ProofDrift schema conformance harness.

`emit` writes JSONL vectors containing opaque vector IDs, schema names and documents,
but no expected validity labels or valid/invalid path hints. A consumer validates each
document with its own implementation and returns JSONL rows shaped as
{"vector_id":"vector-...","accepted":true}. `score` compares those decisions with
the canonical positive/negative examples held privately by the scorer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALID = ROOT / "contracts" / "examples" / "valid"
INVALID = ROOT / "contracts" / "examples" / "invalid"
VECTOR_ID_DOMAIN = b"proofdrift-spec-conformance-v2\0"


def opaque_vector_id(source_id: str) -> str:
    digest = hashlib.sha256(VECTOR_ID_DOMAIN + source_id.encode("utf-8")).hexdigest()
    return f"vector-{digest[:20]}"


def load_vectors():
    vectors = []
    for path in sorted(VALID.glob("*.valid.json")):
        schema = path.name.removesuffix(".valid.json")
        source_id = f"valid/{path.name}"
        vectors.append(
            {
                "source_id": source_id,
                "vector_id": opaque_vector_id(source_id),
                "schema": schema,
                "document": json.loads(path.read_text(encoding="utf-8")),
                "expected": True,
            }
        )
    for path in sorted(INVALID.glob("*.invalid.json")):
        wrapper = json.loads(path.read_text(encoding="utf-8"))
        source_id = f"invalid/{path.name}"
        vectors.append(
            {
                "source_id": source_id,
                "vector_id": opaque_vector_id(source_id),
                "schema": wrapper["$expected_schema"],
                "document": wrapper["$document"],
                "expected": False,
            }
        )
    ids = [vector["vector_id"] for vector in vectors]
    if len(ids) != len(set(ids)):
        raise ValueError("opaque conformance vector ID collision")
    return vectors


def public_vectors(vectors):
    return [
        {k: vector[k] for k in ("vector_id", "schema", "document")}
        for vector in sorted(vectors, key=lambda item: item["vector_id"])
    ]


def suite_digest(vectors) -> str:
    encoded = json.dumps(
        public_vectors(vectors),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def emit(vectors):
    for vector in public_vectors(vectors):
        print(json.dumps(vector, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def load_results(path: Path):
    out = {}
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        row = json.loads(raw)
        vector_id, accepted = row.get("vector_id"), row.get("accepted")
        if not isinstance(vector_id, str) or not isinstance(accepted, bool):
            raise ValueError(f"line {line_no}: expected vector_id:string and accepted:boolean")
        if vector_id in out:
            raise ValueError(f"line {line_no}: duplicate vector_id {vector_id}")
        out[vector_id] = accepted
    return out


def score(vectors, results):
    expected_ids = {v["vector_id"] for v in vectors}
    missing = sorted(expected_ids - results.keys())
    unknown = sorted(results.keys() - expected_ids)
    if missing:
        raise ValueError(f"missing {len(missing)} results; first={missing[0]}")
    if unknown:
        raise ValueError(f"unknown {len(unknown)} results; first={unknown[0]}")
    per_schema = {}
    correct = 0
    failures = []
    for vector in vectors:
        actual = results[vector["vector_id"]]
        ok = actual is vector["expected"]
        correct += int(ok)
        stats = per_schema.setdefault(vector["schema"], {"total": 0, "correct": 0})
        stats["total"] += 1
        stats["correct"] += int(ok)
        if not ok:
            failures.append(
                {
                    "vector_id": vector["vector_id"],
                    "schema": vector["schema"],
                    "expected_accepted": vector["expected"],
                    "actual_accepted": actual,
                }
            )
    for stats in per_schema.values():
        stats["rate"] = stats["correct"] / stats["total"]
    return {
        "schema_version": "2",
        "suite": "proofdrift_spec_conformance",
        "suite_digest": suite_digest(vectors),
        "vectors": len(vectors),
        "correct": correct,
        "conformance_rate": correct / len(vectors) if vectors else None,
        "per_schema": dict(sorted(per_schema.items())),
        "failures": failures,
    }


def self_test(vectors):
    public = public_vectors(vectors)
    assert all(set(vector) == {"vector_id", "schema", "document"} for vector in public)
    assert all(vector["vector_id"].startswith("vector-") for vector in public)
    assert all("valid" not in vector["vector_id"] for vector in public)
    assert all("invalid" not in vector["vector_id"] for vector in public)
    result = score(vectors, {v["vector_id"]: v["expected"] for v in vectors})
    assert result["conformance_rate"] == 1.0
    assert len(result["suite_digest"]) == 64
    return result


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("emit")
    score_parser = sub.add_parser("score")
    score_parser.add_argument("results", type=Path)
    score_parser.add_argument("--require-perfect", action="store_true")
    sub.add_parser("self-test")
    args = parser.parse_args()
    vectors = load_vectors()
    if args.command == "emit":
        emit(vectors)
        return 0
    if args.command == "self-test":
        print(json.dumps(self_test(vectors), indent=2, sort_keys=True))
        return 0
    result = score(vectors, load_results(args.results))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 2 if args.require_perfect and result["conformance_rate"] != 1.0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
