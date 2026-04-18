# CONQUEST — Formal State Machine Specification

**Status:** Formal specification (executable)
**Scope:** WorldState algebra, mutation calculus, deterministic tribunal
**Date:** February 15, 2026

---

## 1. CORE DEFINITION: WorldState

```
WorldState := {
    version: Version,
    timestamp: Timestamp,
    ledger_hash: Hash,

    territory_map: Territory[],
    factions: Faction[],
    resources: Resource[],

    tribunal_state: TribunalState,
    prince_seal: Seal,
}
```

### 1.1 Immutable Identity

```
WorldState.ID := hash(version || ledger_hash || timestamp)
```

Every WorldState has a unique, deterministic identifier.
Identical (version, ledger, timestamp) → identical ID.
If ID changes, mutation occurred.

### 1.2 Versioning

```
Version := (epoch: Int, seq: Int, micro: Int)

Example:
  (1, 0, 0) = First world state (genesis)
  (1, 0, 1) = First mutation on epoch 1
  (1, 1, 0) = First mutation after tribunal validation
  (2, 0, 0) = Epoch rollover (triggered by constitutional event)
```

Versions are **monotonic only**. No rollback. No rewind.

---

## 2. TERRITORY MODEL

```
Territory := {
    id: TerritoryID,
    owner: FactionID | null,
    stability: Float [0.0, 1.0],
    resources: ResourceCount[],
    contested: Boolean,
    last_seal_round: Round,
}
```

### 2.1 Territory Ownership Law

```
Mutation that changes Territory.owner must:
  (a) come from owner faction OR prince seal
  (b) pass tribunal validation
  (c) be recorded as Mutation with:
      - pre_state: Territory (before)
      - post_state: Territory (after)
      - sealed_by: PrinceSeal
      - receipts: TribunalReceipt[]
```

### 2.2 Stability Computation

```
Territory.stability(round) :=
    base_stability
    - (contested ? 0.1 : 0.0)
    - (resources_depleted ? 0.2 : 0.0)
    + (defended_last_round ? 0.05 : 0.0)

Base range: [0.0, 1.0]
0.0 = collapsed territory
1.0 = fortress
```

---

## 3. FACTION MODEL

```
Faction := {
    id: FactionID,
    name: String,
    archetype: Archetype,  # Templar, Rosicrucian, Chaos

    authority: Authority,
    power: Float [0.0, 10.0],

    occupied_territory: TerritoryID[],
    proposals_pending: Proposal[],
    receipts: TribunalReceipt[],

    last_action_round: Round,
    mood: Mood,
}
```

### 3.1 Authority Definition

```
Authority := {
    can_propose: Boolean,
    can_challenge: Boolean,
    can_provide_evidence: Boolean,

    can_mutate_territory: Boolean,  # ALWAYS FALSE
    can_mutate_constitution: Boolean,  # ALWAYS FALSE
    can_seal: Boolean,  # ALWAYS FALSE
}

Hard Rule: For all Faction f:
    f.Authority.can_seal == FALSE
    f.Authority.can_mutate_constitution == FALSE
```

Factions propose. They do not decide.

### 3.2 Power Law

```
Faction.power is NOT used in Tribunal validation.

It is narrative/aesthetic only.

Tribunal decisions are:
    deterministic(proposal, receipts, constitution)

NOT:
    deterministic(proposal, receipts, constitution, faction.power)
```

---

## 4. MUTATION MODEL

```
Mutation := {
    id: MutationID,
    round: Round,

    proposal: Proposal,
    tribunal_receipt: TribunalReceipt,
    prince_seal: PrinceSeal,

    pre_state: WorldState.ID,
    post_state: WorldState.ID,

    timestamp: Timestamp,
    ledger_entry_hash: Hash,
}
```

### 4.1 Mutation = (Proposal + Validation + Seal)

```
Valid Mutation IFF:
    (1) proposal is well-formed
    (2) tribunal_receipt.verdict == APPROVED
    (3) prince_seal.valid == TRUE
    (4) pre_state hash matches ledger
    (5) post_state is deterministic from (pre_state + proposal)
```

### 4.2 Mutation Determinism

```
For mutation M:
    if (pre_state, proposal, tribunal_config) == (pre_state', proposal', tribunal_config')
    then apply(M) == apply(M')
    then post_state == post_state'
```

Same input → same mutation output.
No randomness. No "what-if" scenarios.

### 4.3 Ledger Append

```
All mutations are appended (never overwritten):

Ledger := Mutation[]  (immutable list)

To verify world state:
    ws = apply_all_mutations(genesis_state, Ledger)
```

Ledger is the source of truth. Not the WorldState display.

---

## 5. TRIBUNAL VALIDATION MODEL

