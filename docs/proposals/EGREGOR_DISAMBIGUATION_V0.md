---
schema: HELEN_PROPOSAL_V1
title: EGREGOR Disambiguation V0 — three names, three repos, one frontier still proposed
authority: false
sovereign: false
canon: false
ledger_effect: none
reducer_required: true
git_stage: no
git_commit: no
claim_status: NO_CLAIM
final: HOLD_FOR_OPERATOR
origin: session 2026-10-04 → 2026-10-07 · branch claude/wonderful-cannon-gua790 · operator mandate "terminer la désambiguïsation avant FRONTIER"
---

# EGREGOR Disambiguation V0

No global banner. Every line below carries its own qualification:
🔵 OBSERVED = file read in this session, with repo, path and commit · 🟣 CLAIM (PROPOSED) = named and specified in conversation, no code anywhere.

## 0. Three surfaces, three evidence levels

| Surface | Established state |
|---|---|
| `JMTassy/helen-conquest` @ `claude/wonderful-cannon-gua790` (base `main@997aa50`) | Two commits (`5ac788f`, `3056868`). Both diffs re-read and their controls re-tested in this session (§4). |
| `JMTassy/helen-os` @ `51a4109f` (2026-10-06, "ops: add cost-aware cognition discipline") | Cost rule verified in `AGENTS.md`; no code binding anywhere (§5). Read-only shallow clone. |
| External scheduler | Cadence reduction and pauses applied by the operator; not represented in either repo. |

## 1. The three senses

| Qualified name | Repo @ commit | Meaning | Qualification |
|---|---|---|---|
| **CONQUEST.EGREGOR** | helen-conquest @ `997aa50` | Emergence regime of CONQUEST LAND. A House whose policy predicts member action: `P(action \| House_policy) ≥ 0.65`. Regime ladder `NOISE → SPECIALIZATION → HOUSE_FORMATION → EGREGOR → POLITICS`. | 🔵 OBSERVED — `docs/architecture/GLOSSARY_V1.md` L80–81, L187 · `docs/architecture/EMERGENCE_MODEL_V1.md` §5.7 L181–194 · `conquest_emergence_engine.py` L5, L21–23, L58–67 |
| **HELENSH.EGREGOR** | helen-os @ `51a4109f` | Multi-LLM routing mesh (task → "street" → model chain with fallbacks) plus a governed multi-agent coding pipeline (architect / coder / reviewer / tester roles, retries, receipt chain, `authority` always False). | 🔵 OBSERVED for the three test files (§2, read). Modules `helensh/egregor/{registry,router,executor,mesh,pipeline,roles}.py` are 🔵 OBSERVED as *present and imported* (directory listing + import lines); their bodies were **not** read — behaviour below is inferred from test assertions only. |
| **HELEN.FRONTIER** | none | Keeper of a frontier Q_t of unresolved discriminations D_i = (H+, H−, x*, E+, E−, W, status, scope, provenance). | 🟣 CLAIM (PROPOSED). Zero occurrences of `FRONTIER` in either repo before this branch. The prototype in `experiments/helen_frontier_v0/` is experimental and proves only the local properties named in its README. |

No implementation link exists between the three. Earlier memos used the first two names to speak about the third.

## 2. Inventory of the three `helen-os` EGREGOR test files (🔵 OBSERVED, read)

| Path | Imports | Behaviour actually tested | Sample assertions | Sense |
|---|---|---|---|---|
| `tests/test_egregor_v0.py` (310 lines) | `helensh.egregor.registry`, `helensh.egregor.router.classify`, `helensh.egregor.executor.{run_task, run_task_receipted, hal_review}`, `helensh.court.CourtLedger` | Task text routes to a street (`code` / `reason` / `chat` / `fast`); fallback to second model when HAL rejects; full rejection returns clean failure; registry has four streets; `hal_review` rejects empty / short / whitespace / None; determinism of routing; attempt traces; receipts written to CourtLedger with chain integrity. All Ollama calls monkeypatched. | `result["street"] == "code"` · `result["approved"] is True` · `result["model"] == "qwen2.5-coder:7b"` · `len(result["attempts"]) == 2` · `result["approved"] is False` | HELENSH routing + HAL review |
| `tests/test_egregor.py` (844 lines) | `helensh.egregor.pipeline`, `helensh.egregor.roles`, `helensh.agents.hal_reviewer`, `helensh.adapters.ollama.OllamaError`, `helensh.kernel.init_session` | Frozen dataclasses `SubTask` / `PhaseResult` / `CodeUnit` / `EgregorSession`; subtask parsing (max 10); code extraction; phase receipts hash-chained from `EGREGOR_GENESIS`; roles have models + fallbacks; happy path; reviewer rejection → retry; validator score below threshold → retry; max retries; invariants E1 authority False on every result and receipt, E2 chain integrity, E7 deterministic session hash, E8 base state not mutated, E10 all-Ollama-error still yields a session; tamper detection. Mocked Ollama. | `pr.authority is False` · `st.dependencies == (2, 3)` · `cu.approved is True` · `session.session_hash == "abc"` | HELENSH coding pipeline |
| `tests/test_egregor_mesh.py` (522 lines) | `helensh.egregor.mesh` | Classifier maps mode / keywords to streets (`CODE`, `REASONING`, `RESEARCH`, `TEMPLE`, `FAST`, `HEAVY`, `ORACLE_MODE`); street registry complete, each with models and fallback, consensus streets have 3 models; `MeshResult.authority` cannot be True; in-character instant fallbacks that never claim authority; mocked `mesh_call` routing and fallback chain; consensus; available-model introspection; non-sovereignty on every path. | `classify_task("hello world", mode="temple") == "TEMPLE"` · `classify_task("tldr this") == "FAST"` | HELENSH model mesh |

