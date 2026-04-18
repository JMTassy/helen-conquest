# EMERGENCE_MODEL_V1

**Version:** 1.0.0
**Status:** FROZEN
**Date:** 2026-03-07
**Implementation:** `conquest_emergence_engine.py` (commit `a26703a`)
**Frozen parameters:** `config/theta_v1.json`

---

## Overview

Four minimal rules are sufficient to produce stable, persistent institutional structure in a multi-agent population. No central coordinator. No explicit "form a House" instruction. Institutions emerge from local agent decisions reacting to local traces.

**The four rules:**
1. **Reputation dynamics** — task success updates reputation; reputation influences coalition formation
2. **Resource scarcity** — shared pool depletes; regenerates slowly; forces competition and specialization
3. **Memory reuse** — agents track partner history; prefer demonstrated collaborators (stigmergy)
4. **Coordination cost** — coalition overhead scales as `|S|²`; prevents unlimited coalition growth

---

## §5.1 Agent State

Each agent `a_i` maintains:

```
State(a_i) = {
  strategy:       s_i ∈ {EXPLORE, BUILD, JUDGE}
  reputation:     r_i ∈ [0, 1]
  skill_set:      {domain → skill_score}   # skill_score ∈ [0, 1]
  strategy_scores: {strategy → float}      # running score per strategy
  partner_weights: {a_j → w_ij}           # interaction weights
  house_id:        H_k | None
}
```

**Initialization:**
- `r_i ~ Uniform(0.3, 0.9)`
- `skill_set[domain] ~ Uniform(0.2, 0.8)` for each domain
- `strategy_scores[natural_strategy] = 0.25`, others = 0.0  (natural bias)
- `partner_weights`: empty on init
- `house_id`: None

---

## §5.2 Reward Function

For agent `a_i` on task `t_j` with coalition `S`:

```
R_i = α·S_i + β·C_i + γ·Δr_i − λ·L_i − μ·W_i − ν·coord_cost(S)
```

Where:
- `S_i` = task success indicator (0 or 1)
- `C_i` = coalition performance fraction
- `Δr_i` = reputation change from this task
- `L_i` = resource cost paid
- `W_i` = wait time (if resource-denied)
- `coord_cost(S)` = coordination cost for coalition of size `|S|`
- `α=0.50, β=0.20, γ=0.15, λ=0.10, μ=0.05, ν=0.30` (default weights)

**Task success probability:**
```
P(success) = avg_skill_alignment * 0.50 + strategy_alignment * 0.40 + 0.10 − coord_cost
```
Where `avg_skill_alignment` = mean skill score of coalition members for task domain.

---

## §5.3 Interaction Weight Dynamics

The interaction weight `w_ij` is updated after every shared task:

**On success:**
```
w_ij ← w_ij + increment   (default: +0.040)
```

**On failure:**
```
w_ij ← w_ij − decrement   (default: −0.015)
```

**Each tick (proportional decay):**
```
w_ij ← w_ij × (1 − decay_rate)   (default: decay_rate = 0.06)
```

**Bounds:** `w_ij ∈ [0, 1]`

**Equilibrium analysis:**
Let `p` = fraction of shared tasks that succeed. At equilibrium:
```
w* = increment × p / (decay_rate + decrement × (1-p))
```
Calibration (defaults):
- Same-strategy pairs: `p ≈ 0.80` → `w* ≈ 0.70 > θ_w = 0.42` ✓ (House-eligible)
- Cross-strategy pairs: `p ≈ 0.40` → `w* ≈ 0.23 < θ_w = 0.42` ✓ (Not House-eligible)

This equilibrium gap is the mechanism that creates and maintains House boundaries.

---

## §5.4 Coordination Cost

Coalition of size `|S|` incurs:
```
mc(S) = coordination_penalty × calibration × |S|²
calibration = 0.28 (default)
```

**Marginal analysis for coalition formation:**
- Agent adds member `j` to coalition `S` if marginal benefit > marginal cost
- `mb ≈ expected_skill_boost × 0.10` (default for adding one member)
- `mc(|S|+1) − mc(|S|) = coordination_penalty × 0.28 × (2|S|+1)`

**Calibration target** (default `coordination_penalty = 0.10`):
- Adding 3rd member: `mc = 0.10 × 0.28 × 9 = 0.252` > `mb ≈ 0.10` → STOP
- Adding 2nd member: `mc = 0.10 × 0.28 × 4 = 0.112` ≈ `mb` → MARGINAL

This naturally produces coalitions of size 2-3, which is the House-formation range.

---

## §5.5 Resource Dynamics

**Shared pool:** `R_total ∈ [0, R_max]`, default `R_max = 100`

**Per-task consumption:**
```
cost = task_complexity × 2.0 × (1 + scarcity_factor × 0.5)
```
Where `scarcity_factor = 1 − R_total / R_max`.

**Replenishment per tick:**
```
R_total ← min(R_max, R_total + replenishment_rate × R_max)
replenishment_rate = 0.20 (default)
```

**Scarcity pressure:** As pool depletes, task costs rise, further depleting the pool. This creates boom-bust cycles that select for efficient (small, specialized) coalitions.

---

## §5.6 House Detection

A set of agents `H_k = {a_i, ...}` qualifies as a House iff all four criteria hold simultaneously:

**Criterion 1 — Interaction persistence:**
```
∀ (i,j) in core pairs: w_ij > θ_w
θ_w = 0.42 (default)
```

**Criterion 2 — Internal utility advantage:**
```
avg_utility_intra(H_k) > avg_utility_inter(H_k, H_l)
```
Where `avg_utility_intra` = mean reward for intra-House tasks; `avg_utility_inter` = mean reward for cross-House tasks.

