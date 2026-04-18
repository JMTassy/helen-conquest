# CONQUEST_LAND MVP — Decisions & Next Steps

**Status:** Blueprint complete. Ready for implementation.

---

## Part 1: Decisions You Need to Make (Right Now)

These decisions **block** coding. Answer them now, and we finalize the spec.

### Decision 1: Board Configuration

**Question:** What's your hex board?

**Options:**
- **A) 19-tile hex** (center + 2 rings, like CONQUEST tabletop)
- **B) Larger** (37 tiles = center + 3 rings, for 6–8 players)
- **C) Custom grid** (rectangular or irregular)

**Recommendation:** A (19-tile hex, proven to work)

**Impact:** Determines adjacency logic in `rules.rs`

**Action:** Pick A, B, or C. Write it here: `BOARD_SIZE = ___`

---

### Decision 2: Player Count

**Question:** How many players per game?

**Options:**
- **A) 2–4** (standard, competitive)
- **B) 4–8** (cooperative/PvP mixed)
- **C) 10+** (massive multiplayer)

**Recommendation:** A (MVP scope, Kiomet-like)

**Impact:** Determines network scaling, fog-of-war complexity, server load

**Action:** Pick A, B, or C. Write it here: `PLAYER_COUNT = ___`

---

### Decision 3: Game Loop Cadence

**Question:** How fast should ticks happen?

**Options:**
- **A) 500ms ticks** (fast, arcade-like)
- **B) 1s ticks** (slower, tactical)
- **C) Variable** (adaptive based on actions)

**Recommendation:** A (500ms, matches server code)

**Impact:** Affects real-time feel, bandwidth, server load

**Action:** Pick A, B, or C. Write it here: `TICK_MS = ___`

---

### Decision 4: Lock Timeout

**Question:** How long do LOCK'ed tiles stay sealed?

**Options:**
- **A) 7 ticks** (3.5 seconds at 500ms)
- **B) 14 ticks** (7 seconds)
- **C) Permanent** (once locked, stays locked)
- **D) Player-negotiated** (unlock time varies)

**Recommendation:** A (7 ticks, matches server code)

**Impact:** Affects territory control strategy

**Action:** Pick A, B, C, or D. Write it here: `LOCK_TIMEOUT_TICKS = ___`

---

### Decision 5: Duel Determinism

**Question:** How should DUEL outcomes be determined?

**Options:**
- **A) Tick-based** (seed = tick % 2, alternates every tick)
- **B) Hash-based** (seed = SHA256(claimer + defender + tile), deterministic but unpredictable)
- **C) Skill-based** (player stats affect outcome)
- **D) Random** (fair coin flip)

**Recommendation:** B (more interesting for replays, still deterministic)

**Impact:** Affects gameplay strategy, replay verification

**Action:** Pick A, B, C, or D. Write it here: `DUEL_SEED = ___`

---

### Decision 6: UI Complexity

**Question:** What should the HUD show?

**Options:**
- **A) Minimal** (just hex grid + current tick + territory count)
- **B) Standard** (A + player names + pressure values + lock timers)
- **C) Full** (B + chat + scoreboard + action history)

**Recommendation:** A (MVP, Kiomet-style minimal)

**Impact:** Dev time, client complexity

**Action:** Pick A, B, or C. Write it here: `HUD_LEVEL = ___`

---

### Decision 7: Audio

**Question:** Include sound effects?

**Options:**
- **A) No audio** (MVP scope)
- **B) Minimal** (tile claim "ping", lock "seal sound")
- **C) Full** (music + SFX)

**Recommendation:** A (MVP, can add later)

**Impact:** Asset creation, client weight

**Action:** Pick A, B, or C. Write it here: `AUDIO = ___`

---

### Decision 8: Spectator Mode

**Question:** Should non-players be able to watch?

**Options:**
- **A) Yes, full visibility** (spectators see everything)
- **B) Yes, hidden info** (spectators see tiles but not player intentions)
- **C) No** (only players in game can view)

**Recommendation:** A (Kiomet-style, good for streaming)

**Impact:** Network messages, visibility logic

**Action:** Pick A, B, or C. Write it here: `SPECTATOR_MODE = ___`

---

## Part 2: Your Decision Card

**Print this out, fill it in, and we code to it:**

```
┌─────────────────────────────────────────────────┐
│ CONQUEST_LAND MVP DECISION CARD                 │
├─────────────────────────────────────────────────┤
│ Board Size:         [ A / B / C ]               │
│ Player Count:       [ A / B / C ]               │
│ Tick Cadence:       [ A / B / C ]               │
│ Lock Timeout:       [ A / B / C / D ]           │
│ Duel Seed:          [ A / B / C / D ]           │
│ HUD Level:          [ A / B / C ]               │
│ Audio:              [ A / B / C ]               │
│ Spectator Mode:     [ A / B / C ]               │
│ Date Filled:        [____]                      │
│ Approved By:        [____]                      │
└─────────────────────────────────────────────────┘
```

---

## Part 3: Immediate Next Steps (This Week)

### STEP A: Answer the 8 Decisions (30 min)

1. Read Part 1 above
2. Fill in your choice for each decision
3. Reply to Claude with your choices

**I will update the blueprint to match your choices.**

---

### STEP B: Set Up Cargo Workspace (1 hour)

```bash
# Run the quickstart script
bash CONQUEST_LAND_QUICKSTART.sh

# OR do it manually:
mkdir conquest-land-mvp
cd conquest-land-mvp
cargo new --lib common
cargo new --bin server
cargo new --bin client

# Test compilation
cargo check --all
```

