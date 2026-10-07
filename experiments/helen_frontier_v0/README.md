# HELEN.FRONTIER v0 — experimental prototype

Status: PROPOSED · NON_SOVEREIGN · authority=false · ledger_effect=none · NO_SHIP.

Disambiguation first: see `docs/proposals/EGREGOR_DISAMBIGUATION_V0.md`.
This package is HELEN.FRONTIER, not CONQUEST.EGREGOR (emergence regime, this
repo) and not HELENSH.EGREGOR (routing mesh + coding pipeline, `JMTassy/helen-os`).

## Contents

| File | What it is |
|---|---|
| `schemas/DISCRIMINATION_V0.schema.json` | One open discrimination D_i = (H+, H-, x*, E+, E-, W, status, scope, provenance). `additionalProperties: false`, `authority` const false. |
| `discrimination.py` | Fail-closed structural validator + *declared* grouping by `distinction_id`. |
| `cost_gate.py` | Strict-boolean evaluation of the five-conjunct cost rule versioned in helen-os AGENTS.md @ 51a4109f. |
| `tests/` | The four properties below, plus T7 against the real reducer. |

## What each test proves — and only that

| Test file | Property name | Proves | Does not prove |
|---|---|---|---|
| `test_structural_validation.py` | structural validation | fields, types, closed property sets, `authority=false` enforced | that any D_i is meaningful |
| `test_cost_gate.py` | cost predicate | strict booleans, non-empty evidence, fail-closed on malformation | that evidence is true, that a model call was gated, that credits were saved |
| `test_declared_dedup.py` | declared deduplication · rename invariance | same declared id under three producers → one group; same producers, different ids → distinct groups; bijective renaming → identical signature | semantic equivalence of differently worded distinctions; independence of contributions |
| `test_t7_reducer_reject_isolation.py` | T7 (local) | on the real `reduce_promotion_packet`, REJECTED leaves packet, state, cwd and the sovereign ledger file byte-identical; no new grant | collective intelligence; anything about the daemon path that *applies* decisions |

Run: `.venv/bin/pytest experiments/helen_frontier_v0/tests -q` (not part of `make test`).
