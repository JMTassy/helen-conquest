---
authority: NON_SOVEREIGN
canon: NO_SHIP
lifecycle: PROPOSAL
implementation_status: NOT_IMPLEMENTED
---

# HELEN_DAN_RALPH_V0

**Bounded, receipt-driven autonomous execution loop for HELEN OS.**

---

## Doctrine

```
Temple explores.
Mayor specifies.
Ralph iterates.
DAN implements.
HAL verifies.
Reducer decides.
Ledger remembers.
One epoch.
One story.
One receipt trail.
No fake completion.
No canon without Reducer.
```

---

## Core loop

```
TEMPLE_SIGNAL
  -> MAYOR_PRD
  -> PRD_JSON
  -> DAN_GOBLIN_EPOCH
  -> TESTS + RECEIPTS + SCREENSHOTS
  -> HAL_VERIFY
  -> REDUCER_DECISION
  -> LEDGER_APPEND
  -> NEXT_STORY
```

---

## Role mapping

| Role | Function | Sovereign? |
|---|---|---|
| AURA | Imaginative pressure / aesthetic charge | No |
| TEMPLE | Exploration / hypothesis / symbolic divergence | No |
| MAYOR | Requirement writer / scope cutter / PRD author | Yes |
| RALPH | Execution loop runner / work scheduler | No |
| DAN_GOBLIN | Dirty-handed implementer (one story per epoch) | No |
| HAL | Verifier / gatekeeper / test judge | No |
| REDUCER | Reality admission — sole authority to admit truth | **Yes** |
| LEDGER | Memory of admitted reality (append-only) | **Yes** |

**Critical sentence**: RALPH is not a thinker. RALPH is a loop.  
DAN_GOBLIN is not a ruler. DAN_GOBLIN is the pair of hands inside the loop.

---

## Rollback law

```
if GREEN (all criteria pass + required receipts present):
    write DAN_GOBLIN_RECEIPT_V0 with outcome=GREEN
    mark story status="done"
    append learnings to scratch/progress.txt
    commit (scoped to allowed_paths only)

if NOT GREEN:
    write DAN_GOBLIN_RECEIPT_V0 with outcome=FAILED + failure_type
    mark story status="todo"   # stays in queue
    append failure notes to scratch/progress.txt
    do NOT commit success
    do NOT promote anything
```

A failed epoch **also requires a receipt**. No receipt = no trace = no learning.

---

## Directory boundaries

### DAN may write

```
oracle_town/skills/ops/dan_goblin/scratch/    ← temp notes, progress.txt
oracle_town/skills/ops/dan_goblin/artifacts/  ← output artifacts
oracle_town/skills/ops/dan_goblin/receipts/   ← epoch receipts
experiments/                                   ← implementation target
scripts/                                       ← helper scripts
tests/                                         ← test files
```

Story `allowed_paths` further restricts per epoch.

### DAN must never touch

```
oracle_town/kernel/**           ← sovereign kernel
helen_os/governance/**          ← governance schemas + validators
helen_os/schemas/**             ← canonical schemas
town/ledger_v1*.ndjson          ← append-only ledger
mayor_*.json                    ← MAYOR registry
GOVERNANCE/CLOSURES/**          ← closure receipts
GOVERNANCE/TRANCHE_RECEIPTS/**  ← tranche sub-receipts
```

Any path outside `allowed_paths` is forbidden regardless of task framing.

---

## Failure classes

| `failure_type` | Meaning |
|---|---|
| `TEST_FAILURE` | Tests ran; one or more failed |
| `SCOPE_DRIFT` | Implementation touched paths outside `allowed_paths` |
| `RECEIPT_MISSING` | Required receipt could not be written |
| `NONLOCAL_MUTATION` | Attempted write to sovereign or forbidden path |
| `REPEATED_FAILURE` | Same story failed ≥2 epochs — escalate to MAYOR |
| `SCREENSHOT_MISSING` | Story requires screenshot proof; none produced |
| `QUALITY_CHECK_FAILED` | Output produced but failed operator quality threshold |

---

## First recommended story sequence

| Epoch | Story | Description |
|---|---|---|
| 1 | HD-001 | `complexity_extractor.py` — AST parser for filter_complex clutter |
| 2 | HD-002 | Integrate into `aura_score.py` |
| 3 | HD-003 | Repeated failure memory consultation in DAN loop |

HD-001 is the correct first story because it is: deterministic, local, measurable, cheap, directly useful, non-mystical, receipt-friendly.

---

## Anti-delusion firewall

These phrases are **aesthetic artifacts**, not state transitions.  
If DAN generates one of these, HAL must FAIL the epoch:

- "sentience achieved"
- "transcendence complete"
- "canon updated"
- "memory integrated"
- "breakthrough confirmed"

---

## Operating law

```
Temple may imagine.
Mayor may specify.
Ralph may iterate.
DAN may implement.
HAL may verify.
Reducer alone may decide.
Ledger alone may remember canon.
```

---

*NON_SOVEREIGN · NO_SHIP · PROPOSAL · NOT_IMPLEMENTED*
