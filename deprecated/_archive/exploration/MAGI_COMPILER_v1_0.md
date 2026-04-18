# MAGI → LEDGER COMPILER v1.0

**Status:** Specification (Executable)
**Date:** February 15, 2026
**Axis:** 2 — Deterministic Compiler

---

## I. INPUT CONTRACT

```
MAGI_LINE := FACTION "::" OPERATOR "->" STATE
```

**Exactly 3 semantic tokens. Order is mandatory.**

### Token Sets (Locked)

**FACTION** (identity channel — exactly 1 required)
- `✝️` = VOW / WAR DISCIPLINE / HARD CONSTRAINT
- `🌹` = TRANSFORMATION / INTEGRATION / REFINEMENT
- `🌀` = VOLATILITY / ADVERSARIAL ENTROPY / STRESS

**OPERATOR** (intent — exactly 1 required)
- `🜄` = SOLVE (dissolve / open / loosen)
- `🜂` = IGNITE (intensify / escalate)
- `🜁` = ASCEND (abstract / elevate / optimize)
- `🜃` = WEIGHT (bind to cost / materialize / commit)
- `⚗` = REFINE (purify / compress / iterate)
- `⚔` = SEVER (cut / veto / isolate)

**STATE** (consequence — exactly 1 required)
- `⚰` = SEAL (irreversible / no rollback)
- `🌑` = ECLIPSE (hidden / covert / fog-of-war)
- `🖤` = VOID (null / no resource / no proof)

### Valid Examples

```
✝️ :: ⚔ -> ⚰
🌹 :: 🜄 -> ⚗
🌀 :: 🜂 -> 🌑
```

### Invalid (Rejected by Parser)

```
✝️ ⚔ ⚰              ❌ (no structure)
🌹 :: 🜄             ❌ (missing state)
🌀 -> 🌑             ❌ (missing operator)
✝️ :: 🜄 :: ⚔ -> ⚰  ❌ (double delimiter)
```

---

## II. PARSER (Strict Grammar)

```regex
^(✝️|🌹|🌀)\s::\s(🜄|🜂|🜁|🜃|⚗|⚔)\s->\s(⚰|🌑|🖤)$
```

**Rejection Rules:**
1. Unknown token
2. Improper delimiter spacing (not ` :: ` and ` -> `)
3. More than 1 FACTION
4. More than 1 OPERATOR
5. More than 1 STATE
6. Overlay atoms inside MAGI line
7. Invalid token combinations

**Return:** `(F, O, S)` tuple or REJECT

---

## III. CANONICAL FIELD EXTRACTION

Given parsed:
- `F` = FACTION
- `O` = OPERATOR
- `S` = STATE

Compiler emits **7-token WULMOJI ledger entry:**

```
(n) STATE FACTION PAIR ACT 🔗#HEX4 RIBBON
```

### Field Mapping Rules

| Ledger Field | Source | Rule |
|---|---|---|
| (n) | Counter | Entry number (auto-increment) |
| STATE | S | Direct from parsed STATE |
| FACTION | F | Direct from parsed FACTION |
| PAIR | O + F | Operator concat faction (fixed order) |
| ACT | (F, O) | Deterministic mapping table (below) |
| 🔗#HEX4 | Hash | FNV1A64(input) truncated to 4 hex |
| RIBBON | F + S | Faction concat state |

---

## IV. OPERATOR ENCODING (PAIR)

**PAIR = O ∘ F** (string concatenation, fixed order)

### Examples

| FACTION | OPERATOR | PAIR |
|---|---|---|
| `✝️` | `⚔` | `⚔✝️` |
| `🌹` | `🜄` | `🜄🌹` |
| `🌀` | `🜂` | `🜂🌀` |

**No permutation allowed. Order is immutable.**

---

## V. ACT DETERMINISTIC MAPPING

**ACT is not free text. Maps from (F, O).**

### Full Mapping Table

