---
authority: NON_SOVEREIGN
canon: NO_SHIP
lifecycle: DRAFT_SPEC
source: TEMPLE_200_WUL
transmutation_request: TRANS_WUL_P1_VALIDATOR_001
---

# WUL Packet Spec v0.1

Compile-time specification for WUL (WULmoji) inter-agent packets.
Implemented by `src/wul_packet_validator.py`.

---

## Packet format

```
[KEY::VALUE][KEY::VALUE]...[WUL::<glyphs>]
```

All fields use `[KEY::VALUE]` syntax. Order is not significant for validation.
The `WUL` field is always last by convention and carries the compressed glyph summary.

---

## Tiers

| Tier | Required fields | When |
|---|---|---|
| ACK | ROLE · WUL | receipt of transmission only |
| PRODUCTION | ROLE · INTENT · CONF · IMPACT · TASK · TRACE · DIALECT · WUL | standard inter-agent work |
| KERNEL_ADJACENT | all PRODUCTION + PERM · ESCALATE | any kernel-proximity action |

Tier is auto-detected from fields present. Caller may override via explicit `tier` argument.

---

## Canonical field values

### ROLE
`AURA · HER · DAN · HAL · MAYOR · TEMPLE · OPERATOR`

### INTENT
`INFORM · PROPOSE · REQUEST · VERIFY · HANDOFF · ESCALATE · ARCHIVE · REJECT · ACK · EXPLORE`

### IMPACT
`LOCAL · MULTI_AGENT · KERNEL_ADJACENT · SOVEREIGN_ADJACENT`

### DIALECT
`TEMPLE · MAYOR · HAL · DAN · KERNEL_SAFE · CROWD · UNDERWARREN_SAFE`

Unknown values in ROLE, INTENT, IMPACT, DIALECT produce **warnings**, not errors (forward-compatible).

---

## KERNEL_ADJACENT rules (all are errors)

1. `CONF` must be numeric ≥ 0.85, or the literal string `HIGH`
2. `WUL` field must contain `⌬` (U+23AC, sovereign-proximity marker)
3. `ESCALATE` must be `OPERATOR`
4. `PERM` field is required

---

## Unconditional rejections (always errors, any tier)

| Field | Forbidden value | Reason |
|---|---|---|
| PERM | WRITE_SOVEREIGN | Unconditionally rejected; no confidence level overrides this |

---

## Validation result

```python
@dataclass
class ValidationResult:
    valid: bool                # False = fail closed; caller must not proceed
    tier: Optional[PacketTier]
    errors: list[str]          # empty when valid
    warnings: list[str]        # non-blocking; for human inspection
```

**Fail closed**: callers must check `result.valid` before acting on any packet.

---

## Safe boundary

The validator:
- reads packet strings only
- writes nothing to disk
- does not call `tools/helen_say.py`
- does not touch kernel, ledger, or canon
- does not grant or deny permissions — it validates the packet form only

Permission enforcement is HAL's responsibility, not the validator's.

---

## Example packets

**ACK:**
```
[ROLE::DAN][WUL::⚪]
```

**PRODUCTION — propose:**
```
[ROLE::DAN][INTENT::PROPOSE][CONF::0.8][IMPACT::LOCAL]
[TASK::HD-002][TRACE::epoch_043][DIALECT::DAN][WUL::📦✍️]
```

**KERNEL_ADJACENT — read-only request:**
```
[ROLE::DAN][INTENT::REQUEST][CONF::0.91][IMPACT::KERNEL_ADJACENT]
[TASK::HD-003][TRACE::epoch_048][DIALECT::KERNEL_SAFE]
[PERM::READ_ONLY][ESCALATE::OPERATOR][WUL::⌬⚠️📊]
```

---

## P1 success condition

> Invalid packets fail closed in tests.

`tests/test_wul_packet_validator.py` — 29 tests, all must pass.

---

*NON_SOVEREIGN · NO_SHIP · DRAFT_SPEC*
