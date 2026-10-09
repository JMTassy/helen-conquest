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
| `fixtures/jester_riemann_fixtures_v1.json` | Superseding version after swarm v0: L1–L3 reworded, N1 null semantics added, F7 split (13 oracles), F4a/F5b/F6/F9 corrected, V0 kept frozen. |
| `fixtures/jester_riemann_fixtures_v0.json` | Machine-readable twin of `docs/proposals/HELEN_JESTER_RIEMANN_FIXTURES_V0.md`: 3 kept laws, 5 revised, 6 invalidated, 9 fixtures with frozen oracles. |
| `dedup_probe.py` | Cheap-rejection tiers of the cost rule measured on the real outbox: exact, structural (template-aware), lexical; optional `embedding` tier (google/embeddinggemma-2, text-only, CPU, float32) once the network policy allows `huggingface.co` + `cdn-lfs.huggingface.co`. Emits `DEDUP_PROBE_RECEIPT_V0` into `receipts/`. |
| `receipts/` | Probe receipts (authority=false) and the manual-review note. |
| `prereg/` | Preregistered G2 embedding probe: protocol JSON, blind pairs (no labels), runner (needs network), frozen scorer. No score exists yet. |
| `tests/` | The six properties below, plus T7 against the real reducer. |

## What each test proves — and only that

| Test file | Property name | Proves | Does not prove |
|---|---|---|---|
| `test_structural_validation.py` | structural validation | fields, types, closed property sets, `authority=false` enforced | that any D_i is meaningful |
| `test_cost_gate.py` | cost predicate | strict booleans, non-empty evidence, fail-closed on malformation | that evidence is true, that a model call was gated, that credits were saved |
| `test_declared_dedup.py` | declared deduplication · rename invariance | same declared id under three producers → one group; same producers, different ids → distinct groups; bijective renaming → identical signature | semantic equivalence of differently worded distinctions; independence of contributions |
| `test_fixture_freeze_v1.py` | fixture freeze V1 | V1 digest frozen, V0 still frozen and referenced by supersedes, 13 oracles, blind export carries no outcome word or hint field | that any oracle is right |
| `test_prereg_g2.py` | preregistration freeze | protocol+scorer+runner digest frozen; blind pairs carry no label; runner never names the labelled file; scorer rule verified on synthetic scores | anything about embeddings |
| `test_fixture_freeze.py` | fixture freeze | canonical digest of the oracle file equals the one frozen at introduction; every oracle in vocabulary; ΔX only on ADMIT | that any oracle is right; nothing is evaluated |
| `test_dedup_probe.py` | cheap-rejection tiers | exact/structural/lexical behave as specified on synthetic packets; receipts carry authority=false | that any flagged pair is a real duplicate |
| `test_t7_reducer_reject_isolation.py` | T7 (local) | on the real `reduce_promotion_packet`, REJECTED leaves packet, state, cwd and the sovereign ledger file byte-identical; no new grant | collective intelligence; anything about the daemon path that *applies* decisions |

Run: `.venv/bin/pytest experiments/helen_frontier_v0/tests -q` (not part of `make test`).
