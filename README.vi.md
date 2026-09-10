# ProofDrift Spec

[English](README.md) | **Tiếng Việt**

[![Spec CI](https://github.com/WahuVN/proofdrift-spec/actions/workflows/ci.yml/badge.svg)](https://github.com/WahuVN/proofdrift-spec/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

`proofdrift-spec` chứa **hợp đồng dữ liệu công khai, có version và không phụ thuộc implementation** của hệ sinh thái ProofDrift. Repo này gồm JSON Schema deterministic, ví dụ positive/negative chuẩn, fixture tái sử dụng và bộ generator/validator để contract có thể được tái tạo và kiểm tra độc lập.

## Tài liệu normative

Hợp đồng normative chính thức là [SPECIFICATION.md](SPECIFICATION.md) bằng tiếng Anh. README tiếng Việt này dùng để giải thích và hướng dẫn sử dụng; khi có khác biệt diễn đạt, **SPECIFICATION.md là nguồn normative**.

Specification định nghĩa:

- ý nghĩa và field bắt buộc của các object public;
- failure behavior và fail-closed semantics;
- canonicalization/digest `proofdrift-json-v1`;
- sáu nhóm drift chuẩn;
- conformance levels;
- version negotiation và forward compatibility;
- threat model.

## Bộ contract v1

Contract hiện bao phủ:

- artifact identity;
- evidence values và evidence reference/envelope;
- capabilities;
- agent events;
- policy request/decision;
- findings/drift findings;
- patch impact;
- test evidence;
- provenance edges;
- trust reports;
- evidence bundle manifests;
- baseline snapshots;
- trust diffs và evaluation decisions.

Schema dùng JSON Schema Draft 2020-12. Field cộng thêm được phép ở nơi thiết kế cần forward compatibility, trong khi các field liên quan bảo mật vẫn bị giới hạn bằng required keys, enum, digest format, range và path rules.

## Sáu nhóm drift chuẩn

1. `provenance drift`
2. `capability drift`
3. `policy drift`
4. `runtime drift`
5. `patch-impact drift`
6. `test-proof drift`

Tên và semantics của sáu nhóm này là hợp đồng chung giữa `proofdrift`, `proofdrift-spec` và `proofdrift-bench`.

## Versioning

Mọi wire object phải có `schema_version`.

- Parser v1 phải nhận tài liệu hợp lệ dạng `1.x.y` phù hợp schema.
- Unknown additive field trong cùng major version phải được bỏ qua hoặc bảo toàn mà không đổi ý nghĩa field đã biết.
- Unsupported major version phải fail closed, không được tự đoán semantics.
- Breaking wire change cần major version mới và migration note.

## Canonicalization và digest

Profile `proofdrift-json-v1` yêu cầu JSON deterministic: object keys được sắp xếp, không có insignificant whitespace, array giữ nguyên thứ tự trừ khi contract cấp cao hơn khai báo set semantics, NaN/infinity bị từ chối, và digest là SHA-256 của canonical UTF-8 bytes sau khi bỏ chính field digest đang tính.

Mục tiêu là hai implementation độc lập có thể tính cùng digest cho cùng một object hợp lệ.

## Validate local

```sh
python -m pip install -r requirements.txt
python contracts/tools/validate_examples.py
python contracts/tools/conformance.py self-test
python contracts/tools/validate_semantics.py
python contracts/tools/validate_conformance.py
python contracts/tools/security_release_gate.py
```

## Normative semantics

`contracts/semantics.json` chứa các requirement ID ổn định dạng `PD-*-NNN` cho những vùng như:

- passive discovery;
- evidence integrity;
- approval binding;
- enforcement strength;
- policy binding;
- provenance;
- test proof;
- bundle safety;
- capability drift;
- MCP schema drift;
- nested shell;
- secret egress.

CI yêu cầu fixture trace coverage đầy đủ và kiểm tra semantic invariants.

## Conformance giữa các implementation

Repo có protocol JSONL implementation-neutral. Nó phát vector với ID opaque, không lộ expected label hay gợi ý valid/invalid trong đường dẫn.

```sh
python contracts/tools/conformance.py emit > proofdrift-conformance-vectors.jsonl
```

Implementation bên ngoài trả một dòng cho mỗi vector:

```json
{"vector_id":"vector-0123456789abcdef0123","accepted":true}
```

Sau đó chấm:

```sh
python contracts/tools/conformance.py score external-results.jsonl --require-perfect
```

Scorer ghi `suite_digest` deterministic để kết quả có thể bind với đúng vector set. CI còn dùng Ajv 8.20.0 trên Node 24 như một JSON Schema implementation độc lập; Python self-test chỉ chứng minh harness của chính repo, còn Ajv result là bằng chứng interoperability bổ sung.

## Schema identity

Schema `$id` dùng URN bất biến có version, ví dụ:

```text
urn:proofdrift:schema:1.0.0:agent-event
```

Nó không trỏ tới `main` có thể thay đổi. `contracts/schemas/index.json` lưu mapping filename → URN cho consumer.

## Tái tạo contract

```sh
python contracts/tools/generate_contracts.py
python contracts/tools/validate_examples.py
```

Generation phải deterministic. Chạy lại trên source không đổi không được tạo diff không giải thích được.

## Security release gate

Release gate kiểm các invariant quan trọng như schema/index consistency, fixture coverage, canonicalization, semantic requirements và security-sensitive negative cases. Mục đích là ngăn contract bị nới lỏng âm thầm trong một release.

## Repo liên quan

- `WahuVN/proofdrift` — executable engine/CLI/runtime.
- `WahuVN/proofdrift-bench` — adversarial corpus, drift-science benchmark và FPR/FNR gates.

## Giấy phép

Apache License 2.0. Xem [LICENSE](LICENSE).
