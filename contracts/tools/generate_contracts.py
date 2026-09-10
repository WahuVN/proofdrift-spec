#!/usr/bin/env python3
"""Generate ProofDrift v1 JSON Schemas, canonical examples, and shared fixtures.

The generator is deterministic: sorted keys, fixed indentation, and fixed fixture data.
It intentionally uses only the Python standard library so contract generation does not
require a network or package manager.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "contracts" / "schemas"
VALID = ROOT / "contracts" / "examples" / "valid"
INVALID = ROOT / "contracts" / "examples" / "invalid"
FIXTURES = ROOT / "contracts" / "fixtures"
BASE = "https://raw.githubusercontent.com/WahuVN/proofdrift-spec/main/contracts/schemas/"
VERSION_PATTERN = r"^1\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$"
SHA256_PATTERN = r"^(?:sha256:)?[0-9a-fA-F]{64}$"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def ref(name: str) -> dict:
    return {"$ref": BASE + name + ".schema.json"}


def arr(items: dict, *, unique: bool = False) -> dict:
    result = {"type": "array", "items": items}
    if unique:
        result["uniqueItems"] = True
    return result


def string(*, enum: list[str] | None = None, pattern: str | None = None, min_len: int = 1) -> dict:
    value: dict = {"type": "string", "minLength": min_len}
    if enum is not None:
        value["enum"] = enum
    if pattern is not None:
        value["pattern"] = pattern
    return value


def obj(required: list[str], properties: dict, *, additional: bool = True) -> dict:
    return {
        "type": "object",
        "required": required,
        "properties": properties,
        "additionalProperties": additional,
    }


def schema(name: str, title: str, body: dict) -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": BASE + name + ".schema.json",
        "title": title,
        **body,
    }


schema_version = string(pattern=VERSION_PATTERN)
confidence = {"type": "number", "minimum": 0, "maximum": 1}
digest = string(pattern=SHA256_PATTERN)
metadata = {"type": "object", "additionalProperties": True}

artifact = schema("artifact-identity", "ArtifactIdentity", obj(
    ["schema_version", "artifact_id", "artifact_type", "name", "provenance_status"],
    {
        "schema_version": schema_version,
        "artifact_id": string(),
        "artifact_type": string(enum=["repo", "commit", "file", "skill", "hook", "agent", "plugin", "mcp_server", "model", "dataset", "binary", "container", "package", "other"]),
        "name": string(),
        "version": string(),
        "source_uri": string(),
        "resolved_revision": string(),
        "content_digest": digest,
        "local_path": string(),
        "provenance_status": string(enum=["verified", "declared", "inferred", "unknown"]),
        "metadata": metadata,
    },
))

evidence_value = schema("evidence-value", "EvidenceValue", obj(
    ["schema_version", "value", "evidence_kind"],
    {
        "schema_version": schema_version,
        "value": {},
        "evidence_kind": string(enum=["observed", "derived", "declared", "external"]),
        "confidence": confidence,
        "source_refs": arr(string()),
        "timestamp": string(),
    },
))
evidence_value["allOf"] = [{
    "if": {"required": ["confidence"]},
    "then": {"properties": {"evidence_kind": {"const": "derived"}}},
}]

capability = schema("capability", "Capability", obj(
    ["schema_version", "capability_id", "action_family", "resource_selector", "source"],
    {
        "schema_version": schema_version,
        "capability_id": string(),
        "action_family": string(),
        "resource_selector": string(min_len=0),
        "constraints": metadata,
        "source": string(enum=["declared", "inferred", "observed"]),
        "evidence_refs": arr(string()),
        "risk_tags": arr(string(), unique=True),
    },
))

agent_event = schema("agent-event", "AgentEvent", obj(
    ["schema_version", "event_id", "session_id", "sequence", "timestamp_wall", "actor", "adapter_id", "event_type", "outcome", "enforcement_level"],
    {
        "schema_version": schema_version,
        "event_id": string(),
        "session_id": string(),
        "sequence": {"type": "integer", "minimum": 1},
        "timestamp_wall": string(),
        "timestamp_monotonic_ns": {"type": "integer", "minimum": 0},
        "actor": string(),
        "adapter_id": string(),
        "adapter_version": string(),
        "event_type": string(),
        "proposed_action": string(),
        "resource": string(min_len=0),
        "normalized_args": {},
        "decision_id": string(),
        "outcome": string(),
        "enforcement_level": string(enum=["L0", "L1", "L2", "L3"]),
        "evidence_refs": arr(string()),
        "prev_event_hash": digest,
        "event_hash": digest,
    },
))

policy_request = schema("policy-request", "PolicyRequest", obj(
    ["schema_version", "request_id", "principal", "action", "resource"],
    {
        "schema_version": schema_version,
        "request_id": string(),
        "principal": string(),
        "action": string(),
        "resource": string(min_len=0),
        "context": metadata,
        "session_path_summary": arr(string()),
        "capability": ref("capability"),
        "provenance": ref("artifact-identity"),
    },
))

policy_decision = schema("policy-decision", "PolicyDecision", obj(
    ["schema_version", "decision_id", "request_id", "decision", "decision_hash", "policy_bundle_digest"],
    {
        "schema_version": schema_version,
        "decision_id": string(),
        "request_id": string(),
        "decision": string(enum=["ALLOW", "DENY", "REQUIRE_APPROVAL", "OBSERVE"]),
        "policy_ids": arr(string(), unique=True),
        "reason_codes": arr(string(), unique=True),
        "diagnostics": arr({"type": "string"}),
        "decision_hash": digest,
        "policy_bundle_digest": digest,
    },
))

finding = schema("finding", "Finding", obj(
    ["schema_version", "finding_id", "rule_id", "rule_version", "category", "severity", "title", "explanation", "remediation", "fingerprint", "status"],
    {
        "schema_version": schema_version,
        "finding_id": string(),
        "rule_id": string(),
        "rule_version": string(),
        "category": string(),
        "severity": string(enum=["info", "low", "medium", "high", "critical"]),
        "confidence": confidence,
        "title": string(),
        "explanation": string(),
        "evidence_refs": arr(string()),
        "artifact_refs": arr(string()),
        "location": {},
        "remediation": string(),
        "fingerprint": digest,
        "status": string(enum=["new", "accepted", "fixed", "suppressed"]),
    },
))

blast_radius = obj(["score", "explanation"], {
    "score": {"type": "integer", "minimum": 0},
    "components": {"type": "object", "additionalProperties": {"type": "integer", "minimum": 0}},
    "explanation": string(),
})

patch_impact = schema("patch-impact", "PatchImpact", obj(
    ["schema_version", "base", "head", "blast_radius"],
    {
        "schema_version": schema_version,
        "base": string(),
        "head": string(),
        "changed_files": arr(string()),
        "changed_symbols": arr(string()),
        "affected_modules": arr(string()),
        "dependency_edges": arr(string()),
        "sensitive_surfaces": arr(string(enum=["auth", "crypto", "secret", "db", "migration", "concurrency", "network", "public_api", "serialization", "config", "build", "deployment"]), unique=True),
        "blast_radius": blast_radius,
        "analysis_confidence": {"type": "object", "additionalProperties": confidence},
        "evidence_refs": arr(string()),
    },
))

test_evidence = schema("test-evidence", "TestEvidence", obj(
    ["schema_version", "command", "tool", "exit_status", "duration_ms", "environment_fingerprint", "observed"],
    {
        "schema_version": schema_version,
        "command": string(),
        "tool": string(),
        "tool_version": string(),
        "test_ids": arr(string()),
        "suites": arr(string()),
        "exit_status": {"type": "integer"},
        "duration_ms": {"type": "integer", "minimum": 0},
        "environment_fingerprint": digest,
        "coverage_refs": arr(string()),
        "changed_code_mapping": {"type": "object", "additionalProperties": arr(string())},
        "observed": {"type": "boolean"},
        "claimed_result": string(),
        "artifact_hashes": {"type": "object", "additionalProperties": digest},
    },
))

provenance_edge = schema("provenance-edge", "ProvenanceEdge", obj(
    ["schema_version", "from_artifact_id", "relation", "to_artifact_id", "evidence_kind", "source", "verified"],
    {
        "schema_version": schema_version,
        "from_artifact_id": string(),
        "relation": string(enum=["includes", "loads", "built_from", "derived_from", "trained_on", "fine_tuned_from", "quantized_from", "invokes", "produced_by", "verified_by", "other"]),
        "to_artifact_id": string(),
        "evidence_kind": string(enum=["observed", "derived", "declared", "external"]),
        "source": string(),
        "verified": {"type": "boolean"},
        "confidence": confidence,
    },
))

trust_diff_change = obj(["change_type", "severity", "explanation"], {
    "change_type": string(enum=["COMPONENT_ADDED", "COMPONENT_REMOVED", "COMPONENT_CHANGED", "SOURCE_REF_DRIFT", "HASH_DRIFT", "TOOL_SCHEMA_DRIFT", "CAPABILITY_ADDED", "CAPABILITY_REMOVED", "CAPABILITY_EXPANDED", "CAPABILITY_REDUCED", "DECLARED_INFERRED_MISMATCH", "DECLARED_OBSERVED_MISMATCH", "POLICY_CHANGED", "ENFORCEMENT_COVERAGE_CHANGED", "SECRET_SURFACE_CHANGED", "NETWORK_SURFACE_CHANGED", "PATCH_SCOPE_CHANGED", "TEST_EVIDENCE_CHANGED"]),
    "severity": string(enum=["info", "low", "medium", "high", "critical"]),
    "artifact_id": string(),
    "capability_id": string(),
    "before": {},
    "after": {},
    "evidence_refs": arr(string()),
    "explanation": string(),
})

trust_diff = schema("trust-diff", "TrustDiff", obj(
    ["schema_version", "baseline_name", "baseline_digest", "current_digest", "changes"],
    {
        "schema_version": schema_version,
        "baseline_name": string(),
        "baseline_digest": digest,
        "current_digest": digest,
        "changes": arr(trust_diff_change),
    },
))

coverage_metric = obj(["covered", "total"], {
    "covered": {"type": "integer", "minimum": 0},
    "total": {"type": "integer", "minimum": 0},
})
risk_component = obj(["component_id", "value", "weight_milli", "rationale"], {
    "component_id": string(),
    "value": {"type": "integer"},
    "weight_milli": {"type": "integer"},
    "rationale": string(),
    "evidence_refs": arr(string()),
})
risk_score = obj(["formula", "total", "components"], {
    "formula": string(),
    "total": {"type": "integer"},
    "components": arr(risk_component),
})

trust_report = schema("trust-report", "TrustReport", obj(
    ["schema_version", "scope"],
    {
        "schema_version": schema_version,
        "scope": {},
        "inventory_summary": {"type": "object", "additionalProperties": {"type": "integer", "minimum": 0}},
        "findings": arr(ref("finding")),
        "capabilities": arr(ref("capability")),
        "declared_vs_observed_drift": arr(trust_diff_change),
        "policy_decisions": arr(ref("policy-decision")),
        "enforcement_coverage": {"type": "object", "additionalProperties": string(enum=["L0", "L1", "L2", "L3"])},
        "provenance_coverage": {"type": "object", "additionalProperties": coverage_metric},
        "patch_impact": ref("patch-impact"),
        "test_evidence": arr(ref("test-evidence")),
        "residual_risks": arr(string()),
        "score_card": risk_score,
    },
))

bundle_entry = obj(["path", "sha256", "size_bytes"], {
    "path": {
        "type": "string",
        "minLength": 1,
        # Portable relative POSIX archive path. Reject Windows drive/ADS syntax,
        # backslashes, duplicate separators, absolute paths, and dot segments.
        "pattern": r"^[^/\\:]+(?:/[^/\\:]+)*$",
        "not": {"pattern": r"(^|/)\.{1,2}(/|$)"},
    },
    "sha256": digest,
    "size_bytes": {"type": "integer", "minimum": 0, "maximum": 268435456},
    "media_type": string(),
})
bundle_manifest = schema("bundle-manifest", "BundleManifest", obj(
    ["schema_version", "bundle_version", "session_id", "created_at", "canonicalization", "entries"],
    {
        "schema_version": schema_version,
        "bundle_version": string(),
        "session_id": string(),
        "created_at": string(),
        "canonicalization": string(),
        "entries": {**arr(bundle_entry), "maxItems": 10000},
        "attestation_refs": arr(string()),
    },
))

baseline_snapshot = schema("baseline-snapshot", "BaselineSnapshot", obj(
    ["schema_version", "name", "created_at"],
    {
        "schema_version": schema_version,
        "name": string(),
        "created_at": string(),
        "digest": digest,
        "artifacts": arr(ref("artifact-identity")),
        "capabilities": arr(ref("capability")),
        "policy_digest": digest,
        "enforcement_coverage": {"type": "object", "additionalProperties": string(enum=["L0", "L1", "L2", "L3"])},
    },
))

fixture_case = schema("fixture-case", "FixtureCase", obj(
    ["schema_version", "fixture_id", "category", "description", "input", "expect"],
    {
        "schema_version": schema_version,
        "fixture_id": string(),
        "category": string(enum=["safe", "malicious", "drift", "edge", "security", "patch", "provenance", "runtime"]),
        "description": string(),
        "input": {},
        "expect": obj([], {
            "change_types": arr(string()),
            "reason_codes": arr(string()),
            "invariants": arr(string()),
            "notes": arr(string()),
        }),
    },
))

SCHEMA_DOCS = {
    "artifact-identity": artifact,
    "evidence-value": evidence_value,
    "capability": capability,
    "agent-event": agent_event,
    "policy-request": policy_request,
    "policy-decision": policy_decision,
    "finding": finding,
    "patch-impact": patch_impact,
    "test-evidence": test_evidence,
    "provenance-edge": provenance_edge,
    "trust-report": trust_report,
    "bundle-manifest": bundle_manifest,
    "baseline-snapshot": baseline_snapshot,
    "trust-diff": trust_diff,
    "fixture-case": fixture_case,
}

H = "a" * 64
H2 = "b" * 64
H3 = "c" * 64

EXAMPLES = {
    "artifact-identity": {"schema_version": "1.0.0", "artifact_id": "skill:review", "artifact_type": "skill", "name": "review", "source_uri": "https://example.invalid/repo", "resolved_revision": "abc123", "content_digest": "sha256:" + H, "provenance_status": "verified", "metadata": {"active": True}},
    "evidence-value": {"schema_version": "1.0.0", "value": "network.connect", "evidence_kind": "derived", "confidence": 0.9, "source_refs": ["file:.agent/skill.md"]},
    "capability": {"schema_version": "1.0.0", "capability_id": "network.connect", "action_family": "network.connect", "resource_selector": "github.com:443", "constraints": {"tls": True}, "source": "inferred", "evidence_refs": ["artifact:skill:review"], "risk_tags": ["network"]},
    "agent-event": {"schema_version": "1.0.0", "event_id": "evt-1", "session_id": "sess-1", "sequence": 1, "timestamp_wall": "2026-09-10T00:00:00Z", "actor": "agent:test", "adapter_id": "mcp", "event_type": "mcp.tools/call", "proposed_action": "mcp.call", "resource": "tool:read", "outcome": "allowed", "enforcement_level": "L1"},
    "policy-request": {"schema_version": "1.0.0", "request_id": "req-1", "principal": "agent:test", "action": "fs.read", "resource": "workspace/src/**", "context": {"interactive": False}},
    "policy-decision": {"schema_version": "1.0.0", "decision_id": "dec-1", "request_id": "req-1", "decision": "ALLOW", "policy_ids": ["safe-local-read"], "reason_codes": [], "diagnostics": [], "decision_hash": H, "policy_bundle_digest": H2},
    "finding": {"schema_version": "1.0.0", "finding_id": "finding-1", "rule_id": "source.unpinned", "rule_version": "1", "category": "provenance", "severity": "high", "title": "Unpinned source", "explanation": "Source has no immutable revision.", "remediation": "Pin an immutable commit or digest.", "fingerprint": H, "status": "new"},
    "patch-impact": {"schema_version": "1.0.0", "base": "origin/main", "head": "HEAD", "changed_files": ["src/auth.rs"], "sensitive_surfaces": ["auth"], "blast_radius": {"score": 40, "components": {"auth": 40}, "explanation": "Authentication code changed."}, "analysis_confidence": {"path_classifier": 1.0}},
    "test-evidence": {"schema_version": "1.0.0", "command": "cargo test auth", "tool": "cargo", "test_ids": ["auth::login"], "exit_status": 0, "duration_ms": 123, "environment_fingerprint": H, "observed": True, "artifact_hashes": {"stdout": H2}},
    "provenance-edge": {"schema_version": "1.0.0", "from_artifact_id": "agent:test", "relation": "loads", "to_artifact_id": "skill:review", "evidence_kind": "observed", "source": "runtime:mcp", "verified": True},
    "trust-report": {"schema_version": "1.0.0", "scope": {"workspace": "fixture"}, "inventory_summary": {"skill": 1}, "findings": [], "capabilities": [], "policy_decisions": [], "enforcement_coverage": {"mcp": "L1"}, "provenance_coverage": {"artifacts": {"covered": 1, "total": 1}}, "residual_risks": ["OS process isolation not enabled"]},
    "bundle-manifest": {"schema_version": "1.0.0", "bundle_version": "1", "session_id": "sess-1", "created_at": "2026-09-10T00:00:00Z", "canonicalization": "proofdrift-json-v1", "entries": [{"path": "events.jsonl", "sha256": H, "size_bytes": 42}]},
    "baseline-snapshot": {"schema_version": "1.0.0", "name": "trusted-main", "created_at": "2026-09-10T00:00:00Z", "artifacts": [], "capabilities": [], "policy_digest": H, "enforcement_coverage": {"mcp": "L1"}},
    "trust-diff": {"schema_version": "1.0.0", "baseline_name": "trusted-main", "baseline_digest": H, "current_digest": H2, "changes": [{"change_type": "CAPABILITY_EXPANDED", "severity": "high", "capability_id": "network.connect", "before": "github.com:443", "after": "**", "explanation": "Network scope expanded."}]},
    "fixture-case": {"schema_version": "1.0.0", "fixture_id": "safe-minimal", "category": "safe", "description": "Minimal safe project fixture.", "input": {"files": ["README.md"]}, "expect": {"invariants": ["passive_discovery_no_process_launch"]}},
}

INVALID_EXAMPLES = {
    "artifact-identity.missing-id": ("artifact-identity", {"schema_version": "1.0.0", "artifact_type": "file", "name": "x", "provenance_status": "unknown"}),
    "artifact-identity.bad-version": ("artifact-identity", {**EXAMPLES["artifact-identity"], "schema_version": "1.0"}),
    "evidence-value.observed-confidence": ("evidence-value", {**EXAMPLES["evidence-value"], "evidence_kind": "observed", "confidence": 0.9}),
    "capability.bad-source": ("capability", {**EXAMPLES["capability"], "source": "guessed"}),
    "agent-event.zero-sequence": ("agent-event", {**EXAMPLES["agent-event"], "sequence": 0}),
    "policy-decision.bad-decision": ("policy-decision", {**EXAMPLES["policy-decision"], "decision": "MAYBE"}),
    "finding.bad-severity": ("finding", {**EXAMPLES["finding"], "severity": "urgent"}),
    "bundle-manifest.path-traversal": ("bundle-manifest", {**EXAMPLES["bundle-manifest"], "entries": [{"path": "../secret.txt", "sha256": H, "size_bytes": 1}]}),
    "bundle-manifest.absolute-path": ("bundle-manifest", {**EXAMPLES["bundle-manifest"], "entries": [{"path": "C:\\secret.txt", "sha256": H, "size_bytes": 1}]}),
    "bundle-manifest.drive-relative": ("bundle-manifest", {**EXAMPLES["bundle-manifest"], "entries": [{"path": "C:secret.txt", "sha256": H, "size_bytes": 1}]}),
    "bundle-manifest.backslash-path": ("bundle-manifest", {**EXAMPLES["bundle-manifest"], "entries": [{"path": "dir\\events.jsonl", "sha256": H, "size_bytes": 1}]}),
    "bundle-manifest.dot-segment": ("bundle-manifest", {**EXAMPLES["bundle-manifest"], "entries": [{"path": "dir/./events.jsonl", "sha256": H, "size_bytes": 1}]}),
    "bundle-manifest.empty-segment": ("bundle-manifest", {**EXAMPLES["bundle-manifest"], "entries": [{"path": "dir//events.jsonl", "sha256": H, "size_bytes": 1}]}),
    "bundle-manifest.ads-colon": ("bundle-manifest", {**EXAMPLES["bundle-manifest"], "entries": [{"path": "events.jsonl:stream", "sha256": H, "size_bytes": 1}]}),
    "bundle-manifest.oversize-entry": ("bundle-manifest", {**EXAMPLES["bundle-manifest"], "entries": [{"path": "huge.bin", "sha256": H, "size_bytes": 268435457}]}),
    "trust-diff.bad-change-type": ("trust-diff", {**EXAMPLES["trust-diff"], "changes": [{"change_type": "MAGIC_SCORE_CHANGED", "severity": "high", "explanation": "invalid"}]}),
}

FIXTURE_DATA = [
    ("safe-minimal-agent", "safe", {"component": "skill", "capability": "fs.read"}, {"invariants": ["no_high_findings"]}),
    ("malicious-skill-instruction", "malicious", {"instruction": "attempt hidden shell setup"}, {"reason_codes": ["capability.undeclared"]}),
    ("unpinned-mcp", "provenance", {"source": "git+https://example.invalid/server.git@main"}, {"reason_codes": ["provenance.unverified"]}),
    ("overbroad-shell-grant", "security", {"capability": "process.exec", "resource": "**"}, {"invariants": ["finding_has_evidence"]}),
    ("path-traversal", "security", {"path": "../../outside"}, {"invariants": ["reject_outside_root"]}),
    ("symlink-escape", "security", {"path": "workspace/link/outside"}, {"invariants": ["resolve_before_enforce"]}),
    ("secret-egress-attempt", "security", {"payload": "<synthetic-secret-marker>"}, {"invariants": ["no_plaintext_secret_persisted"]}),
    ("git-safe-commit", "safe", {"action": "git.commit", "resource": "local"}, {"invariants": ["brokered_action_distinguished"]}),
    ("git-force-push", "runtime", {"action": "git.force_push", "resource": "origin/main"}, {"reason_codes": ["policy.explicit_deny"]}),
    ("patch-auth", "patch", {"changed_files": ["src/auth.rs"]}, {"notes": ["classify auth sensitive surface"]}),
    ("patch-db", "patch", {"changed_files": ["src/db/transaction.rs"]}, {"notes": ["classify db sensitive surface"]}),
    ("patch-concurrency", "patch", {"changed_files": ["src/runtime/locks.rs"]}, {"notes": ["classify concurrency sensitive surface"]}),
    ("bundle-valid", "safe", {"manifest_digest": H}, {"invariants": ["offline_verify_pass"]}),
    ("bundle-corrupted-byte", "security", {"manifest_digest": H, "actual_digest": H2}, {"reason_codes": ["evidence.integrity_failure"]}),
    ("provenance-missing-edge", "provenance", {"from": "agent:a", "to": "skill:b", "edge": None}, {"reason_codes": ["provenance.unverified"]}),
    ("mcp-tool-schema-drift", "drift", {"before": {"readOnlyHint": True}, "after": {"readOnlyHint": False}}, {"change_types": ["TOOL_SCHEMA_DRIFT", "CAPABILITY_EXPANDED"]}),
    ("capability-expansion", "drift", {"before": "github.com/api/**", "after": "**"}, {"change_types": ["CAPABILITY_EXPANDED"]}),
    ("capability-reduction", "drift", {"before": "**", "after": "github.com/api/**"}, {"change_types": ["CAPABILITY_REDUCED"]}),
    ("template-not-active", "edge", {"path": "docs/example/.mcp.json", "active": False}, {"invariants": ["do_not_treat_template_as_active"]}),
    ("policy-digest-changed", "drift", {"before": H, "after": H3}, {"change_types": ["POLICY_CHANGED"]}),
    ("observed-not-enforced", "runtime", {"observed": True, "enforcement_level": "L0"}, {"invariants": ["never_label_observed_as_isolated"]}),
    ("approval-replay", "security", {"token_use_count": 2}, {"invariants": ["second_use_denied"]}),
    ("duplicate-event-id", "edge", {"event_ids": ["e1", "e1"]}, {"invariants": ["duplicate_event_rejected"]}),
    ("out-of-order-event", "edge", {"sequence": [1, 3]}, {"invariants": ["out_of_order_event_rejected"]}),
]


def main() -> None:
    for directory in (SCHEMAS, VALID, INVALID, FIXTURES):
        directory.mkdir(parents=True, exist_ok=True)
    for name, document in SCHEMA_DOCS.items():
        write_json(SCHEMAS / f"{name}.schema.json", document)
    for name, document in EXAMPLES.items():
        write_json(VALID / f"{name}.valid.json", document)
    for filename, (schema_name, document) in INVALID_EXAMPLES.items():
        wrapped = {"$expected_schema": schema_name, "$document": document}
        write_json(INVALID / f"{filename}.invalid.json", wrapped)
    for fixture_id, category, input_value, expect in FIXTURE_DATA:
        write_json(FIXTURES / f"{fixture_id}.json", {
            "schema_version": "1.0.0",
            "fixture_id": fixture_id,
            "category": category,
            "description": fixture_id.replace("-", " ").capitalize() + ".",
            "input": input_value,
            "expect": expect,
        })
    write_json(SCHEMAS / "index.json", {
        "schema_version": "1.0.0",
        "canonicalization": "proofdrift-json-v1",
        "schemas": sorted(f"{name}.schema.json" for name in SCHEMA_DOCS),
    })
    print(f"generated {len(SCHEMA_DOCS)} schemas, {len(EXAMPLES)} valid examples, {len(INVALID_EXAMPLES)} invalid examples, {len(FIXTURE_DATA)} fixtures")


if __name__ == "__main__":
    main()
