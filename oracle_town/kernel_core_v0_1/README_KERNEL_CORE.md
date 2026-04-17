# Kernel Core v0.1 (Minimal Checkable)

This folder contains the smallest executable substrate for the invariant:

**No receipt → no ship** (reduced here to a PASS/BLOCK predicate on HAL_VERDICT_V1).

## Layout
```
oracle_town/kernel_core_v0_1/
  schemas/
    event_v1.schema.json
    hal_verdict_v1.schema.json
  tools/
    canon.py
    ndjson_append.py
    validate_hash_chain.py
    validate_turn_schema.py
    kernel_reduce.py
  town/
    ledger_v1.ndjson
```

## Canon + Hash Rules
- Canonical JSON: sorted keys, no floats, separators "," ":", UTF-8
- payload_hash = SHA256(canon(payload))
- cum_hash = SHA256(prev_cum_hash || payload_hash)  (raw bytes from hex)

## Minimal Usage
```bash
# append a new event (event.json must contain payload + meta + type + seq + schema_version)
python3 oracle_town/kernel_core_v0_1/tools/ndjson_append.py \
  oracle_town/kernel_core_v0_1/town/ledger_v1.ndjson event.json

# validate chain + schema
python3 oracle_town/kernel_core_v0_1/tools/validate_hash_chain.py \
  oracle_town/kernel_core_v0_1/town/ledger_v1.ndjson
python3 oracle_town/kernel_core_v0_1/tools/validate_turn_schema.py \
  oracle_town/kernel_core_v0_1/town/ledger_v1.ndjson
```
