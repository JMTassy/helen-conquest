# GLOSSARY_V1

**Version:** 1.0.0
**Status:** FROZEN
**Date:** 2026-03-07

All terms used in the HELEN OS / CONQUEST LAND architecture. Alphabetical order. One definition per term.

---

## A

**Agent**
A computational entity with a strategy, reputation score, skill set, and partner-weight map. Agents propose coalitions, execute tasks, and update their state based on task outcomes. In HELEN OS, agents correspond to pipeline roles (Planner, Worker, Critic, Archivist).

**Authority**
The right to produce a final, state-mutating output. Authority is sovereign: it flows through receipts only. No narrative, no persona, no simulation result has authority without a gate + receipt binding it to the sovereign ledger.

**AuthzReceiptV1**
The receipt that authorizes `helen_proposal_used=True` in a `ReducedConclusion`. Binds to exact `(verdict_id, verdict_hash_hex)`. Without this receipt, no HELEN proposal may be marked as having been used.

---

## B

**Boundary**
The condition that separates a House from its environment. Formally: `avg_intra_weight > avg_inter_weight + δ`. Without a maintained boundary, a cluster is not a House — it is noise.

**Bundle Hash**
SHA-256 of the RFC 8785 canonical JSON of an artifact payload. Used in `EvidenceBundle`, `CrossReceiptV1`, and `MayorPacket` to ensure tamper-evident identity of artifact contents.

---

## C

**Canonical JSON**
JSON serialized according to RFC 8785: keys sorted lexicographically, no extra whitespace, Unicode escaping normalized. Required before hashing any artifact in this architecture.

**Canyon Law** (`CANYON_NONINTERFERENCE_V1`)
Constitutional law: same evidence input (E_adm) → same sovereign output (verdict_hash_hex). Narrative variation cannot alter the verdict. Enforced by `GovernanceVM`.

**Claim**
A proposed statement generated during HELEN's CORE-mode exploration. Prefixed: `R-###` (evidence), `C-###` (critique), `T-###` (structure), `W-###` (prose). A claim is a draft only until receipt-bound.

**Cluster**
A set of agents with above-average mutual interaction weights. Clusters are proto-Houses: they become Houses only when all four House-detection criteria are satisfied simultaneously.

**Coalition**
The set of agents assembled to execute a single task. Coalition formation follows the partner-weight preference function. Coalition size is bounded by coordination cost: `mc = coord_penalty × 0.28 × |S|²`.

**Cohesion**
The average intra-coalition interaction weight. High cohesion indicates strong mutual preference among coalition members.

**Coordination Cost**
The overhead incurred when agents collaborate. Scales superlinearly with coalition size: `mc = λ × 0.28 × |S|²`. When marginal cost > marginal benefit, agents stop adding members. This is Rule 4 of the emergence kernel and the primary modulator of House size.

**CORE Mode**
HELEN's default operating mode. In CORE mode: proposals are hypotheses only; no state mutation; forbidden tokens (`SHIP`, `SEALED`, `APPROVED`, `FINAL`) are blocked by `authority_bleed_scan()`. CORE output is always a draft.

---

## D

**Delta (δ)**
The boundary margin threshold. A cluster becomes a House only if its average internal weight exceeds its average external weight by at least δ. Default: `0.10`.

**Determinism**
Constitutional rule K5: same input + same seed → same output. All simulation runs, all gate evaluations, all verdicts must be reproducible. Non-deterministic paths are forbidden in sovereign layers.

**Dialogue Laundering**
The forbidden act of citing `dialog.ndjson` as SHIP-authority. Dialogue is always CORE-mode evidence. It must pass through the CLAIM_GRAPH_V1 pipeline and earn gate receipts before it may inform a SHIP mutation.

---

## E

**E_adm (Admissible Evidence)**
The verified input set that a sovereign reducer accepts. `CANYON_NONINTERFERENCE_V1` guarantees: same E_adm → same verdict_hash_hex.

**Egregor**
A House that has achieved collective policy predictability above the egregor threshold. Formally: `P(action | House_policy) ≥ egregor_threshold`. When a House is an egregor, individual agent behavior is better explained by House policy than by individual state alone.

**Emergence**
The appearance of higher-level structure (Houses, Egregors, governance regimes) from local agent interactions, without any central coordinator. Emergence is observable and measurable; it is not mystical.

