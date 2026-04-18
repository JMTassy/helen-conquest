# Payload/Meta Split: Quick Reference Card

**One-page guide for developers** | **Print this** 🖨️

---

## 1. Write a Turn Event (Python)

```python
from tools.ndjson_writer import NDJSONWriter

writer = NDJSONWriter("./town/dialogue.ndjson")

event = writer.append(
    type_="turn",
    payload={
        "turn": 1,
        "hal": {
            "verdict": "PASS",
            "reasons_codes": ["ALL_K_GATES_VERIFIED"],
            "required_fixes": [],
            "certificates": ["KTAU_OK"],
            "refs": {
                "run_id": "run-001",
                "kernel_hash": "a" * 64,
                "policy_hash": "b" * 64,
                "ledger_cum_hash": "c" * 64,
                "identity_hash": "d" * 64,
            },
            "mutations": [],
        },
        "channel_contract": "HER_HAL_V1",
    },
    meta={
        "timestamp_utc": "2026-02-23T10:30:00Z",
        "raw_text": "[HER]\n...\n\n[HAL]\n{...}",
    },
)

print(f"Event {event['seq']} written. cum_hash: {event['cum_hash'][:16]}...")
```

---

## 2. Validate Hash Chain

```bash
python3 tools/validate_hash_chain.py ./town/dialogue.ndjson
```

**Checks:**
- ✅ Every payload_hash is correct
- ✅ Every cum_hash is correct
- ✅ seq is monotonic (0,1,2,...)

---

## 3. Validate Schema

```bash
python3 tools/validate_turn_schema.py ./town/dialogue.ndjson
```

**Checks:**
- ✅ verdict ∈ {PASS, WARN, BLOCK}
- ✅ reasons_codes sorted + regex
- ✅ required_fixes sorted
- ✅ mutations rule enforced

---

## 4. Event Structure

```json
{
  "type": "turn",
  "seq": 0,
  "payload": {
    "turn": 1,
    "hal": {...},
    "channel_contract": "HER_HAL_V1"
  },
  "meta": {
    "timestamp_utc": "2026-02-23T10:30:00Z"
  },
  "payload_hash": "f498...",
  "prev_cum_hash": "0000...",
  "cum_hash": "c7c9..."
}
```

**KEY:** Only PAYLOAD is hashed. META is observational.

---

## 5. Reason Codes (DO & DON'T)

**✅ DO:**
```json
"reasons_codes": ["ALL_K_GATES_VERIFIED", "LEDGER_COHERENT"]
```

**❌ DON'T:**
```json
"reasons": ["All K-gates verified", "Ledger coherent"]
"reasons_codes": ["LEDGER_COHERENT", "ALL_K_GATES_VERIFIED"]
```

---

## 6. Timestamp Rule (DO & DON'T)

**✅ DO:**
```json
{
  "meta": {"timestamp_utc": "2026-02-23T10:30:00Z"}
}
```

**❌ DON'T:**
```json
{
  "payload": {"timestamp_utc": "2026-02-23T10:30:00Z"}
}
```

---

## 7. Determinism Test

```bash
SEED=42 python3 app.py
H1=$(tail -1 dialogue.ndjson | jq -r '.cum_hash')
rm dialogue.ndjson
SEED=42 python3 app.py
H2=$(tail -1 dialogue.ndjson | jq -r '.cum_hash')
[ "$H1" = "$H2" ] && echo "✅ DETERMINISM OK"
```

---

## 8. Common Mistakes (DON'T)

- ❌ Use prose reasons (use enumerated codes)
- ❌ Put timestamp in payload (goes in meta)
- ❌ Use floats (use strings)
- ❌ Skip validation (always validate)
- ❌ Unsorted reasons_codes (sort before append)
- ❌ Mutations + PASS verdict (use WARN/BLOCK)

---

## 9. Files You Need

**Copy to repo:**
- `tools/ndjson_writer.py`
- `tools/validate_hash_chain.py`
- `tools/validate_turn_schema.py`

**Reference:**
- `schemas/hal_reason_codes.enum.json`
- `PAYLOAD_META_WRITER_SPEC.md`

---

## 10. CI Pipeline (Pick One)

**GitHub Actions:**
```yaml
- python3 tools/validate_hash_chain.py ./town/dialogue.ndjson
- python3 tools/validate_turn_schema.py ./town/dialogue.ndjson
```

**Makefile:**
```makefile
ci:
	python3 tools/validate_hash_chain.py ./town/dialogue.ndjson
	python3 tools/validate_turn_schema.py ./town/dialogue.ndjson
```

**Bash:**
```bash
python3 tools/validate_hash_chain.py ./town/dialogue.ndjson && \
python3 tools/validate_turn_schema.py ./town/dialogue.ndjson
```

---

## 11. Troubleshooting

| Problem | Fix |
|---------|-----|
| `payload_hash mismatch` | Check payload is unchanged |
| `cum_hash mismatch` | Verify prev_cum_hash |
| `seq mismatch` | Fix seq field |
| `reasons_codes not sorted` | `sorted(codes)` before append |
| `Float forbidden` | Use strings: `"3.14"` not `3.14` |

---

## 12. Cheat Sheet

```python
# Create writer
from tools.ndjson_writer import NDJSONWriter
w = NDJSONWriter()

# Append event
w.append(type_="turn", payload={...}, meta={...})

# Validate
python3 tools/validate_hash_chain.py ./town/dialogue.ndjson
python3 tools/validate_turn_schema.py ./town/dialogue.ndjson

# Check hash
tail -1 ./town/dialogue.ndjson | jq '.cum_hash'
```

---

**Print & Tape to Monitor** 🖨️