```
Tribunal := {
    constitution: Constitution,
    evidence_pool: Evidence[],
    pending_proposals: Proposal[],
}

Tribunal.validate(proposal, evidence[])
    -> TribunalReceipt
```

### 5.1 Tribunal Receipt

```
TribunalReceipt := {
    proposal_id: ProposalID,
    verdict: Verdict,  # APPROVED | REJECTED | CONTESTED

    evidence_examined: EvidenceID[],
    rule_applied: Rule[],

    validation_hash: Hash,
    timestamp: Timestamp,
}

Verdict in {APPROVED, REJECTED, CONTESTED}
```

### 5.2 Deterministic Validation

```
validate(proposal, evidence, constitution) := {
    (1) Parse proposal into claims
    (2) Cross-reference each claim against evidence
    (3) Apply constitution rules
    (4) Emit APPROVED | REJECTED | CONTESTED
    (5) Hash result

    Same (proposal, evidence, constitution)
        -> same verdict
        -> same hash
}
```

No human judgment. No "feels right" logic.
Pure rule application.

### 5.3 Contested Verdict

```
Verdict == CONTESTED when:
    - Evidence is ambiguous
    - Multiple constitutional rules apply
    - Conflicting faction claims

Action:
    - Mutation is BLOCKED
    - Proposal returns to factions
    - Tribunal requests clarification
```

CONTESTED is safe state. Not failure. Not approval.

---

## 6. PRINCE SEAL MODEL

```
Seal := {
    prince_id: PrinceID,
    mutation_id: MutationID,

    pre_state_hash: Hash,
    post_state_hash: Hash,

    tribunal_receipt_hash: Hash,

    signature: Signature,
    timestamp: Timestamp,
}
```

### 6.1 Seal Validity

```
Seal.valid() IFF:
    (1) signature verifies against prince_public_key
    (2) tribunal_receipt_hash matches referenced receipt
    (3) pre_state_hash matches ledger state at round-1
    (4) post_state_hash is deterministic from (pre_state + proposal)
```

Prince does not create state. Prince only seals validated mutations.

### 6.2 Seal as Reducer

```
Prince role:

    Input:  (proposal + tribunal_receipt)
    Check:  Is tribunal_receipt.verdict == APPROVED?
    Action: If YES → emit Seal
            If NO → reject
    Output: Seal (if approved) OR null

Prince cannot:
    - override tribunal
    - invent state
    - create mutations without tribunal approval
    - break determinism
```

---

## 7. MUTATION APPLICATION ALGEBRA

```
apply(mutation: Mutation, ws: WorldState) -> WorldState'
```

### 7.1 Territory Mutation

```
apply_territory_mutation(m: Mutation, ws: WorldState) {
    old_territory = ws.territory_map[m.proposal.target_id]

    // Validation already done by Tribunal
    // We just compute new state

    new_territory = {
        id: old_territory.id,
        owner: m.proposal.new_owner,
        stability: m.proposal.new_stability,
        resources: m.proposal.new_resources,
        contested: m.proposal.contested,
        last_seal_round: m.round,
    }

    ws.territory_map[m.proposal.target_id] = new_territory
    return ws
}
```

### 7.2 Faction Mutation

```
apply_faction_mutation(m: Mutation, ws: WorldState) {
    old_faction = ws.factions[m.proposal.faction_id]

    new_faction = {
        id: old_faction.id,
        // other fields unchanged except:
        power: m.proposal.new_power,  // if power changed
        occupied_territory: m.proposal.new_territories,
        mood: m.proposal.new_mood,
    }

    ws.factions[m.proposal.faction_id] = new_faction
    return ws
}
```

### 7.3 Deterministic Application

```
for mutation in Ledger:
    ws = apply(mutation, ws)

Every step is deterministic.
No randomness.
Replayable from genesis.
```

---

## 8. CONSTITUTION MODEL

```
Constitution := {
    version: Version,
    rules: Rule[],

    factions_allowed: Faction[],
    resources_types: ResourceType[],

    territory_max: Int,
    stability_thresholds: Map[Mood, Float],

    frozen_until: Timestamp,
}

Constitution is immutable during play.
Changes require epoch rollover.
```

### 8.1 Rule Definition

```
Rule := {
    id: RuleID,
    precondition: Predicate,
    conclusion: Statement,

    applies_to: Faction[] | "all",
}

Example:
    Rule(id: "R001") {
        precondition: faction.archetype == TEMPLAR
        conclusion: can_challenge == TRUE
    }
```

### 8.2 Rule Application

```
validate(proposal) {
    for rule in Constitution.rules:
        if rule.precondition(proposal):
            if not rule.conclusion(proposal):
                return REJECTED
    return APPROVED
}
```

Rules are applied in deterministic order.

---

## 9. REPLAYABILITY PROOF

