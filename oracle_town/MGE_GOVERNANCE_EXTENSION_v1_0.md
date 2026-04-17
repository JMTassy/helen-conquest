# MGE — MAGI Governance Extension v1.0

**Status:** Governance-grade kernel patch (deterministic, locked)
**Date:** February 15, 2026
**Type:** Constitutional ledger protocol

---

## I. Overview

**MGE v1.0** integrates MAGI (Axis 2) and Axis 4B (multi-castle) into the **governance kernel layer** by:

1. Defining deterministic **agent class registration** (version-locked enums)
2. Specifying **5 core events** (AGENT_CREATED, SIGIL_SEALED, PACT_BOUND, QUEST_ISSUED, GLYPH_SCAN)
3. Enforcing **canonical serialization** (sorted keys, no floats, ASCII-only)
4. Requiring **signature gates** (all mutating events require ed25519 signature)
5. Providing **replay verification** (same event sequence = identical kernel state)

**MGE does not:**
- Add new authority (all agents bound by K-gates)
- Allow freeform creativity (enum-only parameters)
- Introduce randomness (all operations deterministic)
- Break existing ledger schema (compatible with MAGI_LEDGER_SCHEMA_v1_2.md)

---

## II. Agent Class Enum (Locked)

```python
AGENT_CLASS ∈ {
    "KNIGHT",        # Combat, defense, enforcement
    "SCRIBE",        # Documentation, verification, auditing
    "BARD",          # Communication, narrative, morale
    "SEER",          # Observation, sensing, prediction
    "MAGI"           # Symbols, treaties, sigils
}
```

**Immutability:** Enum is version-locked per MGE version. No additions without major version bump.

---

## III. MAGI State Schema (Deterministic)

```json
{
  "agent_class": "MAGI",
  "agent_id": "hex64",
  "avatar_id": "hex64",
  "house_id": "hex64",
  "mge_version": "MGE-1",
  "state": "ACTIVE|DORMANT",
  "training_level": 0,
  "sigil_slots": 1,
  "sigil_root": "hex64",
  "cooldowns": {},
  "created_at_tick": 0,
  "signature_pubkey": "hex64"
}
```

**Rules:**
- All keys alphabetically sorted (canonical)
- No null values (omit if absent)
- Integers only (no floats)
- Timestamps as tick numbers, not wall-clock

---

## IV. Core Events (5-Event Minimal Set)

### E1: AGENT_CREATED (immutable once created)

```json
{
  "type": "AGENT_CREATED",
  "tick": 0,
  "agent_id": "hex64",
  "agent_class": "MAGI",
  "avatar_id": "hex64",
  "house_id": "hex64",
  "mge_version": "MGE-1",
  "signature": "hex128"
}
```

**Validation:**
- agent_id = SHA256("AGENT-1|" + agent_class + "|" + avatar_id + "|" + house_id)
- Signature verifies under avatar_id's seal key
- Only one AGENT_CREATED per agent_id (idempotent register)
- agent_class must be in AGENT_CLASS enum

**Reject Codes:**
- INVALID_SIGNATURE
- AGENT_CLASS_UNKNOWN
- DUPLICATE_AGENT_ID
- AVATAR_NOT_FOUND

### E2: SIGIL_SEALED (castle protection)

```json
{
  "type": "SIGIL_SEALED",
  "tick": 0,
  "agent_id": "hex64",
  "target_id": "hex64",
  "sigil_id": "ASCII_ID",
  "delta_defense": 1,
  "duration_ticks": 3,
  "terms_hash": "hex64",
  "signature": "hex128"
}
```

**Validation:**
- agent_id exists and agent_class == "MAGI"
- target_id exists (castle or territory)
- sigil_id in registered sigil root (Merkle proof)
- delta_defense is positive integer (0-10)
- duration_ticks is positive integer (1-20)
- Cooldown gate: no SIGIL_SEALED from same agent within cooldown window (3 ticks default)
- Signature valid under agent_id's seal key

**Effect:**
- Applies delta_defense to target for duration_ticks
- Emits ledger entry (immutable)
- No tokens, no economy (pure state mutation)

**Reject Codes:**
- AGENT_NOT_MAGI
- TARGET_NOT_FOUND
- SIGIL_NOT_REGISTERED
- COOLDOWN_ACTIVE
- DELTA_OOB
- DURATION_OOB
- INVALID_SIGNATURE

### E3: PACT_BOUND (treaty enforcement)

```json
{
  "type": "PACT_BOUND",
  "tick": 0,
  "agent_id": "hex64",
  "pact_id": "hex64",
  "terms_hash": "hex64",
  "counterparty_ids": ["hex64", "hex64"],
  "signature": "hex128"
}
```

