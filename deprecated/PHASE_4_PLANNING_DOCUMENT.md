# Phase 4 Planning — Game Integration (Days 10–12)

**Duration:** ~48 hours (3 days)
**Dependency:** Phases 1–3 complete ✅
**Objective:** Remove hidden state from CONQUESTmon-Gotchi, bind to federation ledger

---

## Current State (Phase 3 Complete)

### What Exists
- ✅ 3-node federation (oracle-1, oracle-2, oracle-3)
- ✅ Peer-to-peer gossip protocol
- ✅ Consensus reporting (voting matrices)
- ✅ Byzantine detection (>30% disagreement threshold)
- ✅ K5 determinism verified across stack

### What's Missing (Phase 4 Scope)
- ❌ Game event → Proposal conversion
- ❌ Game state persistence to ledger
- ❌ Duel outcome → Governance event mapping
- ❌ Game-ledger bidirectional consistency verification

---

## Architecture (Phase 4 Goal)

```
CONQUESTmon-Gotchi Game
    ↓ (duel outcome: attacker wins)
    ↓
Proposal (event-based):
  "Player-A conquered Territory-B"
  Evidence: duel_id, attacker_stats, defender_stats, outcome_hash
    ↓
3-Node Federation
  oracle-1: Processes through debate cycle
  oracle-2: Processes independently
  oracle-3: Processes independently
    ↓
Ledger Entry (immutable):
  {
    "proposal_id": "GAME-CONQUEST-001",
    "duel_id": "DUEL-20260217-001",
    "event": "territory_claimed",
    "attacker": "player-A",
    "defender": "player-B",
    "territory": "T-005",
    "decision": "ACCEPT",  (federation consensus)
    "receipt_id": "R-...",
    "timestamp": "2026-02-17T12:00:00Z"
  }
    ↓
Game State Updated
  (territory ownership derives from ledger, not hidden state)
```

---

## Key Design Decisions to Make (Phase 4 Kickoff)

### 1. Event Format: Game → Proposal

**Question:** How should game events map to proposals?

**Current Game Events (from MEMORY.md):**
- Duel outcome (2/3 manches): attacker vs defender
- Territory claim: winner claims territory
- Prison: captured player (Militaire archetype)

**Proposed Proposal Format:**
```python
Proposal(
    proposal_id="GAME-DUEL-{timestamp}",
    proposer="game_engine",
    intent="TERRITORY_CLAIM",
    content={
        "type": "game_event",
        "action": "CLAIM_TERRITORY",
        "duel_id": "DUEL-20260217-001",
        "attacker": "player-A",
        "defender": "player-B",
        "territory_id": "T-005",
        "duel_outcome": {"manches_won": 2, "manches_lost": 1},
        "evidence_hash": "sha256(duel_result)"
    },
    evidence={
        "confidence": 0.95,  # Duel outcome is high-confidence
        "source": "game_engine"
    }
)
```

**Considerations:**
- Evidence confidence: Duels have clear outcomes (high confidence)
- Novelty: Novel if player-territory combo is new
- State delta: Territory claims change game state significantly

### 2. Debate Cycle Impact

**Question:** Should game events go through full debate?

**Current Design (to verify):**
- Warden agent: Evaluates duel evidence + player stats
  - May REJECT if evidence is weak or player is low-level
  - May MODIFY if duel is close (modify to "contested territory")
- Steward agent: Favors expansion (ACCEPT territory claims)
- Archivist agent: Checks for contradictions (e.g., already owns territory?)

**Risk:** If novel game event gets REJECTED by Warden, does game state update anyway?

**Answer (Design Decision):**
- ACCEPT with consensus → Territory claimed (finalized)
- CONTESTED → Territory claim deferred (needs more evidence? re-play duel?)
- REJECT → Territory claim denied (game state unchanged)

This creates interesting governance: disputed territory claims can be re-evaluated.

### 3. Determinism in Game Events

**Question:** Can CONQUESTmon-Gotchi produce deterministic outcomes?

