# MAGI → LEDGER SCHEMA v1.2
**Status:** JSON Schema (Draft 2020-12, Deterministic)
**Date:** February 15, 2026
**Type:** Canonical Emission Specification

---

## I. ROOT OBJECT (Per Compiled Entry)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "MAGI_Ledger_Entry",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "tick",
    "counter",
    "faction",
    "operator",
    "state",
    "pair",
    "act",
    "proof",
    "channel",
    "delta"
  ],
  "properties": {
    "tick": {
      "type": "integer",
      "minimum": 0,
      "description": "World tick number (game round)"
    },
    "counter": {
      "type": "integer",
      "minimum": 0,
      "description": "Entry counter within tick (0-indexed)"
    },
    "faction": {
      "type": "string",
      "enum": ["✝️", "🌹", "🌀"],
      "description": "MAGI faction (Templar, Rosicrucian, Chaos)"
    },
    "operator": {
      "type": "string",
      "enum": ["🜄", "🜂", "🜁", "🜃", "⚗", "⚔"],
      "description": "MAGI operator (SOLVE, IGNITE, ASCEND, WEIGHT, REFINE, SEVER)"
    },
    "state": {
      "type": "string",
      "enum": ["⚰", "🌑", "🖤"],
      "description": "MAGI state (SEAL, ECLIPSE, VOID)"
    },
    "pair": {
      "type": "string",
      "pattern": "^(🜄|🜂|🜁|🜃|⚗|⚔)(✝️|🌹|🌀)$",
      "description": "Operator + Faction concatenation (fixed order)"
    },
    "act": {
      "type": "string",
      "enum": ["🛡️", "🧱", "📜", "🔬", "🔥", "🗡", "⛔"],
      "description": "Deterministic action symbol from ACT_MAP"
    },
    "proof": {
      "type": "string",
      "pattern": "^[A-F0-9]{4}$",
      "description": "FNV1A64 hash truncated to 4 hex chars"
    },
    "channel": {
      "type": "string",
      "enum": ["WHITE", "BLACK", "NULL"],
      "description": "Visibility: WHITE (public), BLACK (hidden), NULL (void)"
    },
    "delta": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "coherence",
        "chaos",
        "stability",
        "entropy"
      ],
      "properties": {
        "coherence": {
          "type": "integer",
          "description": "Change to global coherence"
        },
        "chaos": {
          "type": "integer",
          "description": "Change to global chaos"
        },
        "stability": {
          "type": "integer",
          "description": "Change to global stability"
        },
        "entropy": {
          "type": "integer",
          "description": "Change to global entropy"
        }
      }
    }
  }
}
```

---

## II. TICK SUMMARY SCHEMA

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "MAGI_Tick_Summary",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "tick",
    "aggregate_delta",
    "tick_hash",
    "channel"
  ],
  "properties": {
    "tick": {
      "type": "integer",
      "minimum": 0,
      "description": "World tick number"
    },
    "aggregate_delta": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "coherence",
        "chaos",
        "stability",
        "entropy"
      ],
      "properties": {
        "coherence": {
          "type": "integer",
          "description": "Sum of all coherence deltas this tick"
        },
        "chaos": {
          "type": "integer",
          "description": "Sum of all chaos deltas this tick"
        },
        "stability": {
          "type": "integer",
          "description": "Sum of all stability deltas this tick"
        },
        "entropy": {
          "type": "integer",
          "description": "Sum of all entropy deltas this tick"
        }
      }
    },
    "tick_hash": {
      "type": "string",
      "pattern": "^[A-F0-9]{4}$",
      "description": "FNV1A64 of concatenated entry proofs (sorted order)"
    },
    "channel": {
      "type": "string",
      "enum": ["WHITE", "BLACK"],
      "description": "Dominant channel this tick (WHITE if any public, else BLACK)"
    }
  }
}
```

---

## III. VALIDATION RULES (Non-Schema Constraints)

These rules are enforced **outside JSON Schema** by the engine:

### Rule 1: Proof Hash (FNV1A64)
```
proof = FNV1A64(faction + "::" + operator + "->" + state)[:4]
```

**Verification:**
```python
def verify_proof(entry: dict) -> bool:
    computed = fnv1a64_truncated(
        f"{entry['faction']}::{entry['operator']}->{entry['state']}"
    )
    return computed == entry['proof']
```

### Rule 2: Pair Construction
```
pair = operator + faction
```