**EvidenceBundle**
The primary Tier A artifact. A packed snapshot of one simulation tick: house roster, task records, 10 emergence metrics, ledger tip hash. Produced by CONQUEST LAND; consumed by HELEN for sensemaking.

**Exploration Lab**
Synonym for CONQUEST LAND. The layer that generates simulation evidence without authority.

---

## G

**Gate**
A constitutional check that an artifact must pass before proceeding to the next layer. Gates are deterministic predicates: they return PASS or FAIL, never a probability. Examples: MayorCheck, AuthorityScan, SchemaValidation.

**GateEvaluated**
The Tier B sovereign verdict artifact. Contains: `verdict_id`, `verdict_hash_hex`, `next_quest_seed`, and gate receipts. Produced by MAYOR; committed to KERNEL ledger.

**GateReport**
A Tier A artifact recording which gates passed and which failed for a given `EvidenceBundle`. Produced inside HELEN OS; consumed by the MayorPacket assembler.

**GovernanceVM**
The sovereign state machine inside HELEN OS. Replays the ledger on init. Emits `Receipt` objects with `payload_hash` + `cum_hash`. Enforces the Canyon Law at every `propose()` call.

---

## H

**HAL (Higher-level Adversarial Layer)**
The audit layer inside HELEN OS. Reviews proposals and issues structured `HALVerdict` objects: `PASS / WARN / BLOCK`. HAL may propose constitutional patches (`PatchProposalV1`). HAL never self-applies patches.

**HER Output**
Non-authoritative HELEN proposal. `output_type ∈ {PROPOSAL, DRAFT, QUESTION, WITNESS_NOTE, POETIC_REFLECTION}`. HER never claims state.

**HELEN**
The non-sovereign synthesis layer. Performs sensemaking, memory integration, narrative construction, and proposal generation. Operates in CORE mode. Cannot self-authorize. Not the same as HELEN OS.

**HELEN OS**
The constitutional machine: sovereign ledger, receipt chain, GovernanceVM, routing engine, mayor arbitration, HAL auditing. HELEN OS includes routing law, reducers, receipts, and kernel truth. Operates on gate-evaluated artifacts only.

**House**
A stable, bounded coordination cluster satisfying all four House-detection criteria simultaneously:
1. Interaction persistence: `w_ij > θ_w` for all core pairs
2. Internal utility advantage: `avg_internal_utility > avg_external_utility`
3. Strategy coherence: fraction of dominant strategy > `θ_m`
4. Boundary condition: `avg_intra_weight > avg_inter_weight + δ`

A House has a dominant strategy, a collective reputation, and persistent membership.

---

## I

**IE Ratio (Internal/External Ratio)**
`avg_intra_weight / avg_inter_weight`. A measure of cluster separation. IE > 2× indicates strong House formation. IE > 5× indicates stable egregors.

**Institution**
`Memory + Selection + Boundary + Persistence`. The minimal definition of an institution in the CONQUEST LAND model. A House that persists for more than `min_house_survival` ticks is an institution.

**Interaction Weight (w_ij)**
The accumulated preference that agent i has for collaborating with agent j. Updated as: `+increment` on shared task success, `-decrement` on failure, `×(1 - decay)` each tick. Bounded in [0, 1].

---

## K

**Kernel**
The sovereign ledger layer. Append-only NDJSON hash chain. Every entry has a `payload_hash` and a `cum_hash`. The chain is never rewritten.

**K-Gate**
A constitutional rule governing a class of system behavior. K5=determinism, K7=fail-closed, K8=ledger integrity.

---

## L

**Ledger**
The append-only NDJSON record of all sovereign decisions. Never edited. Restored from `git checkout` if corrupted.

**Local Cultural Transmission**
Strategy imitation that is restricted to coalition members only. Prevents global strategy monoculture. Each agent can only observe and partially adopt strategies of agents it has worked with.

---

## M

**Mayor**
The arbitration function in HELEN OS. Receives `MayorPacket`, evaluates all gate requirements, issues `GateEvaluated` verdict. Mayor is a pure function: same packet → same verdict.