```
Theorem:
    Given ledger L and genesis state S0,
    applying mutations in L produces world state W
    that is deterministic and reproducible.

Proof sketch:
    (1) Each mutation encodes (proposal, tribunal_receipt, seal)
    (2) Applying mutation requires no new decisions
    (3) apply(mutation, state) is pure function
    (4) Ledger is immutable, append-only
    (5) Replay = apply_all(mutations, genesis)
    (6) QED: Same ledger + genesis -> same final state
```

### 9.1 Replay Test

```
def test_replay(seed: Int):
    # Play game, generate ledger L
    game1 = play(seed)
    L = game1.ledger

    # Replay game, apply same ledger
    game2 = replay(genesis_state, L)

    # Final states must be identical
    assert game1.world_state == game2.world_state
    assert game1.world_state.ID == game2.world_state.ID
```

---

## 10. STATE MACHINE DIAGRAM

```
┌─────────────────────────────────────────────────┐
│                  GENESIS_STATE                  │
│           (epoch: 0, seq: 0, hash: X)          │
└────────────────────┬────────────────────────────┘
                     │
                     ↓
        ┌────────────────────────┐
        │   Faction Proposes     │
        │   (new mutation)       │
        └────────┬───────────────┘
                 │
                 ↓
        ┌────────────────────────┐
        │  Tribunal Validates    │
        │  (check evidence)      │
        └────────┬───────────────┘
                 │
        ┌────────┴──────────┐
        │                   │
        ↓                   ↓
    APPROVED            REJECTED
        │                   │
        ↓                   ↓
    ┌─────────┐        (return to
    │ Prince  │         factions)
    │  Seals  │
    └────┬────┘
         │
         ↓
    ┌──────────────────────┐
    │ Apply Mutation       │
    │ to WorldState        │
    │ (deterministic)      │
    └────┬─────────────────┘
         │
         ↓
    ┌──────────────────────┐
    │ WorldState'          │
    │ (epoch: N, seq: M)   │
    │ (new hash)           │
    └────┬─────────────────┘
         │
         ↓
    [ Append to Ledger ]
         │
         ↓
    [ Next Mutation ]
```

---

## 11. INVARIANT ENFORCEMENT

```
At every state transition, verify:

I1: WorldState.version is monotonic increasing
I2: WorldState.ID is unique per version
I3: All mutations in ledger are sealed
I4: All sealed mutations are approved by tribunal
I5: apply(all_mutations, genesis) == current_state
I6: No faction has can_seal == TRUE
I7: No territory owner is null unless contested
I8: Resources are conserved (unless inflation logged)
```

Violation of any invariant → system is corrupted.

---

## 12. EXAMPLE: Territory Capture Mutation

```
PROPOSAL:
{
    type: "territory_capture",
    faction: Templar,
    target_territory: "Castle_001",
    new_owner: Templar,
    new_stability: 0.8,
    justification: "Templars fortified defenses"
}

TRIBUNAL VALIDATION:
{
    proposal_id: "prop_0042",
    evidence_examined: ["defense_receipt_0041", "stability_log_0041"],
    rule_applied: ["R_ownership_change", "R_stability_threshold"],
    verdict: APPROVED,
    validation_hash: "abc123..."
}

PRINCE SEAL:
{
    mutation_id: "mut_0042",
    pre_state_hash: "xyz789...",
    post_state_hash: "def456...",
    tribunal_receipt_hash: "abc123...",
    signature: <valid>
}

MUTATION APPLICATION:
{
    ws.territory_map["Castle_001"].owner = Templar
    ws.territory_map["Castle_001"].stability = 0.8
    ws.version = (1, 0, 42)
}

LEDGER APPEND:
Ledger[42] = {
    proposal: ...,
    receipt: ...,
    seal: ...,
    pre_state: "xyz789...",
    post_state: "def456...",
}
```

---

## 13. MINIMALIST REFERENCE

### Authority Flow (Only Path)

```
Proposal → Tribunal → Seal → Apply → Ledger
```

### State Change Law

```
No WorldState mutation without:
    - Valid Tribunal Receipt
    - Valid Prince Seal
    - Deterministic Application
```

### Replayability Law

```
Same Ledger + Genesis = Same Final State
(no exceptions)
```

---

## 14. DEPLOYMENT CHECKLIST

- [ ] WorldState algebra implemented
- [ ] Mutation application is pure function
- [ ] Tribunal validation deterministic
- [ ] Seal verification cryptographic
- [ ] Ledger immutable (append-only)
- [ ] Replay test passes 1000 times
- [ ] All invariants enforced in CI
- [ ] Faction isolation verified (static analysis)
- [ ] Constitution frozen (no runtime mutations)

---

**This is the mathematical foundation of CONQUEST governance.**

No story. No aesthetic.

Just state, transition, validity.

If this runs, world-state is auditable.
If ledger is intact, history is verifiable.
If invariants hold, authority is legitimate.