**Current Code (conquest_v2_hexacycle.py):**
- Uses random.seed() for reproducibility
- Duel outcomes from dice rolls + QCM scores
- Deterministic IF input seed is fixed

**Required for Phase 4:**
- Game must accept `deterministic_seed` parameter
- Same seed + same game state → identical game events
- Enables federation to replay game outcomes

**Implementation:**
```python
# Phase 4 addition to conquest_v2_hexacycle.py
class DeterministicGameEngine:
    def __init__(self, seed: int):
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)

    def run_duel(self, attacker, defender) -> DuelOutcome:
        # All dice rolls, QCM, ecology use seeded RNG
        return DuelOutcome(...)
```

### 4. Ledger Binding

**Question:** Where does game state persist?

**Current Game (hidden state):**
- Board state in memory (5×5 grid)
- Player stats in memory
- Territory ownership in memory

**Phase 4 Design:**
```
Game State = Ledger.filter(type="territory_claim")
  ↓
Reconstruct current board from:
  - All ACCEPT receipts (territory claims)
  - Minus all REJECT receipts (disputed claims)
  - Ordered by timestamp
  ↓
Deterministic game state (reproducible from ledger)
```

**Implementation:**
```python
class GameStateFromLedger:
    def __init__(self, ledger: OracleKernel):
        self.ledger = ledger

    def get_board_state(self) -> GameBoard:
        # Extract all territory claims from ledger
        territory_claims = self.ledger.filter(claim_type="territory_claim")

        # Reconstruct board from receipts
        board = GameBoard()
        for claim in territory_claims:
            if claim.decision == "ACCEPT":
                board.claim_territory(claim.attacker, claim.territory_id)

        return board
```

---

## Work Packages (Phase 4 Breakdown)

### WP1: Game Event Conversion (8 hours)

**Deliverable:**
- `game_event_converter.py` — Convert game events to proposals
- Update `conquest_v2_hexacycle.py` to use converter
- Add deterministic_seed parameter to game engine

**Acceptance Criteria:**
- ✅ Duel outcome → Proposal
- ✅ Game event format matches swarm expectations
- ✅ Deterministic game with seed produces identical events
- ✅ Evidence field populated correctly (player stats, duel ID)

**Risk:**
- Game RNG may have hidden non-determinism
- Mitigation: Audit all random calls, add explicit seeding

---

### WP2: Ledger Binding Layer (12 hours)

**Deliverable:**
- `game_ledger_binding.py` — Bidirectional game↔ledger sync
- `GameStateFromLedger` class — Reconstruct game state
- Integration tests showing game state derived from ledger only

**Acceptance Criteria:**
- ✅ Game events persisted to ledger as proposals
- ✅ Game state reconstructed from ledger (no hidden state)
- ✅ Territory ownership matches ledger receipts
- ✅ Replay: same ledger → identical game state

**Risk:**
- Ledger lacks information for full game state (e.g., player health?)
- Mitigation: Store all game state in proposal content/evidence

---

### WP3: Federation-Game Integration (12 hours)

**Deliverable:**
- `oracle_game_federation.py` — Orchestrates game + federation
- 3-node federation processes game events simultaneously
- Game state updated per consensus

**Acceptance Criteria:**
- ✅ 3 oracle instances see identical game state
- ✅ Duel outcomes → Proposals → Consensus → Territory claim
- ✅ Byzantine detection flags inconsistent nodes (if adversary modifies game)
- ✅ Full game simulation (20 turns) runs on federation backend

**Test:**
- Play 20-turn game with federation backend
- All 3 instances report identical board state
- Game can replay deterministically

**Risk:**
- Federation latency may slow game (each turn is 3 proposal→consensus cycles)
- Mitigation: Batch game events? Or accept ~100ms per turn?

---

### WP4: Consistency Verification (8 hours)

**Deliverable:**
- `test_game_ledger_consistency.py` — 10+ tests
- Verify game state == ledger state
- Verify federation consensus == game outcome

**Acceptance Criteria:**
- ✅ 10 property-based tests passing
- ✅ Replay test: save ledger, reconstruct game, compare state
- ✅ Byzantine test: corrupt 1 instance, detect mismatch