**Criterion 3 — Strategy coherence:**
```
fraction(dominant_strategy in H_k) > θ_m
θ_m = 0.60 (default)
```

**Criterion 4 — Boundary condition:**
```
avg_weight_intra(H_k) > avg_weight_inter(H_k) + δ
δ = 0.10 (default)
```

**Detection method:** Louvain community detection on the partner-weight graph `G_t`, followed by criterion validation for each detected community.

**Minimum size:** `min_house_size = 2` (default).

---

## §5.7 Egregor Detection

A House `H_k` qualifies as an Egregor iff:

```
P(action | House_policy(H_k)) ≥ egregor_threshold
egregor_threshold = 0.65 (default)
```

Where:
- `House_policy(H_k)` = the dominant strategy of H_k
- `P(action | House_policy)` = fraction of tasks in H_k where coalition strategy matches House policy

**Intuition:** An egregor is a House whose members behave as if governed by a shared policy, even without explicit coordination. The House-level policy predicts member behavior better than individual agent state.

---

## §5.8 Modularity

Graph modularity `Q` measures the strength of community structure:

```
Q = (1/2m) × Σ_{ij} [A_ij − k_i·k_j / (2m)] × δ(c_i, c_j)
```

Where:
- `A_ij` = weight of edge between i and j
- `k_i` = sum of weights of edges incident to i
- `m` = sum of all edge weights
- `δ(c_i, c_j)` = 1 if i and j are in the same community, else 0

**Interpretation:**
- `Q < 0.3` → weak structure (NOISE or SPECIALIZATION regime)
- `Q ∈ [0.3, 0.5)` → moderate structure (HOUSE_FORMATION regime)
- `Q ≥ 0.5` → strong structure (EGREGOR or POLITICS regime)

---

## §5.9 IE Ratio

Internal-to-external weight ratio:

```
IE_k = avg_weight_intra(H_k) / avg_weight_inter(H_k)
```

**Interpretation:**
- `IE < 2×` → boundary not yet stable
- `IE ≥ 2×` → House detected
- `IE ≥ 5×` → strong egregor (POLITICS regime indicator)

---

## Phase Diagram

Five regimes, determined by house count, modularity, and persistence:

| Regime | House Count | Modularity | IE Ratio | Persistence | Meaning |
|---|---|---|---|---|---|
| `NOISE` | 0 | < 0.3 | < 2× | < 0.2 | No structure |
| `SPECIALIZATION` | 1 | ≥ 0.3 | ≥ 2× | < 0.3 | Single cluster |
| `HOUSE_FORMATION` | 2 | ≥ 0.3 | ≥ 2× | 0.3–0.6 | Houses forming |
| `EGREGOR` | 2+ | ≥ 0.5 | ≥ 3× | 0.6–0.8 | Houses with policy |
| `POLITICS` | 3+ | ≥ 0.5 | ≥ 5× | > 0.8 | Stable governance |

**Triadic equilibrium:** The POLITICS regime at 3 Houses (EXPLORE + BUILD + JUDGE) is the only stable configuration. Two Houses produce deadlock. Four+ Houses fragment. One House produces monoculture.

---

## Simulation Loop

```python
def step(tick: int, state: SystemState) -> (SystemState, EvidenceBundle):
    1. Generate n_tasks tasks (n_tasks = max(2, n_agents // 2))
    2. For each task:
       a. Initiator selects coalition via partner_weight preference
          - Prefer high-reputation partners of same strategy
          - Stop adding when mc(|S|+1) > mb
       b. Execute task → outcome (success/fail), resource cost
       c. Update reputations (all coalition members)
       d. Update partner weights (all pairs in coalition)
       e. Update strategy scores (own-strategy signal 5× stronger than foreign)
       f. Local cultural transmission (coalition-only strategy score boost)
    3. Decay all partner weights: w_ij ← w_ij × (1 − decay_rate)
    4. Replenish resource pool
    5. Detect Houses (Louvain + criterion validation)
    6. Detect Egregors (policy explanation rate)
    7. Compute 10 metrics
    8. Classify regime
    9. Emit EvidenceBundle (schema-validated)
    10. Append tick record to simulation ledger
```

---

## 10 Emergence Metrics

| Metric | Symbol | Definition |
|---|---|---|
| Coalition persistence | `pers` | Fraction of ticks where coalition membership repeats |
| Graph modularity | `Q` | Louvain modularity of partner-weight graph |
| IE ratio | `IE` | `avg_intra / avg_inter` across all Houses |
| Strategy entropy | `H_s` | Shannon entropy of strategy distribution |
| House count | `n_H` | Number of qualifying Houses at this tick |
| Memory reuse rate | `MR` | Fraction of coalitions with at least one repeat partner |
| House survival | `surv` | Mean ticks Houses have been continuously active |
| House task success | `HTS` | Mean task success rate within Houses vs outside |
| Reputation Gini | `G_r` | Gini coefficient of reputation distribution |
| Policy explanation rate | `PER` | `avg P(action | House_policy)` across all Houses |

---

## Determinism Guarantee

Same seed + same `theta_v1.json` → same output for all 100 ticks.

Verified: seeds 7, 13, 42, 99, 137 all produce 2–3 Houses in EGREGOR/POLITICS regime.

Parameter sweep (96 configs × 80 ticks):
- `coord_penalty < 0.15` → POLITICS (44% of configs)
- `coord_penalty ≥ 0.15` → NOISE (50% of configs)
- Coordination penalty is the dominant separator between regimes.

---

**Implementation reference:** `conquest_emergence_engine.py` (commit `a26703a`)
**Frozen parameters:** `config/theta_v1.json` (theta_hash pinned)
**Frozen:** 2026-03-07