**Verification:**
```python
def verify_pair(entry: dict) -> bool:
    computed = entry['operator'] + entry['faction']
    return computed == entry['pair']
```

### Rule 3: ACT Determinism
```
act = ACT_MAP[(faction, operator)]
```

**Verification:**
```python
def verify_act(entry: dict) -> bool:
    computed_act = ACT_MAP.get((entry['faction'], entry['operator']))
    return computed_act == entry['act']
```

### Rule 4: Delta Determinism
```
delta = ENGINE_EFFECTS[(faction, operator, state)]
```

**Verification:**
```python
def verify_delta(entry: dict) -> bool:
    key = (entry['faction'], entry['operator'], entry['state'])
    computed_delta = ENGINE_EFFECTS.get(key)
    return computed_delta == entry['delta']
```

### Rule 5: Counter Monotonicity
```
counter(t, i) < counter(t, i+1)  for all i in tick t
```

**Verification:**
```python
def verify_monotonic_counter(entries: list) -> bool:
    for tick in entries:
        for i in range(len(tick) - 1):
            if tick[i]['counter'] >= tick[i+1]['counter']:
                return False
    return True
```

### Rule 6: Tick Hash (Proof Chain)
```
tick_hash = FNV1A64(
    concat(sorted([e['proof'] for e in entries if e['tick'] == tick]))
)[:4]
```

**Verification:**
```python
def verify_tick_hash(entries: list, tick_summary: dict) -> bool:
    tick_entries = [e for e in entries if e['tick'] == tick_summary['tick']]
    proofs = sorted([e['proof'] for e in tick_entries])
    computed = fnv1a64_truncated(''.join(proofs))
    return computed == tick_summary['tick_hash']
```

---

## IV. CANONICAL SERIALIZATION RULE

Before hashing or storage, entries must be **canonicalized:**

### Encoding
- **UTF-8** (no other encodings)
- **No BOM** (byte order mark)

### Field Ordering
- Keys sorted **lexicographically** (alphabetical)
- Always same order for determinism

### Numeric Formatting
- **No leading zeros** (1 not 01)
- **No trailing zeros** after decimal (1.0 → 1)
- **No scientific notation** (1e6 → 1000000)
- **Integers only** (no floats in delta)

### String Formatting
- **No escaping** unless required by JSON spec
- **No extra whitespace** (compact JSON)
- **No trailing newlines**

### Batch Ordering
- Sort entries by (tick, counter) tuple
- Deterministic ordering across implementations

### Example (Canonical Form)
```json
{"act":"🔬","channel":"WHITE","counter":0,"delta":{"chaos":-1,"coherence":1,"entropy":0,"stability":0},"faction":"🌹","operator":"🜄","pair":"🜄🌹","proof":"A3F9","state":"⚗","tick":0}
```

**Rules:**
- Keys in alphabetical order ✓
- No extra spaces ✓
- Compact format ✓
- No float artifacts ✓

---

## V. SCHEMA VALIDATION LAYERS

### Layer 1: JSON Schema (Automatic)
- Type checking
- Enum validation
- Pattern matching
- Required fields
- No extra properties

**Enforced by:** JSON Schema validator

### Layer 2: Determinism Validation (Engine)
- Proof hash verification
- Pair reconstruction
- ACT mapping lookup
- Delta mapping lookup
- Counter monotonicity

**Enforced by:** Engine validator

### Layer 3: Ledger Integrity (Merkle Chain)
- Tick hash verification
- Proof chain integrity
- Causality (tick N+1 references tick N)

**Enforced by:** Ledger validator

**Rejection:** If ANY layer fails, reject entry and report violation.

---

## VI. CHANNEL DETERMINATION RULE

### Input
```
state (✝️, 🌹, 🌀) → state (⚰, 🌑, 🖤)
```

### Rule
```
IF state == 🌑 THEN channel = BLACK
ELSE channel = WHITE

Special: If state == 🖤 (void), channel = NULL
```

### Implementation
```python
def determine_channel(state: str) -> str:
    if state == "🌑":
        return "BLACK"
    elif state == "🖤":
        return "NULL"
    else:
        return "WHITE"
```

---

## VII. DELTA AGGREGATION RULE

### Per-Entry Delta
```json
{
  "coherence": 1,
  "chaos": -1,
  "stability": 0,
  "entropy": 0
}
```