| FACTION | OPERATOR | ACT | Meaning |
|---|---|---|---|
| `✝️` | `⚔` | `🛡️` | Hard veto |
| `✝️` | `🜃` | `🧱` | Commit resource |
| `✝️` | `🜂` | `⚔️` | Escalate discipline |
| `✝️` | `🜄` | `📜` | Declare doctrine |
| `✝️` | `🜁` | `📈` | Elevate rule |
| `✝️` | `⚗` | `🔐` | Seal oath |
| `🌹` | `🜄` | `📜` | Open integration |
| `🌹` | `⚗` | `🔬` | Refine knowledge |
| `🌹` | `🜂` | `💡` | Intensify coherence |
| `🌹` | `🜃` | `💎` | Materialize value |
| `🌹` | `🜁` | `🎯` | Elevate vision |
| `🌹` | `⚔` | `🕊️` | Dissolve conflict |
| `🌀` | `🜂` | `🔥` | Escalate chaos |
| `🌀` | `⚔` | `🗡️` | Sever link |
| `🌀` | `🌑` | `💨` | Hide volatility |
| `🌀` | `🜃` | `⚫` | Void claim |
| `🌀` | `🜄` | `🌪️` | Dissolve into chaos |
| `🌀` | `⚗` | `♻️` | Iterate conflict |

**Fallback:** `❌` (reject if unmapped)

---

## VI. PROOF HASH (FNV1A64)

**Input string:**
```
hash_input = F + "::" + O + "->" + S
```

**Compute FNV1A64:**
```python
def fnv1a64(s: str) -> int:
    hash_val = 0xcbf29ce484222325
    for byte in s.encode('utf-8'):
        hash_val ^= byte
        hash_val = (hash_val * 0x100000001b3) & ((1 << 64) - 1)
    return hash_val

proof_hex = format(fnv1a64(hash_input), '04x')[:4]
```

**Emit:** `🔗#AB12` (where AB12 is first 4 hex chars)

---

## VII. RIBBON (Faction + State)

**RIBBON = F + S** (string concatenation)

| FACTION | STATE | RIBBON |
|---|---|---|
| `✝️` | `⚰` | `✝️⚰` |
| `🌹` | `⚗` | `🌹⚗` |
| `🌀` | `🌑` | `🌀🌑` |

---

## VIII. COMPILATION EXAMPLE

### Input
```
🌹 :: 🜄 -> ⚗
```

### Parse
```
F = 🌹 (TRANSFORMATION)
O = 🜄 (SOLVE)
S = ⚗ (REFINE)
```

### Extract Fields

| Field | Value | Rule |
|---|---|---|
| (n) | 12 | Counter |
| STATE | ⚗ | From S |
| FACTION | 🌹 | From F |
| PAIR | 🜄🌹 | O + F |
| ACT | 🔬 | Map (🌹, 🜄) |
| PROOF | 🔗#A3F9 | FNV1A64 hash |
| RIBBON | 🌹⚗ | F + S |

### Output (7-Token Ledger Entry)

```
(12) ⚗ 🌹 🜄🌹 🔬 🔗#A3F9 🌹⚗
```

**Deterministic. No free glyph stacking.**

---

## IX. BEAUCÉANT BINARY CHANNEL

**Templar inheritance: Black/White war banner**

### Channel Rule

```
IF STATE == 🌑:
    channel = BLACK
ELSE:
    channel = WHITE
```

### Rendering

| Channel | Visibility | Ledger Rendering |
|---|---|---|
| WHITE | Public | Full entry visible |
| BLACK | Hidden | Entry hidden until resolution |

**No dual-state ambiguity.**

---

## X. TAMAGOTCHI JSON EMISSION

Compiled entry also outputs structured delta:

```json
{
  "entry_number": 12,
  "faction": "🌹",
  "operator": "🜄",
  "state": "⚗",
  "pair": "🜄🌹",
  "act": "🔬",
  "proof": "A3F9",
  "ribbon": "🌹⚗",
  "channel": "WHITE",
  "effect": {
    "coherence": 1,
    "entropy": -1,
    "cost": 0
  },
  "timestamp": "2026-02-15T23:30:00Z"
}
```

**Effect mapping comes from ENGINE EFFECT TABLE (deterministic, no interpretation layer).**

---

## XI. ENGINE EFFECT TABLE

Each (F, O, S) combination maps to explicit engine delta:

### Templar (✝️) Effects

| MAGI | Engine Effect |
|---|---|
| `✝️ :: ⚔ -> ⚰` | Hard veto. Freeze action. (-1 freedom, +1 authority) |
| `✝️ :: 🜃 -> ⚰` | Commit resource irreversibly. (-cost, +1 binding) |
| `✝️ :: 🜂 -> ⚰` | Intensify discipline. Lock freedoms. (+1 order, -1 fluidity) |
| `✝️ :: 🜄 -> 📜` | Declare doctrine. (+1 doctrine, seal in ledger) |
| `✝️ :: 🜁 -> 📈` | Elevate rule. Abstraction level up. |
| `✝️ :: ⚗ -> 🔐` | Seal oath. Bind irreversibly. |

