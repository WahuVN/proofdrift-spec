# Security Release Gate

A releasable ProofDrift public contract must pass structural schema validation, normative conformance, semantic traceability, independent Ajv validation, and `contracts/tools/security_release_gate.py`.

The release gate fails closed unless the schema index matches disk exactly, every public schema has exactly one named valid example, negative-example coverage is at least the schema count, all schema identities are immutable versioned URNs, no schema contains mutable branch references, and the critical replay/tamper/policy/provenance/MCP/secret-egress fixtures remain present.

The gate emits a deterministic SHA-256 over schemas, positive and negative examples, fixtures, normative conformance vectors, and `contracts/semantics.json`. Record that evidence with the independent validator score and the engine cross-repo result before tagging. An intentional contract-tree digest change must be explained by the spec changelog or migration notes; never weaken fixtures or validators merely to make a release gate green.
