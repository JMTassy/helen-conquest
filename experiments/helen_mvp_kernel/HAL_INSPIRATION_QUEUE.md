# HAL_INSPIRATION_QUEUE

Non-sovereign queue of upstream agent-design patterns flagged for HAL's
later inspection. Nothing here is admitted, sealed, or promoted. HAL pulls,
reducer decides, ledger records.

Scope: `experiments/helen_mvp_kernel/` only. Off-limits paths untouched.

---

## ITEM-001 — Persistent cross-turn `/goal` loop (Hermes / Ralph pattern)

**Source**
- `NousResearch/hermes-agent` PR #18262 (merged)
- Inspired by Codex CLI 0.128.0 `/goal` (Eric Traut, Pyright/Codex team)

**Pattern (invariants to keep, code to ignore)**
1. Goal persists in session state.
2. Continuation is a normal user-role input (no system-prompt mutation).
3. Judge call after each response decides done / continue.
4. Judge failure fails OPEN (continue); turn budget is the real backstop.
5. Any real user message preempts the loop automatically.
6. `max_turns` default = 20.
7. Setting a new goal mid-run requires explicit stop (no racing two loops).

**HELEN-native shape (proposal, not admitted)**

Command name candidate: `/ralph goal` (over `/helen-goal` — keeps the
Ralph-loop lineage explicit).

Schema sketch:
```json
{
  "type": "PERSISTENT_GOAL",
  "goal": "...",
  "status": "active | paused | done | exhausted",
  "turns_used": 0,
  "max_turns": 20,
  "judge": "goal_satisfied",
  "authority": false
}
```

**Constitutional constraint (non-negotiable)**

The goal loop must remain **non-sovereign**:

```
Goal loop may PROPOSE.
Judge may CONTINUE.
Reducer still DECIDES.
Ledger still requires RECEIPTS.

/goal ≠ authority
/goal = persistence of intention
```

Implication: every continuation turn that touches a sovereign surface still
goes through `tools/helen_say.py` → `tools/ndjson_writer.py`. The judge
verdict is a non-sovereign signal, never a SHIP/NO_SHIP/BLOCK/PASS.

**Roadmap label** (if HAL admits)

```
HELEN_GOAL_LOOP_V1
Persistent cross-turn objective loop inspired by Hermes /goal and the
Ralph loop. Bounded by max_turns, judged by evaluator, preempted by user,
receipted by ledger. NON_SOVEREIGN.
```

**Status:** QUEUED, conditional on HAL pull. Not a proposal. Not admitted.
Not scheduled. Logged for later inspection only.

**Queued:** 2026-05-01