Conclusion: none of the 170-odd tests concerns an emergence regime, a predictive threshold, Houses, or a discrimination frontier. HELENSH.EGREGOR is a third, distinct sense. Its tests do establish two things worth keeping in view for FRONTIER: `authority` is a hard False everywhere, and base state isolation (E8) is already an invariant in that codebase.

## 3. Cost rule (🔵 OBSERVED in helen-os only)

`helen-os/AGENTS.md` @ `51a4109f`, section "Cost-aware cognition and recurring loops", L90–110:

```
Scheduler != CognitionTrigger
NewEvidence AND DecisionRelevant AND Unresolved AND Testable AND NOT Duplicate
```

Operational defaults there are qualitative: cheapest delta check first; retrieve prior receipts before re-deriving; `NO_CHANGE` / `NO_PROGRESS` then stop; no exhaustive rescan to compensate a missing receipt unless asked; at most one expensive discriminator per bounded pass; no automatic retry; a null run never spawns a swarm; `ReasoningTrace != AuditTrace`.

Not present in either repo: the predicate as code; any call site consulting it; the numeric caps (2–4 searches, 2–3 deep reads) — those live only in the external scheduler's instructions.

Exact formulation retained: **policy versioned in helen-os; automatic application not demonstrated.** `experiments/helen_frontier_v0/cost_gate.py` re-expresses the predicate as a strict-boolean evaluator of a *declaration*; it does not demonstrate binding either, and its README says so.

## 4. Re-verification of the two pushed diffs (this session)

**`3056868` — scanner fixture reworded.** Risk: weakening the fixture. Checks run:
- The fixture doc with fences intact → scanner yields 0 findings (the property under test, unchanged).
- The same doc with fences and blockquote markers stripped → 2 `risk_marker` findings. The fenced content still carries real crossings; the fixture is not hollow.
- A temporary untracked file containing a genuine `open("town/ledger_v1.ndjson", "a")` → `kernel_guard.sh` reports `[VIOLATION] RULE 1`. Removed → `[PASS] 0 violations`. The guard still detects the real forbidden case. Intent of both test and guard preserved.

**`5ac788f` — E58 wording + feed regeneration.** Risk: turning regeneration into an acceptance signal. Checks run:
- The E58 entry in the regenerated feed renders `admission: "FORBIDDEN"`, `authority: false`, `mark: null`, `recommended_action: "?"` (field absent in packet). Feed header: `NON_SOVEREIGN · authority=false · ledger_effect=none · NPC carries ⊬ admits`.
- E58 remains **REJECTED** by `autoresearch_policy.validate_packet` (4 missing fields, `sovereign` not a boolean, `finding_type: gap` outside enum). Identical before and after the one-word change. Regeneration changed display, not status.
- The UI test `test_no_ui_text_claims_admission` is unchanged and would still fail on any `IS ADMITTED` text in the feed.

Separate read-only audit of the whole outbox: `docs/proposals/AUTORESEARCH_OUTBOX_POLICY_AUDIT_2026_10_07.md` (117 packets · 31 valid · 86 rejected).

## 5. What this note does not establish

- Any implementation of HELEN.FRONTIER beyond the experimental package.
- Any cognitive contribution, independence of contributions, economy, or emergence. Those require experiments that measure them (R0′ replay noise, annotated equivalence sets for T8-strong, a real bounded dossier with and without the frontier at comparable budget).
- The bodies of the `helensh/egregor/*` modules (not read).

## 6. Decisions left to the operator

PR for `claude/wonderful-cannon-gua790`; whether FRONTIER proceeds past v0; whether the 86 rejected outbox packets are migrated, archived, or left as historical traces.

## Errata — 2026-10-08 (appended, original lines left as written)

Raised by G5_JESTER, confirmed by HAL_OPUS (swarm v0, commit 60fe734):

- §0, "Cost rule **verified** in `AGENTS.md`": overclaim. The text was *located* at `helen-os@51a4109f` L90–110. Its application is not demonstrated anywhere. Read "located", not "verified".
- §2, "Its tests do **establish** two things … base state isolation (E8) is **already an invariant** in that codebase": overclaim. The three test files were *read*, not run, and `helen-os` is not in this checkout. Read "the test files assert", not "establish".