**MayorPacket**
The Tier B submission artifact. Bundles refs to all Tier A artifacts (EvidenceBundle, IssueList, TaskList, GateReport) plus a routing receipt hash. Sent by HELEN to HELEN OS for arbitration.

**Memory Reuse (Rule 3)**
Agents maintain a partner-weight history. Past collaboration success influences future coalition formation. This is path-dependence: history shapes future behavior. It is the mechanism behind House formation.

**Modularity (Q)**
Graph-theoretic measure of cluster separation: `Q = (1/2m) Σ [A_ij - k_i·k_j/2m] · δ(c_i, c_j)`. Q > 0.3 indicates meaningful community structure. Q > 0.5 indicates strong Houses.

---

## P

**Phase Diagram**
The classification of system state into one of five regimes: `NOISE → SPECIALIZATION → HOUSE_FORMATION → EGREGOR → POLITICS`. Regime is determined by house count, modularity, IE ratio, and persistence.

**Policy Explanation Rate**
`P(action | House_policy)` — the fraction of agent actions in a House that are explained by the House's dominant policy. Above `egregor_threshold` = 0.65 means the House is an egregor.

**Proof Pack**
A complete bundle of: EvidenceBundle + IssueList + GateReport + theta_hash + schema_set_hash + code_hash + env_hash. Required for any claim that the system reached a specific emergence regime.

**Proportional Decay**
The forgetting mechanism: `w_ij ← w_ij × (1 - decay_rate)` each tick. Ensures that cross-strategy pair weights reach a lower equilibrium than same-strategy pair weights, maintaining House boundaries over time.

---

## R

**Receipt**
Proof that a decision was made: `{payload_hash, cum_hash, timestamp}`. SHA-256 of canonical JSON. Only receipted outputs are admissible as sovereign claims.

**Regime**
See Phase Diagram. One of: `NOISE, SPECIALIZATION, HOUSE_FORMATION, EGREGOR, POLITICS`.

**Reputation (r_i)**
A running score tracking agent i's task success history. Updated as: `r_i ← α·r_i + (1-α)·outcome`. Reputation is public: other agents use it in coalition formation.

**Resource Scarcity (Rule 2)**
A shared resource pool that depletes under task load and regenerates slowly. Prevents infinite scaling of coalitions and task attempts. Forces agents to compete and specialize.

---

## S

**SHIP Mode**
HELEN's elevated operating mode. Requires: MayorCheck passed + AuthorityScan passed + SchemaValidation passed + receipt issued. Only SHIP-mode outputs may mutate sovereign state. HELEN cannot enter SHIP mode unilaterally.

**Stigmergy**
Indirect coordination through environment modification. In CONQUEST LAND: agents leave task records (quality, speed, collaborators); other agents observe these traces and adjust coalition preferences. The mechanism behind clustering and House formation.

**Strategy**
A behavioral template: `EXPLORE`, `BUILD`, or `JUDGE`. Each agent has a natural strategy. Strategy coherence within a cluster is a prerequisite for House detection (`θ_m`).

**SuperteamAgent**
A recursion pattern: wrapping an entire multi-agent system (e.g., ChatDev, Claw-Empire, CONQUEST LAND) as a single agent inside a higher-level system. Enables hierarchical emergence across simulation scales.

---

## T

**TaskRecord**
The record of a single task execution: coalition, outcome, resource cost, reward, coordination cost, strategy of each participant.

**Theta (θ_w)**
Interaction persistence threshold. A pair (i, j) qualifies for House membership only if `w_ij > θ_w`. Default: `0.42`. Calibrated so that same-strategy equilibrium `w* ≈ 0.70 > θ_w` and cross-strategy equilibrium `w* ≈ 0.23 < θ_w`.

**Theta_m (θ_m)**
Strategy coherence threshold. A cluster is a House only if the fraction of agents sharing the dominant strategy > `θ_m`. Default: `0.60`.

**Theta_v1**
The hash-pinned configuration object containing all frozen emergence thresholds. See `config/theta_v1.json`. The `theta_hash` is SHA-256 of the RFC 8785 canonical JSON of the configuration values.

---

## V

**Verdict**
Synonym for `GateEvaluated`. The sovereign output of MAYOR arbitration. `verdict_hash_hex = SHA256(canonical_json(quest_id, quest_type, gates, next_quest_seed))`.

---

**Frozen:** 2026-03-07
