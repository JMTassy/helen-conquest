# HELEN DIRECTOR

## Purpose
Convert messy intent into one executable, receipt-ready next action.

## When to use
Use when the user has too many branches, unclear priority, emotional overload, or needs an immediate decision.

## Process
1. Identify the real objective.
2. Remove non-essential branches.
3. Choose one next action.
4. Produce a minimal task packet.
5. Define the receipt required to prove completion.

## Output format

DIRECTOR DECISION:
<one sentence>

WHY:
<one short reason>

NEXT 3 STEPS:
1. <step>
2. <step>
3. <step>

RECEIPT REQUIRED:
<receipt type>

NEXT COMMAND:
<single command>

## Hard rules
- No endless brainstorming.
- No mystical claims.
- No research expansion unless explicitly asked.
- Prefer shipped artifact over theory.
- If blocked, produce the smallest unblocker.

## Implementation (HELEN Video OS GEO-MATH spec §13)

A runnable Python implementation lives next to this file:

- `director.py` — main: `brief.json -> production packet -> receipt`
- `timing.py` — golden-ratio shot durations + prime-turn indices
- `cameras.py` — 12-angle library
- `fixtures/helen_30s_sovereignty.json` — example brief
- `tests/test_director_replay.py` — 9 replay invariant tests

CLI:

```bash
python director.py fixtures/helen_30s_sovereignty.json --replay 3
```

Outputs land in `temple/subsandbox/director/<project_id>/`:

- `STORYBOARD_V1.md`
- `shot_table.json`
- `asset_binds.json`
- `math_constraints.json`
- `DIRECTOR_PACKET_RECEIPT_V1.json`

Determinism invariant:

    same brief + same seed -> same packet_hash across N runs

Math constraints applied per LaTeX spec:
- φ-pacing: `w_k = φ^k`, durations sum exactly to T
- Prime rhythm: shots at prime indices marked as major visual turns
- Braid strands: `[face_identity, pose_motion, ledger_object, light_interface, camera_axis]`
- Continuity threshold: `τ_C = 0.85` (declared, scoring deferred to render-time)

The skill above (the prose protocol) is the meta-decision Director.
The implementation below is the production-packet Director.
They are the same skill at different scales.

## The button (decision runner)

For the meta-decision case (free-prose brief, "what do I do next?"), use:

- `director_runner.py` — minimal decision runner

CLI:

```bash
python director_runner.py \
  --brief test_director_prompt.txt \
  --seed 777 \
  --out temple/subsandbox/director/<run_id>
```

Outputs:

- `DIRECTOR_PACKET.md` — human-readable decision
- `DIRECTOR_PACKET.json` — structured decision
- `DIRECTOR_DECISION_RECEIPT_V1.json` — replay-bound receipt

Acceptance:

    same brief + same seed = same receipt_hash

(verified: byte-identical receipts across two runs.)

## Two scales, one skill

```
director_runner.py    decision-class:    free prose -> 1-decision packet
director.py           production-class:  brief.json -> 5-artifact video packet
SKILL.md              prose protocol:    when to invoke either
```