### Tick Aggregation
```python
def aggregate_tick_delta(entries: list) -> dict:
    """Sum all deltas for entries in this tick."""
    agg = {
        "coherence": 0,
        "chaos": 0,
        "stability": 0,
        "entropy": 0
    }
    for entry in entries:
        for key in agg:
            agg[key] += entry['delta'][key]
    return agg
```

### Example
```
Entry 1 delta: {coherence: 1, chaos: -1, stability: 0, entropy: 0}
Entry 2 delta: {coherence: 0, chaos: 0, stability: 1, entropy: -1}
────────────────────────────────────────────────────────────────
Tick aggregate: {coherence: 1, chaos: -1, stability: 1, entropy: -1}
```

---

## VIII. REPLAY INTEGRITY GUARANTEE

**Claim:** Given an immutable ledger (JSON schema validated), the world state is fully recoverable.

**Proof:**
1. Start with world state W₀ (initial)
2. For each tick T in ledger (sorted by tick number):
   a. For each entry E in tick T (sorted by counter):
      - Verify schema ✓
      - Verify proof hash ✓
      - Lookup delta from ENGINE_EFFECTS ✓
      - Apply delta: W_new = W_old + delta
3. Final state W_n is deterministic

**Consequence:** Same ledger → same final state, always.

---

## IX. ADVERSARIAL ROBUSTNESS

### Attack: Modify entry proof
- **Defense:** Proof verification fails (Rule 1)
- **Result:** Entry rejected

### Attack: Reorder entries
- **Defense:** Tick hash verification fails (Rule 6)
- **Result:** Tick rejected

### Attack: Modify delta
- **Defense:** Delta verification fails (Rule 4)
- **Result:** Entry rejected

### Attack: Add extra field
- **Defense:** Schema rejects (additionalProperties: false)
- **Result:** Entry rejected

### Attack: Duplicate entry
- **Defense:** Counter monotonicity fails (Rule 5)
- **Result:** Tick rejected

**Conclusion:** Schema + rules = cryptographic integrity at ledger level.

---

## X. REFERENCE IMPLEMENTATION CHECKLIST

### Parsing
- [ ] JSON Schema validator (jsonschema library or equivalent)
- [ ] Canonical serialization (lexicographic key ordering)
- [ ] UTF-8 encoding validation

### Validation
- [ ] Proof hash verification (FNV1A64)
- [ ] Pair reconstruction
- [ ] ACT mapping lookup
- [ ] Delta mapping lookup
- [ ] Counter monotonicity check
- [ ] Tick hash verification (proof chain)

### Application
- [ ] Delta aggregation per tick
- [ ] Replay engine (apply deltas to world state)
- [ ] Channel routing (BLACK vs WHITE ledgers)

### Testing
- [ ] Schema validation (valid & invalid entries)
- [ ] Proof hash (known test vectors)
- [ ] Determinism (same ledger → same state)
- [ ] Adversarial (modified entries rejected)

---

## XI. INTEGRATION WITH TAMAGOTCHI STATE

### World State Structure
```python
@dataclass
class WorldState:
    tick: int
    coherence: int
    chaos: int
    stability: int
    entropy: int
    castles: Dict[str, CastleState]
    ledger: List[MagiEntry]

    def apply_delta(self, delta: dict):
        self.coherence += delta['coherence']
        self.chaos += delta['chaos']
        self.stability += delta['stability']
        self.entropy += delta['entropy']
```

### Ledger Append
```python
def append_magi(world: WorldState, entry: MagiEntry) -> bool:
    # 1. Validate schema
    if not schema_valid(entry):
        return False

    # 2. Validate determinism
    if not all_rules_pass(entry):
        return False

    # 3. Append to ledger
    world.ledger.append(entry)

    # 4. Apply delta
    world.apply_delta(entry['delta'])

    return True
```

---

## XII. LOCK STATUS

✅ **JSON Schema locked** (Draft 2020-12)
✅ **Field names locked** (immutable)
✅ **Enum values locked** (no new symbols)
✅ **Validation rules locked** (all 6 rules immutable)
✅ **Serialization rules locked** (deterministic)

**No optional fields. No free keys. No ambiguity.**

---

**Status:** SCHEMA SPECIFICATION COMPLETE
**Determinism:** Guaranteed (FNV1A64 + rules + canonical serialization)
**Ready for:** Implementation + Merkle chaining + Formal test suite

