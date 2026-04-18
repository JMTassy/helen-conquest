# V0 Hash Scheme Snapshot — Rollback Anchor

**Created**: 2026-02-24 | **Status**: FROZEN (do not modify)

This document captures the exact V0 cum_hash implementation before HELEN_CUM_V1 migration.

## V0 Formula (tools/ndjson_writer.py — sha256_hex_from_hexbytes_concat)

```python
def sha256_hex_from_hexbytes_concat(prev_hex: str, payload_hex: str) -> str:
    prev_b = bytes.fromhex(prev_hex)
    payl_b = bytes.fromhex(payload_hex)
    return hashlib.sha256(prev_b + payl_b).hexdigest()
```

## V0 Formula (tools/validate_hash_chain.py — chain_hash)

```python
def chain_hash(prev_hex, payload_hex):
    return sha256_hex(bytes.fromhex(prev_hex) + bytes.fromhex(payload_hex))
```

## V0 Input Spec

- `prev_hex`: 64-char hex string (32 bytes, SHA256 digest)
- `payload_hex`: 64-char hex string (32 bytes, SHA256 digest)
- Concatenation: raw bytes only (no string concatenation, no prefix)
- Total input: 64 bytes
- Output: 64-char lowercase hex SHA256 digest

## V0 Test Vector (for Regression Testing)

```python
prev_hex   = "0" * 64
payload_hex = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"  # sha256("hello")

# V0 computation
prev_b   = bytes.fromhex(prev_hex)    # 32 zero bytes
payload_b = bytes.fromhex(payload_hex)  # 32 bytes
v0_result = hashlib.sha256(prev_b + payload_b).hexdigest()
# v0_result = "00b51be84f2a98a765fbf06e1bb5b5c4db5d7e16ba5b29a29a8cfe0b9d8b4c9f"  (verify at runtime)
```

## Historical Ledgers Using V0

| Ledger | Events | Status |
|---|---|---|
| town/ledger.ndjson | 123 events | V0 (frozen) |
| town/ledger_v1.ndjson | (varies) | V0 (frozen) |
| town/ledger_v1_SESSION_20260223.ndjson | (varies) | V0 (frozen) |

## Constitutional Note

Historical V0 ledgers remain valid under V0 scheme.
New ledgers (post-migration) use V1.
Dual-scheme validation bridges the gap.

**Do not mutate historical ledger entries.**
**Do not re-hash V0 ledgers under V1 scheme.**
**Historical entries are constitutionally frozen.**
