# Run brief — stabilize HELEN runtime

**Run-id**: `2026-04-20-stabilize-helen-runtime`
**Opened**: 2026-04-20
**Status**: OPEN (as of retrofit; final.md not yet written)
**Lead worker**: `claude_macbook`

## Mission

Eliminate HELEN's cross-device fragmentation. Make one repo the source of truth, one remote the canonical anchor, one local tree per machine the clean receiver. Stop treating "whatever is running" as canon.

## Scope

In-scope:
- Canonicalize the GitHub remote and local SOT tree
- Push all in-flight laptop work so GitHub is current
- Clone cleanly onto the iMac from canonical
- Verify iMac clone runs the canonical test suite
- Document process-level discoveries as durable skills (voice transcript ingestion, signing tiers, run coordination)
- Surface real dependency gaps (e.g., missing `jsonschema`) without patching around them

Out-of-scope for this run:
- Option A runtime port-in (moving `~/.helen/` + worktree runtime code into SOT)
- Launchd plists / process supervision
- Any Higgsfield render with actual credit cost (canon register mismatch flagged twice)
- Migration of the three live worktree processes (`gallant-khayyam`, `practical-mirzakhani`, `nervous-hodgkin`)

## Non-goals

- Renaming the local laptop folder `helen_os_v1` → `helen-conquest` (cosmetic, deferred)
- Updating global `~/.claude/CLAUDE.md` + preflight hook for the rename (separate session)
- Fixing pre-existing SOT bugs unrelated to consolidation (e.g., `oracle_town/state/acg_generate.py:84`)

## Constraints

- Respect the sovereign-path firewall (no writes under `oracle_town/kernel/**`, `helen_os/governance/**`, `helen_os/schemas/**`, `town/ledger_v1*.ndjson`, `mayor_*.json`, `GOVERNANCE/**`)
- Obey `NO RECEIPT = NO CLAIM` — only `tools/helen_say.py` enters the sovereign layer
- Proposer ≠ Validator — coordination artifacts are candidates, not verdicts
- Treat Higgsfield credits as real money; no speculative API submissions

## Success criteria

- Laptop + GitHub + iMac all report the same HEAD commit
- iMac runs the canonical test suite (helen_os/tests/) with <5 environmental failures
- At least one durable skill shipped from the session (target: 2+)
- No unreceipted runtime state changes introduced into the sovereign layer