**Validation:**
- agent_id exists and agent_class == "MAGI"
- pact_id = SHA256("PACT-1|" + sorted(counterparty_ids) + "|" + terms_hash)
- terms_hash corresponds to canonical terms (must be provided externally)
- All counterparty_ids exist
- Signature valid

**Effect:**
- Installs "violation counter" on each counterparty
- Auto-penalty function triggered if violation detected
- Ledger entry is immutable proof of pact

**Reject Codes:**
- AGENT_NOT_MAGI
- COUNTERPARTY_NOT_FOUND
- INVALID_TERMS_HASH
- DUPLICATE_PACT
- INVALID_SIGNATURE

### E4: QUEST_ISSUED (deterministic quest templates)

```json
{
  "type": "QUEST_ISSUED",
  "tick": 0,
  "agent_id": "hex64",
  "quest_id": "hex64",
  "template_code": "ASCII_ID",
  "terms_hash": "hex64",
  "signature": "hex128"
}
```

**Validation:**
- agent_id exists and agent_class == "MAGI"
- quest_id = SHA256("QUEST-1|" + state_root_at_tick + "|" + template_code + "|" + agent_id)
  (deterministic, anchored to world state at issue time)
- template_code in registered quest template enum
- terms_hash hash of canonical quest steps JSON
- Signature valid

**Effect:**
- Issues quest as deterministic checklist (no randomness, no "mystery outcomes")
- Quest steps are fixed per template
- Ledger entry records issue time + terms

**Reject Codes:**
- AGENT_NOT_MAGI
- TEMPLATE_NOT_REGISTERED
- INVALID_TERMS_HASH
- DUPLICATE_QUEST
- INVALID_SIGNATURE

### E5: GLYPH_SCAN_RESULT (non-mutating validation)

```json
{
  "type": "GLYPH_SCAN_RESULT",
  "tick": 0,
  "agent_id": "hex64",
  "input_hash": "hex64",
  "result": "ACCEPT|REJECT",
  "codes": ["K1_ORDER", "K2_WARN_INT"],
  "signature": "hex128"
}
```

**Validation:**
- agent_id exists and agent_class == "MAGI"
- input_hash matches input being validated (externally provided)
- result ∈ {ACCEPT, REJECT}
- codes are whitelisted lint codes
- Signature valid

**Effect:**
- **Optional ledger entry** (for audit trail, not required)
- Does not mutate state
- Used for off-chain validation with on-chain proof

**Reject Codes:**
- AGENT_NOT_MAGI
- RESULT_INVALID
- CODE_UNKNOWN
- INVALID_SIGNATURE

---

## V. Canonical Event Serialization (Strict)

All events must serialize deterministically:

```python
def canonical_event_json(event: dict) -> str:
    # 1. Sort all keys alphabetically
    sorted_evt = sort_keys_deep(event)
    
    # 2. Serialize to JSON (compact, no spaces)
    json_str = json.dumps(sorted_evt, separators=(",", ":"), sort_keys=False)
    
    # 3. Verify all keys sorted (defensive check)
    keys = list(sorted_evt.keys())
    assert keys == sorted(keys), "E_KEY_ORDER"
    
    # 4. Verify ASCII-only
    for char in json_str:
        assert ord(char) < 128, "E_NON_ASCII"
    
    # 5. No floats
    assert "." not in json_str or all(...), "E_FLOAT_FOUND"
    
    return json_str
```

---

## VI. Signature Validation (ed25519)

All mutating events require **ed25519 signatures**.

```python
def verify_event_signature(event: dict, seal_pubkey_hex64: str) -> bool:
    # 1. Remove signature field
    event_copy = {k: v for k, v in event.items() if k != "signature"}
    
    # 2. Canonical JSON
    msg_bytes = canonical_event_json(event_copy).encode("utf-8")
    
    # 3. Verify signature
    pubkey_bytes = bytes.fromhex(seal_pubkey_hex64)
    sig_bytes = bytes.fromhex(event["signature"])
    
    try:
        nacl.signing.VerifyKey(pubkey_bytes).verify(msg_bytes, sig_bytes)
        return True
    except nacl.exceptions.BadSignatureError:
        return False
```

---

## VII. Ledger Integration (Compatible with Axis 2)

MGE events append to the same ledger as Axis 2 MAGI entries.

**Ledger entry format (unified):**

```json
{
  "type": "AGENT_CREATED|SIGIL_SEALED|PACT_BOUND|QUEST_ISSUED|GLYPH_SCAN_RESULT|...",
  "tick": 0,
  "counter": 0,
  "payload": { ... },
  "proof": "hex8",
  "timestamp": "2026-02-15T12:00:00Z"
}
```