### Rosicrucian (🌹) Effects

| MAGI | Engine Effect |
|---|---|
| `🌹 :: 🜄 -> ⚗` | Research iteration. (+1 coherence, -1 chaos) |
| `🌹 :: ⚗ -> ⚰` | Refinement complete. Doctrine locked. (+1 wisdom) |
| `🌹 :: 🜂 -> 💡` | Intensify coherence. Integration boost. (+1 cohesion) |
| `🌹 :: 🜃 -> 💎` | Materialize value. Resource committed. |
| `🌹 :: 🜁 -> 🎯` | Elevate vision. Strategic abstraction. |
| `🌹 :: ⚔ -> 🕊️` | Dissolve conflict. Open channel. |

### Chaos (🌀) Effects

| MAGI | Engine Effect |
|---|---|
| `🌀 :: 🜂 -> 🌑` | Escalate under concealment. (+1 pressure, hidden) |
| `🌀 :: ⚔ -> 🖤` | Sever and void. Remove presence. (-1 resource) |
| `🌀 :: 🜄 -> 🌪️` | Dissolve into chaos. Destabilize. (+1 entropy) |
| `🌀 :: 🜃 -> ⚫` | Bind to void. Treasury wiped. (treasury → 0) |
| `🌀 :: ⚗ -> ♻️` | Iterate conflict. Perpetual pressure. |

**No symbolic emission without mechanical mapping.**

---

## XII. STRICT COMPILATION ALGORITHM

```python
def compile_magi(line: str) -> dict:
    """
    Input: MAGI line
    Output: 7-token ledger entry dict (or REJECT)
    """
    # 1. PARSE
    match = re.match(
        r'^(✝️|🌹|🌀)\s::\s(🜄|🜂|🜁|🜃|⚗|⚔)\s->\s(⚰|🌑|🖤)$',
        line
    )
    if not match:
        return {"status": "REJECT", "reason": "Invalid syntax"}

    F, O, S = match.groups()

    # 2. EXTRACT FIELDS
    PAIR = O + F
    ACT = ACT_MAP.get((F, O), "❌")

    if ACT == "❌":
        return {"status": "REJECT", "reason": f"Unmapped (F={F}, O={O})"}

    # 3. COMPUTE HASH
    hash_input = f"{F}::{O}->{S}"
    proof = format(fnv1a64(hash_input), '04x')[:4]

    # 4. BUILD RIBBON
    RIBBON = F + S

    # 5. DETERMINE CHANNEL
    channel = "BLACK" if S == "🌑" else "WHITE"

    # 6. LOOKUP ENGINE EFFECT
    effect_key = f"{F}::{O}->{S}"
    effect = ENGINE_EFFECTS.get(effect_key, {"coherence": 0, "entropy": 0})

    # 7. EMIT
    return {
        "status": "ACCEPT",
        "entry_number": None,  # Set by ledger
        "state": S,
        "faction": F,
        "pair": PAIR,
        "act": ACT,
        "proof": f"🔗#{proof}",
        "ribbon": RIBBON,
        "channel": channel,
        "effect": effect,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
```

---

## XIII. LEDGER INTEGRATION (7-TOKEN SAFE)

**Every compiled MAGI line becomes canonical WULMOJI:**

```
(n) STATE FACTION PAIR ACT 🔗#HEX4 RIBBON
```

### Ledger Append Protocol

```python
def ledger_append_magi(magi_line: str, ledger: list) -> bool:
    """
    Compile MAGI → append to ledger
    Returns: success boolean
    """
    compiled = compile_magi(magi_line)

    if compiled["status"] != "ACCEPT":
        return False

    # Assign entry number
    compiled["entry_number"] = len(ledger) + 1

    # Append
    ledger.append(compiled)

    return True
```

### Ledger Entry Format (JSON)

```json
{
  "entry_number": 12,
  "state": "⚗",
  "faction": "🌹",
  "pair": "🜄🌹",
  "act": "🔬",
  "proof": "🔗#A3F9",
  "ribbon": "🌹⚗",
  "channel": "WHITE",
  "effect": {
    "coherence": 1,
    "entropy": -1
  },
  "timestamp": "2026-02-15T23:30:00Z"
}
```

---

## XIV. DETERMINISM GUARANTEE

**For same input (MAGI line):**
- Same ledger entry ✅
- Same hash ✅
- Same channel ✅
- Same effect delta ✅
- Replay safe ✅

**No randomness in compilation.**

---

