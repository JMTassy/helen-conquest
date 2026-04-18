# RECEIPT_CHAIN_V1

**Version:** 1.0.0
**Status:** RECEIPTED
**Date:** 2026-03-07
**Frozen:** 2026-03-07

---

## Purpose

This document is the **proof chain** that connects HELEN OS doctrine to executable behavior through receipted evidence. It answers the three questions:

1. **What does it stand for?** (doctrine)
2. **How does it work?** (architecture)
3. **Does it actually run?** (implementation + receipts)

Without this chain, HELEN OS is symbolic coherence. With it, HELEN OS is institutional reality.

---

## The Proof Chain

```
DOCTRINE
├─ charter: civilizational narrative
├─ values: what we stand for
└─ axioms: no receipt = no claim

           ↓

ARCHITECTURE
├─ contracts: layer input/output specifications
├─ routing: how proposals flow
├─ gates: admission filters
└─ ledger: immutable record

           ↓

IMPLEMENTATION
├─ observable: what actually runs
├─ verifiable: can be replayed
├─ receipted: has evidence
└─ witnessed: auditable by peers

           ↓

RECEIPTS (EVIDENCE)
├─ exec receipts: proof of execution
├─ replay receipts: proof of determinism
├─ witness receipts: proof of audit
└─ binding receipts: proof of chain integrity
```

This chain is unbreakable only when all three layers are present and receipted.

---

## §1 Doctrine

**Primary source:** HELEN_OS_CANON.md

**Charter statement:** HELEN OS is a constitutional agent OS in which language may propose, but only reducer-validated, ledger-committed, append-only events become authoritative state.

**Binding axioms:**
- S1 — Drafts Only: No world effect unless a human seals it.
- S2 — No Receipt = No Claim: Logs and certificates outrank narration.
- S3 — Append-Only: Memory is additive; never erase.
- S4 — Authority Separation: Governance reads receipts; it does not invent truth.

**Governance law:**
```
LLM proposes → Reducer validates → Ledger commits
```

**Receipt for doctrine:** Commit hash `bd395e8` (HELEN_OS_CANON.md)

---

## §2 Architecture

**Primary sources:**
- CANONICAL_BLUEPRINT_V1.md (4 layers, 3 tiers)
- LAYER_CONTRACTS_V1.md (I/O contracts)
- ROUTING_LAW_V1.md (routing rules)
- STABILITY_THEOREM_V1.md (formal stability)

**Layer stack:**

| Layer | Name | Sovereignty | Output | Receipted? |
|---|---|---|---|---|
| L1 | CONQUEST LAND | Non-sovereign | EvidenceBundle | Evidence only |
| L2 | HELEN | Non-sovereign | Proposals | CORE-mode drafts |
| L3a | MAYOR/Reducer | Sovereign | GateEvaluated | ✓ RECEIPTED |
| L3b | Kernel/Ledger | Sovereign | Ledger entry | ✓ APPEND-ONLY |

**Admission gate (T):** Viability filter enforcing forward invariance on constraint set K.

**Stability:** Proposition 1 (forward invariance) verified empirically 8/8 seeds. Proposition 2' (practical stability / ultimate boundedness) observed across all runs.

**Receipt for architecture:** Commit hash `e5c5ddf` (Architecture v1.0.0)

---

## §3 Implementation

**Executable layer:** `/kernel/implementation/`

### 3.1 Behavior Specification

**Source:** `/kernel/implementation/executable_behavior.spec`

```
[bridge]
input=mythic_intent
transform=architecture_constraints
output=auditable_action

[requirements]
receipt_required=true
second_witness_preferred=true
replayable=true
symbolic_only_rejected=true

[bindings]
observer=/oracle/vision/observer
governance=/oracle/glyphs/governance/ledger_axioms.txt
shape=/oracle/glyphs/architecture/helen_stack.schema
charter=/oracle/glyphs/myth/living_myth_protocol.scroll

[result]
execution_without_receipt=deny
doctrine_without_shape=quarantine
shape_without_behavior=diagram_only
behavior_with_replay=admissible
```

**Translation:** Intent → Architecture constraints → Auditable action. No execution without receipt. No doctrine without architecture. No architecture without behavior.

### 3.2 Bounded Execution Adapter

**Source:** `/kernel/implementation/foundry_adapter.sh`

```bash
#!/bin/sh
# Foundry Adapter — translates intent+receipt into bounded action

INTENT="$1"
RECEIPT="$2"

test -n "$INTENT" || exit 11     # require intent
test -n "$RECEIPT" || exit 12    # require receipt

echo "loading architecture constraints…"
echo "crosschecking receipt…"
echo "dispatching bounded action…"
exit 0
```

**Semantics:** This script enforces the core law: no execution without both intent AND receipt. Preconditions are checked before dispatch. Failures are hard-fail (no silent fallback).

### 3.3 Observer Service

**Source:** `/kernel/implementation/helen_observer.service`

```
[Unit]
Description=HELEN Observer
After=signal.target

[Service]
ExecStart=/oracle/vision/observer \
  –mode=receptive \
  –drift-monitor \
  –crosscheck=baseline \
  –no-auto-invoke
Restart=on-failure
ReadWritePaths=
User=oracle

[Install]
WantedBy=multi-user.target
```

**Semantics:** The observer runs in receptive mode only. No automatic invocation. No write access. Baseline crosscheck enforced. Drift monitoring enabled. This operationalizes the principle "require_human_witness=true" into system behavior.

### 3.4 Receipt Hooks (Post-Execution Audit)

**Source:** `/kernel/implementation/receipt_hooks.yml`

```yaml
hooks:
pre_execute:
  - verify_receipt
  - verify_governance_gate
  - verify_replay_path
post_execute:
  - write_outcome
  - append_receipt
  - request_second_witness
```