**Compatibility rules:**
- All events serialize canonically
- Tick + counter enforce total ordering
- Proof = FNV1A64(canonical_json)[:8]
- Replay verification: same event sequence → identical kernel state

---

## VIII. CI Test Gates (Minimal Suite)

### Gate 1: Canonical Format
```
Input:  MGE event (any)
Check:  JSON canonical (sorted keys, no floats, ASCII)
Reject: E_KEY_ORDER, E_FLOAT_FOUND, E_NON_ASCII
```

### Gate 2: Signature Validity
```
Input:  Event with signature field
Check:  ed25519 verify over canonical payload
Reject: INVALID_SIGNATURE
```

### Gate 3: Type & Enum Validation
```
Input:  Event.type, Event.agent_class, etc.
Check:  All enums in locked whitelist
Reject: TYPE_UNKNOWN, CLASS_UNKNOWN, RESULT_INVALID
```

### Gate 4: Determinism
```
Input:  Same event sequence twice
Check:  Identical kernel state after replay
Reject: E_DETERMINISM_VIOLATION
```

### Gate 5: Idempotence (Select Events)
```
Input:  AGENT_CREATED with same agent_id
Check:  Second is rejected or idempotent
Reject: DUPLICATE_AGENT_ID
```

---

## IX. State Reducer (Kernel Integration)

```python
def apply_mge_event(kernel_state: dict, event: dict) -> dict:
    """Apply MGE event to kernel state, return new state."""
    
    # Canonical validation (pre-check)
    canonical_event_json(event)
    
    # Type dispatch
    if event["type"] == "AGENT_CREATED":
        return apply_agent_created(kernel_state, event)
    elif event["type"] == "SIGIL_SEALED":
        return apply_sigil_sealed(kernel_state, event)
    elif event["type"] == "PACT_BOUND":
        return apply_pact_bound(kernel_state, event)
    elif event["type"] == "QUEST_ISSUED":
        return apply_quest_issued(kernel_state, event)
    elif event["type"] == "GLYPH_SCAN_RESULT":
        return apply_glyph_scan_result(kernel_state, event)
    else:
        raise KeyError(f"E_EVENT_TYPE_UNKNOWN: {event['type']}")
```

Each `apply_*` function is **pure** (no side effects, no I/O):
- Takes kernel_state + event
- Returns new_state (immutable update)
- Throws on validation failure

---

## X. Lock Status

✅ **AGENT_CLASS enum** (locked, no additions)
✅ **5 core events** (locked, no removals)
✅ **Canonical serialization** (locked, no deviations)
✅ **Signature gates** (locked, required for all mutations)
✅ **Determinism property** (locked, replay must be identical)

**MGE v1.0 is immutable once deployed.**

Future versions (MGE-2, MGE-3) may:
- Add new agent classes (breaking change)
- Add new event types (breaking change)
- Modify signature schemes (breaking change)

But MGE-1 deployments remain forever stable.

---

## XI. Minimal Example: Register MAGI Agent

**Step 1: Generate agent ID** (deterministically)
```
agent_id = SHA256("AGENT-1|MAGI|<avatar_id>|<house_id>")
```

**Step 2: Create event**
```json
{
  "type": "AGENT_CREATED",
  "agent_class": "MAGI",
  "agent_id": "<computed above>",
  "avatar_id": "<avatar_id>",
  "house_id": "<house_id>",
  "mge_version": "MGE-1",
  "signature": "<ed25519 signature over canonical JSON>",
  "tick": 0
}
```

**Step 3: Validate & append**
```python
# Verify canonical format
canonical_event_json(event)

# Verify signature
verify_event_signature(event, seal_pubkey)

# Apply to kernel
new_state = apply_agent_created(kernel_state, event)

# Append to ledger (immutable)
ledger.append(event)
```

**Step 4: Verify determinism**
```python
# Replay same event sequence
replay_state = empty_kernel_state()
for evt in ledger:
    replay_state = apply_mge_event(replay_state, evt)

# Should equal current state
assert replay_state == new_state
```

---

## XII. Upgrade Path (Future)

If you need to add capabilities:

1. **New sigil type?** → Add to `sigil_id` enum (no code change)
2. **New quest template?** → Add to `template_code` enum (no code change)
3. **New event type?** → Bump to MGE-2 (breaking change, new spec)
4. **New agent class?** → Bump to MGE-2 (breaking change)

**MGE-1 deployments are forever stable.**

---

**Status:** SPECIFICATION COMPLETE

Ready for kernel integration + Avatar Forge frontend.