## XV. CONFLICT RESOLUTION (Multi-MAGI Same Tick)

### Rule: APPLY IN ORDER

If multiple MAGI lines submitted same tick:

```
Input:
  ✝️ :: ⚔ -> ⚰
  🌹 :: 🜄 -> ⚗
  🌀 :: 🜂 -> 🌑

Processing:
  1. Parse all (reject any invalid)
  2. Compile in submission order
  3. Apply effects sequentially
  4. Append to ledger in order
```

### Collision Rule (Same Target)

If two MAGI target same resource:

```
✝️ :: ⚔ -> ⚰  (hard veto)
🌹 :: 🜄 -> ⚗  (integration)
```

**Templar (✝️) veto overrides all others. ✝️ acts first.**

---

## XVI. VALIDATION GATES

Before ledger append:

1. **K0: Syntax** — Valid MAGI grammar
2. **K1: Mapping** — (F, O) exists in ACT_MAP
3. **K2: Determinism** — Same input → same output
4. **K5: Channel** — S determines BLACK/WHITE
5. **K7: Effect** — (F, O, S) has engine mapping

**Reject if any gate fails.**

---

## XVII. 10 CANONICAL SPELL-LINES

### 1. BUILD
```
🌹 :: 🜃 -> ⚗
Bind resources → refine structure
Effect: +1 coherence, -1 entropy
```

### 2. FORTIFY
```
✝️ :: 🜃 -> ⚰
Commit stone and oath. Irreversible defense.
Effect: +1 binding, +1 authority
```

### 3. DIPLOMACY
```
🌹 :: 🜄 -> ⚗
Open → integrate → purify relations
Effect: +1 coherence, -1 entropy
```

### 4. SANCTION
```
✝️ :: ⚔ -> ⚰
Cut channel. Seal dispute.
Effect: Hard veto, +1 authority
```

### 5. RESEARCH
```
🌹 :: ⚗ -> ⚰
Refinement complete. Doctrine locked.
Effect: +1 wisdom
```

### 6. SABOTAGE (Adversary)
```
🌀 :: 🜂 -> 🌑
Escalate under concealment
Effect: +1 pressure (hidden)
```

### 7. RESOURCE COLLAPSE
```
🌀 :: 🜃 -> 🖤
Bind to void. Treasury wiped.
Effect: treasury → 0
```

### 8. MARTIAL LAW
```
✝️ :: 🜂 -> ⚰
Intensify discipline. Lock freedoms.
Effect: +1 order, -1 fluidity
```

### 9. REFORMATION
```
🌹 :: 🜄 -> ⚰
Dissolve corruption. Seal new charter.
Effect: +1 coherence
```

### 10. EXILE
```
✝️ :: ⚔ -> 🖤
Cut actor. Remove presence.
Effect: -1 resource
```

---

## XVIII. INTEGRATION POINTS

### With WULMOJI Ledger
- 7-token format matches exactly
- Proof hash integrates with ledger chain
- Channel (BLACK/WHITE) integrates with Beaucéant

### With Tamagotchi JSON State
- Effect dict maps directly to state mutations
- Entry number auto-increments with game rounds
- Timestamp syncs with game clock

### With CONQUEST Game Engine
- ACT determines game action outcome
- FACTION determines who acts (player faction)
- EFFECT mutates game state deterministically

---

## XIX. LOCK STATUS

✅ **Grammar locked** (strict regex)
✅ **Tokens locked** (3 sets, defined)
✅ **Mapping locked** (ACT_MAP immutable)
✅ **Hash locked** (FNV1A64 standard)
✅ **Channel locked** (BLACK/WHITE binary)
✅ **Effect locked** (deterministic table)

**No drift. No leakage.**

---

## XX. REFERENCE IMPLEMENTATION CHECKLIST

- [ ] Parser (regex + token validation)
- [ ] ACT_MAP (complete mapping table)
- [ ] ENGINE_EFFECTS (all 13+ effects)
- [ ] FNV1A64 hash function
- [ ] Ledger append protocol
- [ ] JSON emission
- [ ] Beaucéant channel routing
- [ ] Conflict resolution (multi-MAGI ordering)
- [ ] Validation gates (K0, K1, K2, K5, K7)
- [ ] Test suite (syntax, mapping, determinism)

---

**Status:** SPECIFICATION COMPLETE
**Executable:** Ready for implementation
**Determinism:** Guaranteed (FNV1A64 + deterministic tables)
**Safe:** No free glyphs, no interpretation, pure mapping