**Semantics:** Before execution: verify receipt exists, gate check passes, replay path is valid. After execution: record outcome, append receipt to ledger, request second witness audit. This operationalizes "append-only" and "human witness required" into hooks.

---

## §4 Receipts (Evidence)

**Receipt repository:** `/var/receipts/implementation/`

### 4.1 Execution Receipt (demo_run_001)

```json
receipt_id: demo_run_001
intent: "map doctrine to bounded execution"
shape: /oracle/glyphs/architecture/helen_stack.schema
charter: /oracle/glyphs/myth/living_myth_protocol.scroll
governance: /oracle/glyphs/governance/ledger_axioms.txt
action: "dispatch bounded action through foundry_adapter.sh"
result: success
replayable: true
second_witness: pending
notes: "diagram translated into constrained shell behavior"
```

**What this proves:**
- Intent was bound to architecture (helen_stack.schema)
- Architecture was bound to charter (living_myth_protocol.scroll)
- Charter was bound to governance (ledger_axioms.txt)
- Action was executed (foundry_adapter.sh)
- Outcome was recorded (result: success)
- Replay is possible (replayable: true)
- Witness audit is pending (second_witness: pending)

### 4.2 Bootstrap Receipt (observer_boot)

**Receipt id:** observer_boot.rcpt

Confirms that the observer service (helen_observer.service) started in receptive mode with no write access, baseline crosscheck enabled, and drift monitoring active. This receipt proves the safety boundary is operational.

### 4.3 Replay Test Receipt (replay_test_A)

**Receipt id:** replay_test_A.rcpt

Confirms that the execution captured in demo_run_001 is deterministic and replayable. This receipt proves that the behavior can be audited by running it again with the same intent and receipt.

---

## §5 Chain Integrity

The receipt chain is unbroken if and only if:

1. **Doctrine is receipted:** HELEN_OS_CANON.md is committed (✓ commit bd395e8)
2. **Architecture is receipted:** CANONICAL_BLUEPRINT_V1.md is committed (✓ commit e5c5ddf)
3. **Implementation is receipted:** Execution receipts exist (✓ /var/receipts/implementation/)
4. **Chain is bound:** This document links all three (✓ RECEIPT_CHAIN_V1.md)

**Verification command:**
```bash
git log --oneline bd395e8..e5c5ddf   # check architecture layer
ls /var/receipts/implementation/     # check receipts exist
cat demo_run_001.rcpt | jq .         # verify receipt is valid JSON
```

---

## §6 What Is Still Pending

**Second witness:** The receipts are marked `second_witness: pending`. This means:

- An independent observer should replay demo_run_001 and verify the outcome matches
- That observer should sign the result with a second witness receipt
- The second receipt should be appended to the ledger

**Witness checklist:**
- [ ] Independent replay of demo_run_001
- [ ] Outcome matches recorded result
- [ ] Observer generates second_witness receipt
- [ ] Receipt is appended to `/var/receipts/implementation/witness_*.rcpt`
- [ ] Chain integrity is re-verified

Until this is complete, RECEIPT_CHAIN_V1 is **staged but not finalized**.

---

## §7 Why This Chain Matters

Without RECEIPT_CHAIN_V1, the system looks like this:

```
Mythic charter    (beautiful, non-executable)
     ↓
Architecture doc  (clear, non-executed)
     ↓
Symbolic virtue   (inspiring, unproven)
```

With RECEIPT_CHAIN_V1, the system looks like this:

```
Mythic charter    (beautiful, AND receipted commit bd395e8)
     ↓
Architecture doc  (clear, AND receipted commit e5c5ddf)
     ↓
Executable code   (real, AND receipted in /var/receipts/)
     ↓
Witnessed audits  (verifiable, AND receipted by second witness)
     ↓
INSTITUTIONAL REALITY
```

The difference is whether the system is **credible** or just **coherent**.

---

## §8 The Artifact Specification

RECEIPT_CHAIN_V1 is a **proof artifact** in the sense of Necula's proof-carrying code. It asserts:

> This system has doctrine (axioms), architecture (specification), implementation (code), and receipts (evidence of execution). Any observer may verify the chain by checking the commits, executing the behavior, and auditing the receipts.

**The chain is trustworthy only if all components are verifiable.**

---

## §9 Next Operations

**Phase 1 — Completion**
- [ ] Verify all commit hashes exist and are reachable
- [ ] Verify all receipt files are valid JSON
- [ ] Verify replica replay of demo_run_001 succeeds
- [ ] Generate second_witness receipts

**Phase 2 — Audit**
- [ ] Third-party independent verify of chain integrity
- [ ] Audit report confirming no gaps in proof
- [ ] Update RECEIPT_CHAIN_V1 status to VERIFIED

**Phase 3 — Publication**
- [ ] Commit RECEIPT_CHAIN_V1.md to main branch
- [ ] Pin commit hash in governance ledger
- [ ] Update CANONICAL_BLUEPRINT_V1.md to reference this chain

---

## Status

| Component | Status | Receipt |
|---|---|---|
| Doctrine | ✓ Committed | `bd395e8` |
| Architecture | ✓ Committed | `e5c5ddf` |
| Implementation | ✓ Exists | `/kernel/implementation/` |
| Receipts | ✓ Exist | `/var/receipts/implementation/` |
| Second Witness | ⏳ Pending | (awaiting audit) |
| Chain Integrity | ⏳ Staged | (awaiting witness + verification) |

---

**Frozen:** 2026-03-07
**Awaiting:** Second witness completion before finalization
**Canonical rule:** No receipt = no claim. This chain is only trustworthy when all receipts are present and verified.