**Tests:**
1. Deterministic game duel → identical proposal
2. Proposal → federation consensus → ledger entry
3. Ledger entry → game state update
4. Multiple duels → game state evolves correctly
5. Replay: ledger → game state → identical output
6. Byzantine: modify 1 node's proposal, detect flag
7. Territory ownership matches ledger receipts
8. Player stats unchanged (read-only in game)
9. No hidden state (all game state from ledger)
10. Consensus on adverse outcomes (duel losses)

---

## Implementation Order (Recommended)

### Day 10 (First 16 hours)
1. **WP1a** (4 hours): Game event converter (duel→proposal)
2. **WP1b** (4 hours): Deterministic game seeding + testing
3. **WP2a** (8 hours): Ledger binding layer (game→ledger)

### Day 11 (16 hours)
4. **WP2b** (4 hours): State reconstruction (ledger→game)
5. **WP3a** (8 hours): Federation-game integration
6. **WP3b** (4 hours): Full game federation tests

### Day 12 (16 hours)
7. **WP4** (8 hours): Consistency verification + property tests
8. **Polish** (8 hours): Bug fixes, optimization, documentation

---

## Blockers & Unknowns

### Technical Unknowns
- [ ] Is CONQUESTmon-Gotchi RNG fully deterministic?
- [ ] What game state cannot be derived from ledger?
- [ ] Performance: Can federation handle game event rate?
- [ ] Does debate cycle reject valid game events?

### Design Questions
- [ ] Should contested territory claims retry duel?
- [ ] How to handle simultaneous claims (race condition)?
- [ ] What's the evidence confidence threshold for game events?
- [ ] Should game pause during Byzantine dispute resolution?

### Dependencies
- ✅ Phase 1 Kernel (complete)
- ✅ Phase 2 Swarm (complete)
- ✅ Phase 3 Federation (complete)
- ⏳ CONQUEST game code (needs audit for determinism)

---

## Success Criteria (Phase 4 Definition of Done)

### Functional
- ✅ Game events converted to proposals
- ✅ All game state in ledger (no hidden state)
- ✅ 3-node federation processes game events
- ✅ Territory claims deterministic + reproducible

### Non-Functional
- ✅ Determinism verified (same input → same output)
- ✅ K5 maintained (game events produce deterministic receipts)
- ✅ Performance acceptable (game playable at federation latency)
- ✅ Byzantine detection works on game events

### Testing
- ✅ 10+ consistency tests passing
- ✅ 20-turn game simulation on federation backend
- ✅ Replay test: ledger → game state
- ✅ Byzantine test: corrupt node → detect flag

### Documentation
- ✅ Game event format documented
- ✅ Ledger binding architecture explained
- ✅ Game-federation integration guide

---

## Rollback Plan (If Phase 4 Fails)

If game integration doesn't work:
1. Keep Phases 1–3 (kernel + swarm + federation)
2. Deploy as governance-only system (no game)
3. Use Phase 5 to optimize governance layer
4. Game binding becomes Phase 5 extension task

**Risk Assessment:** LOW (phases 1–3 are independent of game)

---

## Stretch Goals (If Ahead of Schedule)

- [ ] Add game event validation rules (e.g., "player can't claim if in prison")
- [ ] Implement dispute resolution for contested claims
- [ ] Create game rendering layer that reads from ledger
- [ ] Performance optimization: parallel federation processing
- [ ] Add spectator mode: view consensus from ledger

---

## Next Steps (End of Phase 3)

1. ✅ Audit conquest_v2_hexacycle.py for determinism
2. ✅ Design game event → proposal conversion
3. ✅ Begin WP1 (game event converter)

**Estimated Phase 4 Start:** Immediately after Phase 3
**Estimated Phase 4 Complete:** Day 12 (end of synthesis plan)

---

**Status:** Ready for Phase 4 kickoff
**Owner:** Autonomous execution (per user's Phase 3 approval)
**Tracking:** PHASE_4_COMPLETION_REPORT.md (will be created end of Day 12)
