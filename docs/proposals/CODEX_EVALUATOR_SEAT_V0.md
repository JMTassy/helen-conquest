---
schema: HELEN_PROPOSAL_V1
title: Evaluator seat V0 — provider-neutral blind evaluator; CODEX_EVALUATOR as a deployment binding
authority: false
sovereign: false
canon: false
ledger_effect: none
reducer_required: true
git_stage: no
git_commit: no
claim_status: NO_CLAIM
final: HOLD_FOR_OPERATOR
origin: operator "Build Codex Evaluator" 2026-10-09, under the constraint that the seat is a binding, not a new organ · branch claude/wonderful-cannon-gua790
---

# Evaluator seat V0

🟣 CLAIM (PROPOSED). Code and tests are 🔵 OBSERVED (149 tests pass). **No provider has been called.** The seat exists; it has not been occupied.

## 1. Interface decision

The stable contract is provider-neutral: an adapter returns text plus the transport facts it observed. The evaluator wraps it: blind input in, G1-shaped outcomes and a partitioned receipt out. `CODEX_EVALUATOR` is the name of one *binding* of that contract — an OpenAI-compatible Responses endpoint plus a key in the environment — and nothing else. No new module, no new authority, no new vocabulary.

| Layer | What it is | Where |
|---|---|---|
| Contract | `Adapter.generate(messages) -> (text, observed)`; `run_blind_evaluation(adapter, blind_path, out_dir)` | `experiments/helen_frontier_v0/evaluator/contract.py` |
| Bindings | `ResponsesAPIAdapter` (OpenAI-compatible), `NullAdapter` (plumbing), `CallableAdapter` (tests) | same file |
| CLI | `run_blind_eval.py --adapter openai\|null --blind … --out …` | `evaluator/` |
| After the fact | `compare_to_oracles.py` joins outcomes with the frozen V1 oracles; separate from the evaluator | `evaluator/` |

## 2. Blindness and fail-closed parsing

- The evaluator accepts only a `*_blind.json`; it asserts the input carries no `expected`; its code never names the oracle files. Tests enforce all three.
- Each oracle is one call with the laws, the vocabulary with semantics, the fixture's `given` and `claim_under_test`, and a strict JSON reply format.
- Parsing is fail-closed: a reply outside the four outcomes, with a non-boolean transition, or with a transition on a non-ADMIT outcome, is recorded as `UNPARSEABLE` with the raw text kept. Nothing is coerced into a verdict.

## 3. Receipt partitions (never merged)

| Block | Content |
|---|---|
| asserted | configured model id, temperature |
| observed | blind-input sha256, hosts contacted, HTTP status and selected response headers per oracle (`openai-model`, `x-request-id`, …), `model` field from the response body, latencies, outcomes sha256, Python version, git HEAD |
| unverifiable | runtime weight identity: UNVERIFIED (the host does not attest executed weights); lineage independence from the oracle author: UNRESOLVED |
| route_diversity | oracle author family `anthropic/claude`; evaluator provider; `provider_differs` boolean; meaning: a different measurement path, not an independent witness |

The `openai-model` response header and the body's `model` field are the only *observed* model identity available over this transport. They are recorded as observed facts about the response, not as proof of which weights ran.

## 4. Deployment preconditions (not capabilities)

| Precondition | State on 2026-10-09 |
|---|---|
| `OPENAI_API_KEY` in the environment | absent; the CLI reports `PRECONDITION_FAILED` and mocks nothing |
| `api.openai.com` allowed by the network policy | refused (CONNECT 403) |
| Codex CLI installed | not installed; not required for the API binding |

A ChatGPT subscription login is an interactive browser OAuth flow; it cannot be completed from a non-interactive cloud session. The API-key path is the one that works here.

## 5. What a first run would produce, and what it would not

Produce: 13 outcomes from a non-Claude route, a partitioned receipt, and a comparison table against the frozen V1 oracles with mismatches listed for blinded adjudication.
Not produce: evidence of independence (lineage unresolved), evidence that any mismatch is the oracle's fault or the evaluator's (adjudication decides), or any admission.

## 6. Status frontier

This update adds one durable interface (the provider-neutral evaluator contract with partitioned receipts) and advances one time-bounded status (CODEX_EVALUATOR: preconditions unmet). Nothing here is `proven`; the clean tree and test counts are implementation evidence only.
