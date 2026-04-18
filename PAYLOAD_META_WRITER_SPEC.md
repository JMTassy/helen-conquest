# Payload/Meta Writer Specification (Minimal, Executable)

**Status:** Frozen spec (ready for implementation) | **Date:** 2026-02-22

---

## A. Record Format (NDJSON, Exact)

Every event is **one JSON line**, terminated by LF (U+000A).

**Shape:**
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
    "timestamp_utc": "2026-02-22T23:30:00.000Z"
  },
  "payload_hash": "f498e90b83a2724c...",
  "prev_cum_hash": "0000000000000000...",
  "cum_hash": "c7c9c509c2fe9d64..."
}
```

**Hard rules:**
1. One JSON object per line
2. Terminated by LF (newline character, U+000A)
3. No trailing spaces
4. JSON is valid and parseable

---

## B. Determinism (Hash Chain)

**cum_hash encoding decision (FROZEN):** Hex-decoded 32-byte concatenation

```
cum_hash = SHA256(bytes(prev_cum_hash, "hex") + bytes(payload_hash, "hex"))
```

In Python:
```python
prev_bytes = bytes.fromhex(prev_cum_hash)   # 32 bytes
payload_bytes = bytes.fromhex(payload_hash)  # 32 bytes
cum_hash = hashlib.sha256(prev_bytes + payload_bytes).hexdigest()
```

This avoids ASCII-level ambiguities and is the standard approach.

**Genesis (seq=0):**
```
prev_cum_hash = "0" * 64  # all zeros
payload_hash = <computed from first payload>
cum_hash = SHA256(zeros_32 || payload_hash_32)
```

---

## C. Canonical Encoding (Executable Definition)

**Canon(payload)** produces stable bytes:

```python
def canon(obj: Dict) -> str:
    return json.dumps(
        obj,
        separators=(",", ":"),      # compact: no spaces
        sort_keys=True,             # keys in lexicographic order
        ensure_ascii=False,         # UTF-8, not \uXXXX escapes
    )

payload_hash = hashlib.sha256(canon(payload).encode("utf-8")).hexdigest()
```

**Invariant:** Same payload object → Same canon(payload) → Same payload_hash.

**Types in payload:**
- Only: `null`, `bool`, `int`, `str`, `list`, `dict`
- **NO floats** (store as strings if decimals needed)
- **NO timestamps** (move to meta)
- **NO random IDs** (pre-generate or derive)

---

## D. Writer Implementation (40 lines, Python)

```python
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional

class DialogueWriter:
    def __init__(self, path: str = "./town/dialogue.ndjson"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.seq = 0
        self.prev_cum_hash = "0" * 64  # genesis
        # Load existing to find last seq + cum_hash
        if self.path.exists():
            lines = self.path.read_text().strip().split("\n")
            if lines and lines[-1].strip():
                last = json.loads(lines[-1])
                self.seq = last.get("seq", 0) + 1
                self.prev_cum_hash = last.get("cum_hash", self.prev_cum_hash)

    def canon(self, obj: Dict[str, Any]) -> str:
        """Canonical JSON (sorted keys, compact)."""
        return json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False)

    def append(self, type_: str, payload: Dict[str, Any], meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Append event to dialogue log.

        Args:
            type_: "turn", "milestone", "seal"
            payload: Hash-bound deterministic fields
            meta: Observational fields (timestamp, notes, etc.)

        Returns:
            Full event object (for testing/inspection)
        """
        # Compute payload_hash
        payload_hash = hashlib.sha256(self.canon(payload).encode("utf-8")).hexdigest()

        # Compute cum_hash (hex-decoded concatenation)
        prev_bytes = bytes.fromhex(self.prev_cum_hash)
        payload_bytes = bytes.fromhex(payload_hash)
        cum_hash = hashlib.sha256(prev_bytes + payload_bytes).hexdigest()

        # Build event
        event = {
            "type": type_,
            "seq": self.seq,
            "payload": payload,
            "meta": meta or {},
            "payload_hash": payload_hash,
            "prev_cum_hash": self.prev_cum_hash,
            "cum_hash": cum_hash,
        }

        # Write to file (NDJSON)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(self.canon(event) + "\n")

        # Update state for next call
        self.seq += 1
        self.prev_cum_hash = cum_hash

        return event
```

**Usage:**
```python
writer = DialogueWriter()

# Turn 1
writer.append(
    type_="turn",
    payload={
        "turn": 1,
        "hal": {
            "verdict": "PASS",
            "reasons_codes": ["ALL_K_GATES_VERIFIED"],
            "required_fixes": [],
            "certificates": ["KTAU_OK"],
            "refs": {...},
            "mutations": [],
        },
        "channel_contract": "HER_HAL_V1",
    },
    meta={
        "timestamp_utc": "2026-02-22T23:30:00.000Z",
        "raw_text": "[HER]\n...\n\n[HAL]\n{...}",
    },
)
```

---

## E. Turn Event Payload (Contract)

```python
{
    "turn": int,                                      # Turn number (1, 2, 3, ...)
    "hal": {                                          # HAL_VERDICT_V1
        "verdict": "PASS" | "WARN" | "BLOCK",
        "reasons_codes": ["CODE1", "CODE2"],         # sorted, regex ^[A-Z0-9_]{3,64}$
        "required_fixes": ["FIX1", "FIX2"],          # sorted
        "certificates": ["CERT1", "CERT2"],         # empty or populated
        "refs": {
            "run_id": str,                            # ≥ 1 char
            "kernel_hash": str,                       # HEX 64 chars
            "policy_hash": str,                       # HEX 64 chars
            "ledger_cum_hash": str,                   # HEX 64 chars
            "identity_hash": str,                     # HEX 64 chars
        },
        "mutations": [...]                           # empty if verdict==PASS
    },
    "channel_contract": "HER_HAL_V1",               # version stamp
}
```

**Invariants:**
- `reasons_codes` and `required_fixes` **must be sorted lexicographically**
- If `mutations` non-empty → verdict must be WARN or BLOCK (never PASS)
- All hex hashes must be exactly 64 lowercase hex chars

---

## F. Migration Path (Old → New)

**Old format:**
```json
{"type":"turn","turn":1,"text":"[HER]\n...\n\n[HAL]\n{...}","hal_parsed":{...},"timestamp_utc":"2026-02-22T23:30:00Z"}
```

**Migration tool:**
```python
def migrate_old_to_new(old_event: Dict) -> Dict:
    """Convert old format to canonical format."""
    new_event = {
        "type": "turn",
        "payload": {
            "turn": old_event["turn"],
            "hal": old_event["hal_parsed"],
            "channel_contract": "HER_HAL_V1",
        },
        "meta": {
            "timestamp_utc": old_event.get("timestamp_utc", ""),
            "raw_text": old_event.get("text", ""),
        },
    }
    return new_event
```

**Migration steps:**
1. Read old dialogue.ndjson line by line
2. Parse each old event
3. Convert using migration tool
4. Create new DialogueWriter
5. For each migrated event, call `writer.append(type_="turn", payload=new["payload"], meta=new["meta"])`
6. This recomputes hash chain from genesis

**Result:** Old data becomes reproducible and provable.

---

## G. Version Stamps (Prevent Semantic Drift)

Add to every payload (encoded once, frozen):

```python
{
    "turn": 1,
    "hal": {...},
    "channel_contract": "HER_HAL_V1",  # ← This stamps HAL schema version
    "format_version": "TURN_V1",       # ← This stamps turn payload version
}
```

**Semantics:**
- If format changes, increment version (e.g., TURN_V2)
- Validators check version; unknown versions fail
- Prevents "same bytes, different meaning" confusion

**Alternative (cleaner):** Omit `format_version` if `channel_contract` + HAL schema version are sufficient.

---

## H. Validators (Minimal, Executable)

### H1. Hash Chain Validator

```python
def validate_hash_chain(path: str) -> List[str]:
    """Validate cum_hash chain integrity."""
    errors = []
    prev_cum_hash = "0" * 64
    seq = 0

    for line_num, line in enumerate(Path(path).read_text().split("\n")):
        if not line.strip():
            continue

        event = json.loads(line)

        # Check seq
        if event.get("seq") != seq:
            errors.append(f"Line {line_num}: seq mismatch. Expected {seq}, got {event.get('seq')}")

        # Check prev_cum_hash
        if event.get("prev_cum_hash") != prev_cum_hash:
            errors.append(f"Line {line_num}: prev_cum_hash mismatch")

        # Recompute payload_hash
        payload_str = json.dumps(event["payload"], separators=(",", ":"), sort_keys=True, ensure_ascii=False)
        expected_payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
        if event.get("payload_hash") != expected_payload_hash:
            errors.append(f"Line {line_num}: payload_hash mismatch")

        # Recompute cum_hash
        prev_bytes = bytes.fromhex(prev_cum_hash)
        payload_bytes = bytes.fromhex(expected_payload_hash)
        expected_cum_hash = hashlib.sha256(prev_bytes + payload_bytes).hexdigest()
        if event.get("cum_hash") != expected_cum_hash:
            errors.append(f"Line {line_num}: cum_hash mismatch")

        seq += 1
        prev_cum_hash = event.get("cum_hash")

    return errors
```

### H2. Schema Validator (Turn Events)

```python
def validate_turn_schema(payload: Dict) -> List[str]:
    """Validate turn event payload."""
    errors = []

    if payload.get("turn") is None:
        errors.append("turn: missing")
    if payload.get("channel_contract") != "HER_HAL_V1":
        errors.append(f"channel_contract: expected HER_HAL_V1, got {payload.get('channel_contract')}")

    hal = payload.get("hal", {})
    if hal.get("verdict") not in ["PASS", "WARN", "BLOCK"]:
        errors.append(f"hal.verdict: invalid {hal.get('verdict')}")

    # Check sorting
    codes = hal.get("reasons_codes", [])
    if codes != sorted(codes):
        errors.append(f"hal.reasons_codes: not sorted. Got {codes}")

    fixes = hal.get("required_fixes", [])
    if fixes != sorted(fixes):
        errors.append(f"hal.required_fixes: not sorted. Got {fixes}")

    # Check mutation rule
    if len(hal.get("mutations", [])) > 0 and hal.get("verdict") == "PASS":
        errors.append("hal: mutations present but verdict is PASS")

    return errors
```

---

## I. Implementation Order (Concrete, Non-negotiable)

1. **Implement DialogueWriter (40 lines)** — payload/meta split + hash chain
   - File: `tools/dialogue_writer.py`
   - Test: Write 3 turns, verify cum_hash chain

2. **Implement validate_hash_chain.py** — Fails CI if hashes wrong
   - File: `scripts/validate_hash_chain.py`
   - Test: Run on own output from step 1

3. **Implement validate_turn_schema.py** — HAL contract + sorting
   - File: `scripts/validate_turn_schema.py`
   - Test: Check sorting enforcement

4. **Create migrate_dialogue.py** — Old → New format
   - File: `scripts/migrate_dialogue.py`
   - Test: Migrate old data, revalidate

5. **Only then: Moment detector + sealing** — Build on proven substrate
   - File: `scripts/detect_her_hal_moment.py`
   - File: `scripts/seal_dialogue_run.py`

---

## J. Concrete Example (Old → New)

**Old format (one line):**
```json
{"type":"turn","turn":1,"text":"[HER]\nAll gates passed\n\n[HAL]\n{\"verdict\":\"PASS\",\"reasons\":[\"ok\"],\"required_fixes\":[],\"state_patch\":{}}","hal_parsed":{"verdict":"PASS","reasons":["ok"],"required_fixes":[],"state_patch":{}},"timestamp_utc":"2026-02-22T23:30:00Z"}
```

**New canonical format (one line, prettified here for readability):**
```json
{
  "type": "turn",
  "seq": 0,
  "payload": {
    "turn": 1,
    "channel_contract": "HER_HAL_V1",
    "hal": {
      "verdict": "PASS",
      "reasons_codes": ["ALL_K_GATES_VERIFIED"],
      "required_fixes": [],
      "certificates": [],
      "refs": {
        "identity_hash": "0000000000000000000000000000000000000000000000000000000000000000",
        "kernel_hash": "0000000000000000000000000000000000000000000000000000000000000000",
        "ledger_cum_hash": "0000000000000000000000000000000000000000000000000000000000000000",
        "policy_hash": "0000000000000000000000000000000000000000000000000000000000000000",
        "run_id": "migration-001"
      },
      "mutations": []
    }
  },
  "meta": {
    "raw_text": "[HER]\nAll gates passed\n\n[HAL]\n{...}",
    "timestamp_utc": "2026-02-22T23:30:00Z"
  },
  "payload_hash": "...",
  "prev_cum_hash": "0000000000000000000000000000000000000000000000000000000000000000",
  "cum_hash": "..."
}
```

**On disk (actual line, no pretty-printing):**
```
{"meta":{"raw_text":"[HER]\nAll gates passed...","timestamp_utc":"2026-02-22T23:30:00Z"},"payload":{"channel_contract":"HER_HAL_V1","hal":{"certificates":[],"mutations":[],"reasons_codes":["ALL_K_GATES_VERIFIED"],"required_fixes":[],"refs":{...},"verdict":"PASS"},"turn":1},"payload_hash":"aaaa...","prev_cum_hash":"0000...","cum_hash":"bbbb...","seq":0,"type":"turn"}
```

**Key differences:**
- ✅ `turn` is in payload (not top-level)
- ✅ `hal` uses `reasons_codes` (not `reasons`), sorted
- ✅ `timestamp_utc` is in meta (not payload)
- ✅ Hash fields explicit (payload_hash, cum_hash, prev_cum_hash)
- ✅ `seq` tracks order
- ✅ Payload is order-independent due to canonical JSON + sorted keys

---

## Summary (Frozen Spec)

| Item | Decision | Reason |
|------|----------|--------|
| cum_hash encoding | Hex-decoded 32B concat | Standard, no ambiguity |
| Canon method | JSON sorted keys, compact | Deterministic |
| Timestamp location | META only | Preserves determinism |
| Reason codes | Sorted, enumerated codes | Avoids prose fragility |
| Writer size | ~40 lines | Maintainable, auditable |
| Validators | Hash chain + Schema | Minimal, sufficient |
| Implementation order | Writer → Validators → Migration → Detector | Substrate-first |

**This spec is locked. Ready for implementation.**