**Expected output:**
```
   Compiling conquest-common v0.1.0
   Compiling conquest-server v0.1.0
   Compiling conquest-client v0.1.0
   Finished dev [unoptimized + debuginfo] target(s) in X.XXs
```

---

### STEP C: Fill in `common/src/rules.rs` (3–4 hours)

This is the **critical piece**. The rules are your game logic.

**What you need to implement:**
1. `validate_claim()` — Check adjacency, ownership, board boundaries
2. `validate_lock()` — Check tile ownership, lock state
3. `adjacent_tiles()` — Return neighbor list for a hex
4. `resolve_duel()` — Deterministic winner based on seed

**For a 19-tile hex, adjacency looks like this:**

```
        0
      1   2
    3   *   4
      5   6
```

**Template:**
```rust
pub fn adjacent_tiles(tile_id: TileId) -> Vec<TileId> {
    match tile_id.0 {
        0 => vec![TileId(1), TileId(2), TileId(4), TileId(5), TileId(6), TileId(3)],
        1 => vec![TileId(0), TileId(2), TileId(7), TileId(8), ...],
        // etc for all 19 tiles
        _ => vec![],
    }
}
```

**Time estimate:** 2–3 hours to get right

---

### STEP D: Implement Server Tick Loop (2–3 hours)

File: `server/src/tick_loop.rs`

This is where the game actually runs. Every 500ms (or your chosen cadence):

1. Increment tick
2. Apply pressure decay (optional)
3. Check lock timeouts
4. Broadcast new state to clients

**Skeleton is in the blueprint. Just fill in the physics.**

---

### STEP E: Implement Client WebSocket + Render Stub (2–3 hours)

File: `client/src/lib.rs` (WASM entry point)

1. Connect to server via WebSocket
2. Receive GameState every tick
3. Render hex grid (can start with colored rectangles)
4. Send Intent on click (can start with log statement)

**No need for fancy shaders yet. Just get the loop working.**

---

### STEP F: Test Determinism (1 hour)

Once rules + ledger are working:

```bash
cargo test -p conquest-common

# Expected:
# test event::tests::test_hash_determinism ... ok
# test ledger::tests::test_ledger_verify ... ok
# test rules::tests::test_duel_seed_consistency ... ok
```

---

## Part 4: Timeline Breakdown (4–5 Weeks)

| Week | What | Time | Blocker |
|------|------|------|---------|
| **1** | Decisions + common/ rules | 8 hrs | Decisions (Part 1) |
| **2–3** | server/ tick loop + authority | 15 hrs | rules.rs complete |
| **3–4** | client/ network + render | 15 hrs | server stable |
| **4** | Integration + testing | 10 hrs | All pieces done |
| **5** | Deploy + docs | 8 hrs | Tests passing |
| **Total** | **56 hours (~11 hrs/week)** | — | — |

---

## Part 5: How to Know You're Done (MVP Success Criteria)

### Functional

- [ ] Server runs 500ms ticks without crashing (24 hours of uptime)
- [ ] Client connects, receives state, displays something
- [ ] CLAIM works: player clicks tile → ownership changes
- [ ] LOCK works: tile locked → visual indicator (color change)
- [ ] DUEL works: two players → deterministic winner
- [ ] Ledger records everything + hashes verify

### Technical

- [ ] All unit tests pass
- [ ] Deterministic replay: same seed → same outcome
- [ ] Fog-of-war: spectator doesn't see hidden tiles
- [ ] No panics in 1 hour of continuous play

### UX

- [ ] Load URL → game state visible in <5 seconds
- [ ] Click tile → feedback <100ms
- [ ] Spectator can watch without account
- [ ] Broadcast (Twitch, YouTube) ready

---

## Part 6: What Happens After MVP

Once the MVP works:

1. **Polish** (1 week)
   - Better rendering (actual hex art)
   - Sound effects
   - Player names/avatars

2. **Scale** (2 weeks)
   - Persistent ledger (PostgreSQL)
   - Replay tools (verify ledger, watch replays)
   - API documentation

3. **Integration** (ongoing)
   - Link to LEGORACLE submission
   - Playtester feedback loop
   - Iterate mechanics based on real players

---

## Part 7: Open Communication

**When you're stuck:**

1. Share error message + context
2. I'll help debug
3. We iterate

**When you have questions:**

1. Ask in this doc (I'll update it)
2. Reply to Claude
3. We clarify assumptions

**When something changes:**

1. Tell me (decisions can evolve)
2. I'll update the blueprint
3. We move forward

---

## The One Critical Thing

**You don't need to be perfect. You need to be done.**

The blueprint is complete. The path is clear. The only thing stopping you is answering those 8 decisions.

**Do that now.** Reply to me with your 8 answers. I'll lock in the spec and you can start coding.

---

## Copy-Paste Template (Reply With This)

```
CONQUEST_LAND MVP Decisions:

1. Board Size:       [A/B/C]  → Reason: ___
2. Player Count:     [A/B/C]  → Reason: ___
3. Tick Cadence:     [A/B/C]  → Reason: ___
4. Lock Timeout:     [A/B/C/D] → Reason: ___
5. Duel Seed:        [A/B/C/D] → Reason: ___
6. HUD Level:        [A/B/C]  → Reason: ___
7. Audio:            [A/B/C]  → Reason: ___
8. Spectator Mode:   [A/B/C]  → Reason: ___

Additional notes: ___
```

---

**Now go fill that out. I'm waiting. ⏳**
