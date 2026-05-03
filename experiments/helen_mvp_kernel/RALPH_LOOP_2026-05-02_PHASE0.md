# RALPH_LOOP_2026-05-02_PHASE0 — Research Ralph, math_to_face Phase 0

**Status:** OPEN. Non-sovereign. Research-class.

**Operator authorization 2026-05-02 (HAL verdict):**
```json
{
  "verdict": "CONTINUE",
  "mode": "RESEARCH_RALPH_PHASE0",
  "authorized_scope": "experiments/helen_mvp_kernel/math_to_face_phase0/",
  "blocked_paths": [
    "helen_os/render/",
    "helen_os/schemas/",
    "temple/subsandbox/renders/"
  ],
  "required_invariant": "same input + same seed -> same spectrum hash + same SDE trace hash",
  "forbidden_claims": [
    "RH proof",
    "sovereign admission",
    "image generation",
    "cloud execution",
    "visual identity validation"
  ]
}
```

## Locked statement

```
Research subsandbox only.
No image generation.
No cloud.
No RH claims.
Replay determinism is the only success criterion.
```

## Phase 0 strict defaults

```yaml
N:                 7
primes:            [2, 3, 5, 7, 11, 13, 17]
epsilon:           0.05
c:                 1.2
fractal_kernel:    exp_neg_abs
phi_sde:
  T:               5.0
  dt:              0.1
  gamma:           0.0
  noise_seed:      0
  noise_mode:      ZERO_NOISE
  qam_projection:  zero       # NOT identity — identity zeroes drift
decimal_precision: 12
scope:             RESEARCH_SUBSANDBOX
sovereign_admitted: false
```

## Constitutional bounds

- All work scoped to `experiments/helen_mvp_kernel/math_to_face_phase0/`
- Schemas drafted in `experiments/helen_mvp_kernel/schemas/` (NOT helen_os/schemas/)
- Runtime outputs in `temple/subsandbox/research/<problem_id>/` (NOT renders/)
- Each epoch emits a 7-field PULL-mode receipt
- Halt on: forbidden-path attempt, hash drift, sovereign-admission boundary

## Goal

Build a stdlib-only, deterministic, hashable Phase 0 receipt loop:

```
m → embedding H(m) = z_0 → φ-SDE trace (zero noise, zero projection) → z_T → receipts
                                ↑
                          H_N spectral diagnostics
                                ↓
                          eigenvalues_hash, λ_min, λ_max, trace, frobenius
```

Success criterion: `same input + same seed → same hashes`, run 3×, all match.

## Epoch plan

| # | Goal | Output |
|---|------|--------|
| 1 | Open this loop log | `RALPH_LOOP_2026-05-02_PHASE0.md` |
| 2 | Draft 3 receipt schemas | `schemas/{h_n_spectral,phi_sde_trace,research_run}_receipt_v1.json` |
| 3 | Draft MAYOR precursor packet | `MAYOR_TASK_PACKET_PHASE0_SCHEMAS.md` (NOT SUBMITTED) |
| 4 | `embedding.py` — H(p) sin/cos | 512-dim from single prime |
| 5 | `h_n.py` — H_N + Jacobi eigensolver | spectrum diagnostics |
| 6 | `phi_sde_trace.py` — Euler-Maruyama | zero noise + zero projection |
| 7 | `receipts.py` — 3 emitters + SovereignWriteRefused | canonical hashing |
| 8 | `phase0_runner.py` + `fixtures/phase0_prime7.json` | orchestrator |
| 9 | `tests/test_phase0_replay.py` | replay invariant |
| 10 | Run 3×, verify all hashes match | emit `RESEARCH_RUN_RECEIPT_V1` |

## Receipt template (per epoch)

```yaml
epoch:               <n>
carry_forward_state: <what prior epochs left>
hypothesis:          <what this epoch tests>
experiment:          <what was actually built>
metric:              <how success is measured>
failure_mode:        <what would have caused halt>
keep_reject_rule:    <criterion for keeping>
upgrade_path:        <next-epoch consequence>
hal_verdict:         CONTINUE | DONE | BLOCK
```

---

## Epoch receipts

### Epoch 1 — open loop log

```yaml
epoch:               1
carry_forward_state: branch claude/setup-helen-os-node-b4uj8 with Higgsfield Ralph
                     loop committed (E1-E10). Phase 0 design proposal sent and
                     operator approved with strict defaults + qam_projection=zero
                     correction.
hypothesis:          a typed loop log artifact is sufficient to bound a
                     Research Ralph run without touching sovereign paths
experiment:          wrote RALPH_LOOP_2026-05-02_PHASE0.md with HAL verdict,
                     locked statement, strict defaults, bounds, plan
metric:              file exists in experiments/helen_mvp_kernel/, no writes
                     to blocked paths
failure_mode:        write to helen_os/render/, helen_os/schemas/, or
                     temple/subsandbox/renders/ would have halted
keep_reject_rule:    KEEP if file is operator-readable via git pull
upgrade_path:        epoch 2 drafts the 3 receipt schemas this loop emits
hal_verdict:         CONTINUE
```

---

### Epoch 2 — three receipt schemas

```yaml
epoch:               2
carry_forward_state: loop log open with HAL verdict + strict defaults
hypothesis:          three JSON Schema drafts in experiments/.../schemas/
                     can specify the receipt shapes for spectrum, SDE
                     trace, and run-wrapper without touching helen_os/schemas/
experiment:          wrote h_n_spectral_receipt_v1.json (15 required fields,
                     spectral_summary nested object), phi_sde_trace_receipt_v1.json
                     (16 required fields incl. qam_projection enum [zero,
                     identity]), research_run_receipt_v1.json (run-level
                     wrapper binding both with replay_check_hashes object)
metric:              all three are draft-2020-12 valid; additionalProperties:
                     false; scope locked to RESEARCH_SUBSANDBOX (single
                     enum value); sovereign_admitted const false;
                     decimal_precision const 12
failure_mode:        write to helen_os/schemas/ would have been a sovereign
                     mutation
keep_reject_rule:    KEEP if epoch 7 receipts.py can validate against them
upgrade_path:        epoch 3 drafts the precursor packet that proposes
                     promotion to helen_os/schemas/
hal_verdict:         CONTINUE
```

---

### Epoch 3 — MAYOR precursor packet (NOT SUBMITTED)

```yaml
epoch:               3
carry_forward_state: three schema drafts in experiments/.../schemas/
hypothesis:          a precursor MAYOR packet can be drafted and HELD,
                     marked NOT_SUBMITTED + SOVEREIGN_ADMISSION_REQUIRED,
                     so the sovereign-promotion path is documented but
                     not invoked unilaterally by the loop
experiment:          wrote MAYOR_TASK_PACKET_PHASE0_SCHEMAS.md targeting
                     three new files in helen_os/schemas/ + three append
                     entries in helen_os/governance/schema_registry.py;
                     7 acceptance criteria, 4 receipt types, locked
                     "NOT SUBMITTED" header
metric:              packet has all MAYOR_TASK_PACKET_V1 required fields,
                     forbidden_paths complete, hand-off command runnable,
                     status explicitly held
failure_mode:        invoking helen_say.py from within this loop would
                     have crossed the sovereign-admission boundary even
                     if daemon were up — packet is HELD by design
keep_reject_rule:    KEEP if operator can route via helen_say.py later
                     without edits to the packet
upgrade_path:        epoch 4 begins building actual code in
                     experiments/.../math_to_face_phase0/ — no further
                     sovereign-path authorization needed for that work
hal_verdict:         CONTINUE
```

---

(more epochs appended below as they execute)
