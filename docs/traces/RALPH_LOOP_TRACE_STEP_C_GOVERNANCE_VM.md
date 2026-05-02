---
trace_id: RALPH_LOOP_TRACE_STEP_C_GOVERNANCE_VM
authority: NON_SOVEREIGN
canon: NO_SHIP
lifecycle: IMPLEMENTATION_TRACE
ledger_effect: NONE
kernel_writes: NONE
status: PROPOSAL
captured_on: 2026-05-02
session_id: ralph-loop-step-c-governance-vm-001
ralph_loop:
  R: governance hardening recap (user, 2026-05-02) + repo current state
  A: discrete implementation units (registry / generator / schemas / validators / tests / gate)
  L: kernel deny-list semantics, FROZEN registry header, no-receipt-no-ship
  P: file plan + patches + tests below
  H: NO_CLAIM until red tests fail and green implementation makes them pass under MAYOR-signed verdict
hal_gate:
  allow:
    - proposal trace
    - file plan
    - tests
    - validators
    - generated registry design
  block:
    - live activation claim
    - ledger append
    - MAYOR impersonation
    - policy marked LIVE without receipt
    - duplicate authority matrices maintained by hand
---

# RALPH_LOOP_TRACE — STEP_C — Governance VM Implementation Plan

**NO CLAIM — NO SHIP — IMPLEMENTATION TRACE ONLY**

This document is a **proposal-stage implementation trace**, not an
implementation. It does not mutate the kernel, the registry, the
ledger, or any sovereign state. It does not claim any policy is live.
It identifies the implementation units required to land the governance
hardening described in the user's 2026-05-02 recap, and it specifies
the red/green tests, the acceptance gate, and the risks each unit
faces.

The trace must be reviewed by MAYOR (via a sealed VERDICT) before any
of its units are implemented. The trace itself is `NON_SOVEREIGN`,
`NO_SHIP`, and produces no ledger effect.

---

## 1. Inputs Received

### 1.1 User governance hardening recap (2026-05-02)

Fifteen sections covering: HELEN OS identity as governance VM (§1);
hash substrate with byte-not-string cum-hash correction and canonical
JSON V1 (§2); ledger envelope shape using `type` not `etype` (§3);
kernel-level actor authority matrix (§4); BUILDER / INTEGRATOR /
CHRONOS / HELEN / MAYOR role definitions (§5); `VERDICT_PAYLOAD_V1`
schema (§6); `RECEIPT_PAYLOAD_V1` schema (§7); receipt linkage rule
binding `verdict_id` + `payload_hash` + `cum_hash` (§8); validator
stack (§9); acceptance gate as composite of validators + pytest (§10);
red/green test cases (§11); policy activation flow (§12); HELEN
orchestration state machine (§13); core doctrine (§14); "Generate from
registry" as next brick (§15).

### 1.2 Repo current state (verified 2026-05-02)

| Target file | Status | Notes |
|---|---|---|
| `registries/actors.v1.json` | **EXISTS** | FROZEN header, claims to mirror `formal/LedgerKernel.v` — *does not actually match* (see §8.1). |
| `formal/LedgerKernel.v` | **EXISTS** | 3 actors (HELEN/MAYOR/CHRONOS), 10 event types (USER_MESSAGE/ASSISTANT_MESSAGE/PROPOSAL/VERDICT/REVISION/TERMINATION/MILESTONE/RECEIPT/WUL_SLAB/RHO_CERT), deny-list `authority_ok_event_b`. |
| `tests/test_kernel_authority.py` | **EXISTS** | Tests against the kernel's deny-list fences. RED until kernel_cli enforces `structural_valid_b`. |
| `tools/accept_payload_meta.sh` | **EXISTS** | Acceptance gate script. May need extension. |
| `tools/validate_hash_chain.py` | **EXISTS** | Hash-chain validator. |
| `tools/validate_verdict_payload.py` | **EXISTS** | Verdict payload validator. |
| `tools/validate_receipt_linkage.py` | **EXISTS** | Receipt linkage validator. May need extension to also validate verdict events (per recap §9). |
| `tools/validate_receipt_payload.py` | **MISSING** | Listed in recap §9; not in repo. |
| `tools/generate_authority_matrix.py` | **MISSING** | Recap §15 next brick. |
| `tools/generated/authority_matrix.py` | **MISSING** | Recap §15 next brick. |
| `formal/generated/AuthorityMatrix.v` | **MISSING** | Recap §15 next brick. |
| `docs/generated/AUTHORITY_MATRIX.md` | **MISSING** | Recap §15 next brick. |
| `tests/test_authority_matrix_generation.py` | **MISSING** | Recap §15 next brick. |
| `tests/test_receipt_linkage.py` | **MISSING** (status TBD — pytest discoverable file may exist under different name) | Listed in trace target file list. |
| `helen_os/schemas/verdict_payload.v1.schema.json` | **EXISTS** | Canonical schema location per `CLAUDE.md`. |
| `helen_os/schemas/receipt_payload.v1.schema.json` | **EXISTS** | Canonical schema location. |
| `schemas/verdict_payload.v1.schema.json` (repo root) | **MISSING** | Recap target path differs from canonical location. **See HAL risk §8.4.** |
| `schemas/receipt_payload.v1.schema.json` (repo root) | **MISSING** | Same. |

### 1.3 Open governance disagreement

Three documents disagree on what the actor-authority matrix actually
is. This was named in the previous turn and is not silently resolved
here. See §3.1 below.

---

## 2. Immutable Invariants

These hold across **every** implementation unit. A unit that violates
any invariant must be rejected at the proposal stage, not patched at
the implementation stage.

### 2.1 Kernel sovereignty
- Only `MAYOR` may emit terminal verdicts and receipts that bind to
  ledger position.
- `HELEN` orchestrates, never signs.
- `BUILDER`, `INTEGRATOR`, `CHRONOS` produce artifacts; never append to
  the ledger directly (kernel boundary writer is `tools/ndjson_writer.py`
  per `CLAUDE.md`).

### 2.2 Hash substrate (canonical)
- `payload_hash = SHA256(canon_json(payload))`
- `cum_hash = SHA256("HELEN_CUM_V1" || prev_cum_hash_bytes || payload_hash_bytes)`
- **Bytes, not string concatenation.** Hex must be decoded to bytes
  before cum-hashing unless explicitly frozen otherwise. (User recap §2
  correction; this trace adopts it.)
- `canon_json` = `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")`.

### 2.3 Receipt linkage (no-receipt-no-ship)
For every `SHIP` verdict event, there must exist a later `RECEIPT`
event such that:
- `receipt.payload.verdict_id == verdict.payload.verdict_id`
- `receipt.payload.refs.ref_verdict_payload_hash_hex == verdict_event.payload_hash`
- `receipt.payload.refs.ref_verdict_cum_hash_hex == verdict_event.cum_hash`

A SHIP verdict without a matching receipt is **invalid by acceptance**.

### 2.4 No silent drift
- A registry that claims to mirror a Coq file must actually mirror it,
  or the claim is removed.
- A generator that claims to be deterministic must produce
  byte-identical output across runs.
- A validator that claims to bind A to B must reject A whenever B is
  absent or inconsistent.

### 2.5 Generation discipline
- One registry → many artifacts. No hand-maintained authority tables.
- Each generated file carries the source registry's SHA-256.
- Acceptance gate runs the generator with `--check`; divergence blocks
  merge.

### 2.6 Schema authority
- Canonical schema location is `helen_os/schemas/` per `CLAUDE.md`.
- New schemas land there unless a sovereign decision moves them.
- Validators reference schemas via `helen_os/governance/schema_registry.py`.

---

## 3. Implementation Units

Eight discrete units. Each can be sized, reviewed, and shipped
independently. Order is significant — earlier units are prerequisites
for later ones.

### Unit U1 — Authority registry reconciliation **(BLOCKER)**

The `registries/actors.v1.json` file claims to mirror
`formal/LedgerKernel.v` and does not. Three options for resolution
documented in HAL §8.1. **No subsequent unit can ship until this is
resolved by a MAYOR-signed verdict.**

Deliverable: a `KERNEL_AMENDMENT_V1` payload (or a registry-truncation
patch, depending on resolution path) submitted via the proposal/verdict
flow.

### Unit U2 — Generator and generated artifacts

**Depends on U1.** Once the registry is reconciled with the kernel:

- Create `tools/generate_authority_matrix.py` (deterministic,
  registry-keyed-by-SHA256, supports `--check` for CI).
- Generate `formal/generated/AuthorityMatrix.v`,
  `tools/generated/authority_matrix.py`,
  `docs/generated/AUTHORITY_MATRIX.md`.
- All generated files include source-registry SHA in header.

### Unit U3 — Verdict and receipt schemas (canonical)

Schemas already exist at `helen_os/schemas/verdict_payload.v1.schema.json`
and `helen_os/schemas/receipt_payload.v1.schema.json`. Verify they
match the recap §6 / §7 shapes. Patch as needed. **Do not create
duplicates at repo root `schemas/` — that path is not the canonical
location per `CLAUDE.md`.**

### Unit U4 — Receipt-payload validator **(NEW FILE)**

Create `tools/validate_receipt_payload.py`. Mirrors the structure of
`tools/validate_verdict_payload.py`. Validates each `RECEIPT` event
against `RECEIPT_PAYLOAD_V1` schema, enforcing:
- 64-hex lowercase hashes
- no floats
- correct `receipt_kind`
- required `refs` and `recomputed` blocks present

### Unit U5 — Receipt linkage validator extension

Patch `tools/validate_receipt_linkage.py` so it **also** validates
verdict-event payloads when linking. Per recap §9: *"a receipt
validator that trusts malformed VERDICT events can miss drift or crash
unpredictably."*

Linkage rule (verbatim from §2.3 above):
```
receipt.verdict_id == verdict.verdict_id
receipt.refs.ref_verdict_payload_hash_hex == verdict_event.payload_hash
receipt.refs.ref_verdict_cum_hash_hex == verdict_event.cum_hash
```

### Unit U6 — Acceptance gate composition

Patch `tools/accept_payload_meta.sh` to run, in order:

```bash
python3 tools/validate_hash_chain.py       town/ledger_v1.ndjson
python3 tools/validate_verdict_payload.py  town/ledger_v1.ndjson
python3 tools/validate_receipt_payload.py  town/ledger_v1.ndjson  # U4
python3 tools/validate_receipt_linkage.py  town/ledger_v1.ndjson  # U5 (extended)
python3 tools/generate_authority_matrix.py --check               # U2
pytest -q tests/test_authority_matrix_generation.py
pytest -q tests/test_receipt_linkage.py
```

Any non-zero exit blocks merge/deploy.

### Unit U7 — Red/green test suite

Create `tests/test_authority_matrix_generation.py` (per §5) and
`tests/test_receipt_linkage.py` (per §5). Both start RED (assertions
that the current state fails) and turn GREEN once Units U2 / U4 / U5
land.

### Unit U8 — CI integration

Wire the acceptance gate into `.github/workflows/payload_meta.yml`
(the existing payload/meta acceptance gate workflow). Add a step
that fails on `tools/generate_authority_matrix.py --check` divergence.

---

## 4. Files to Create or Patch

| File | Action | Unit | Notes |
|---|---|---|---|
| `registries/actors.v1.json` | **PATCH** | U1 | Resolve drift with `LedgerKernel.v`. Path A/B/C/A-min decision required. |
| `formal/LedgerKernel.v` | **POSSIBLY PATCH** | U1 | Only if Path B chosen (extend kernel). Requires re-proving theorems. |
| `tools/generate_authority_matrix.py` | CREATE | U2 | Deterministic generator with `--check` mode. |
| `formal/generated/AuthorityMatrix.v` | CREATE (generated) | U2 | Mirror of `actors.v1.json` as Coq predicate. |
| `tools/generated/authority_matrix.py` | CREATE (generated) | U2 | Python allowlists + `authority_ok_event(actor, event_type) -> bool`. |
| `docs/generated/AUTHORITY_MATRIX.md` | CREATE (generated) | U2 | Markdown table with actors × event types and registry SHA in header. |
| `helen_os/schemas/verdict_payload.v1.schema.json` | **VERIFY/PATCH** | U3 | Match recap §6 shape. |
| `helen_os/schemas/receipt_payload.v1.schema.json` | **VERIFY/PATCH** | U3 | Match recap §7 shape. |
| `tools/validate_receipt_payload.py` | CREATE | U4 | New validator. |
| `tools/validate_receipt_linkage.py` | **PATCH** | U5 | Extend to also validate verdict events. |
| `tools/accept_payload_meta.sh` | **PATCH** | U6 | Add U2 `--check` + U4 + U5 (extended) + new pytest invocations. |
| `tests/test_authority_matrix_generation.py` | CREATE | U7 | Red/green agreement tests. |
| `tests/test_receipt_linkage.py` | CREATE | U7 | Red/green linkage tests. |
| `.github/workflows/payload_meta.yml` | **PATCH** | U8 | CI integration. |

**Files explicitly NOT created at repo-root paths:**
- `schemas/verdict_payload.v1.schema.json` — duplicate of canonical.
- `schemas/receipt_payload.v1.schema.json` — duplicate of canonical.

---

## 5. Red Tests (must fail before implementation)

### 5.1 `tests/test_authority_matrix_generation.py`

**RED state expectations (current):**

| Test | Expected before U2 lands | Reason |
|---|---|---|
| `test_generator_runs_check_succeeds` | FAIL with "missing files" | generated/ files don't exist yet |
| `test_python_allowlist_matches_registry` | FAIL with `ImportError` | `tools.generated.authority_matrix` doesn't exist |
| `test_coq_file_present_with_registry_sha` | FAIL with FileNotFoundError | `formal/generated/AuthorityMatrix.v` doesn't exist |
| `test_md_file_present_with_registry_sha` | FAIL with FileNotFoundError | `docs/generated/AUTHORITY_MATRIX.md` doesn't exist |
| `test_actors_match_registry_keys` | FAIL until U2 lands | nothing to compare against |
| `test_event_types_match_registry_keys` | FAIL until U2 lands | nothing to compare against |
| `test_authority_ok_event_kernel_parity` | FAIL until U1 resolves drift | registry vs kernel disagree |

### 5.2 `tests/test_receipt_linkage.py`

**RED-state expectations (cases the validator must reject):**

| Case | Why it must fail |
|---|---|
| SHIP verdict with no later receipt | violates §2.3 receipt-linkage |
| Receipt referencing unknown `verdict_id` | dangling reference |
| Receipt referencing correct `verdict_id` but wrong `ref_verdict_payload_hash_hex` | bound payload changed |
| Receipt referencing correct `verdict_id` and correct `payload_hash` but wrong `ref_verdict_cum_hash_hex` | ledger position changed |
| Receipt with malformed (non-64-hex-lowercase) hashes | format violation |
| VERDICT event with unsorted `reason_codes` | ordering rule violation |
| VERDICT event with duplicate `reason_codes` | uniqueness rule violation |
| VERDICT event with float in `anchors.input_events_length` | "no floats" rule violation |
| Envelope drift: missing `type` / `payload` / `payload_hash` / `cum_hash` | envelope contract violation |

**GREEN state expectations:**
- All red cases above are caught and produce non-zero exit.
- A correctly linked SHIP/RECEIPT pair passes.
- A `WARN`/`PASS`/`BLOCK`/`ABORT` verdict without receipt passes (only `SHIP` requires receipt linkage; this is the recap's framing).

---

## 6. Green Implementation (sketches; expand per unit)

### 6.1 Generator skeleton (U2)

```python
# tools/generate_authority_matrix.py
import argparse, hashlib, json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REGISTRY = REPO / "registries" / "actors.v1.json"
OUT_COQ = REPO / "formal" / "generated" / "AuthorityMatrix.v"
OUT_PY  = REPO / "tools" / "generated" / "authority_matrix.py"
OUT_MD  = REPO / "docs"  / "generated" / "AUTHORITY_MATRIX.md"

def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    sha = hashlib.sha256(canon(reg)).hexdigest()
    outs = {OUT_COQ: render_coq(reg, sha),
            OUT_PY:  render_py(reg, sha),
            OUT_MD:  render_md(reg, sha)}
    bad = []
    for path, content in outs.items():
        if args.check:
            if not path.exists() or path.read_text("utf-8") != content:
                bad.append(str(path))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    if args.check and bad:
        print("DIVERGENCE:", *bad, sep="\n  ")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

`render_coq`, `render_py`, `render_md` produce deterministic strings
keyed off `sha`. All actors and event types are sorted before emission.

### 6.2 Receipt linkage validator extension (U5)

```python
# tools/validate_receipt_linkage.py  (patched)
def validate(ledger_path):
    events = load_events(ledger_path)
    # NEW: validate every VERDICT event's payload before linkage
    for ev in events:
        if ev["type"] == "VERDICT":
            err = validate_verdict_payload_inline(ev["payload"])
            if err:
                fail(f"verdict at seq={ev['seq']} malformed: {err}")
    # Existing linkage logic
    verdicts = [e for e in events if e["type"] == "VERDICT"
                and e["payload"]["decision"]["outcome"] == "SHIP"]
    receipts = {e["payload"]["verdict_id"]: e
                for e in events if e["type"] == "RECEIPT"}
    for v in verdicts:
        vid = v["payload"]["verdict_id"]
        r = receipts.get(vid)
        if r is None:
            fail(f"SHIP verdict {vid} has no matching receipt")
        if r["payload"]["refs"]["ref_verdict_payload_hash_hex"] != v["payload_hash"]:
            fail(f"receipt for {vid}: payload_hash mismatch")
        if r["payload"]["refs"]["ref_verdict_cum_hash_hex"] != v["cum_hash"]:
            fail(f"receipt for {vid}: cum_hash mismatch")
```

### 6.3 Receipt-payload validator (U4)

```python
# tools/validate_receipt_payload.py  (new)
import json, sys
from pathlib import Path
from helen_os.governance.schema_registry import load_schema
import jsonschema

def main(ledger_path):
    schema = load_schema("RECEIPT_PAYLOAD_V1")
    events = [json.loads(l) for l in Path(ledger_path).read_text().splitlines() if l.strip()]
    fails = []
    for ev in events:
        if ev.get("type") != "RECEIPT":
            continue
        try:
            jsonschema.validate(ev["payload"], schema)
        except jsonschema.ValidationError as e:
            fails.append((ev.get("seq"), e.message))
    if fails:
        for seq, msg in fails:
            print(f"seq={seq}: {msg}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
```

---

## 7. Acceptance Gate Update

Patched `tools/accept_payload_meta.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

LEDGER="${1:-town/ledger_v1.ndjson}"

echo "[ACCEPT] hash chain"
python3 tools/validate_hash_chain.py "$LEDGER"

echo "[ACCEPT] verdict payload"
python3 tools/validate_verdict_payload.py "$LEDGER"

echo "[ACCEPT] receipt payload"
python3 tools/validate_receipt_payload.py "$LEDGER"

echo "[ACCEPT] receipt linkage"
python3 tools/validate_receipt_linkage.py "$LEDGER"

echo "[ACCEPT] authority matrix generation parity"
python3 tools/generate_authority_matrix.py --check

echo "[ACCEPT] pytest agreement suite"
pytest -q tests/test_authority_matrix_generation.py tests/test_receipt_linkage.py

echo "[ACCEPT] all gates passed"
```

CI step in `.github/workflows/payload_meta.yml`:
```yaml
- name: Acceptance gate
  run: bash tools/accept_payload_meta.sh town/ledger_v1.ndjson
```

---

## 8. HAL Risks

### 8.1 Authority drift (kernel ↔ registry ↔ recap) — **BLOCKER**

`formal/LedgerKernel.v` (3 actors / 10 event types / deny-list),
`registries/actors.v1.json` (6 actors / 9 event types / allow-list),
and the user's recap §4 (6 actors / different event-type vocabulary)
disagree. The registry's claim to mirror `LedgerKernel.v` is false.

**Resolution paths** (one must be MAYOR-signed before U2 runs):

- **Path A** — truncate the registry to match the kernel. Smallest
  change. Discards `USER/BUILDER/INTEGRATOR` from the registry.
- **Path B** — extend `LedgerKernel.v` to add `USER/BUILDER/INTEGRATOR`
  and rename event types. Requires re-proving theorems and re-running
  the Coq typecheck in `kernel_guard.yml`. Substantial.
- **Path C** — formal `KERNEL_AMENDMENT_V1` proposal that lands the
  recap §4 vocabulary as a sovereign change. Longest, most
  governance-correct.
- **Path A-min** — generate from the registry as-is, generated files
  carry an explicit divergence header, agreement test passes against
  registry only with a known-skip flag for kernel-vs-registry
  comparison until reconciliation.

### 8.2 Schema location drift

User's recap §6/§7 references schemas at repo-root `schemas/`. The
canonical location per `CLAUDE.md` is `helen_os/schemas/`. Creating
duplicates would create a worse drift than not creating them.

**Mitigation:** Unit U3 patches the canonical-location files;
no repo-root duplicates land.

### 8.3 Hash substrate drift (string vs bytes)

User recap §2 explicitly corrects ambiguous string concatenation to
bytes-with-prefix:
```
cum_hash = SHA256("HELEN_CUM_V1" || prev_cum_hash_bytes || payload_hash_bytes)
```

If any existing validator (`tools/validate_hash_chain.py`) currently
uses string concatenation, replaying old ledgers against the new
formula will produce hash mismatches. **Before patching the formula:**
audit existing receipts on the canonical ledger to determine current
behavior; if the kernel has been writing string-concat hashes, the
formula change is itself a kernel amendment.

**Mitigation:** Unit U1's amendment must explicitly call out which
hash formula it freezes. The trace does not assume the recap's
correction is already in force.

### 8.4 Replay-divergence risk on validator extension (U5)

Extending `validate_receipt_linkage.py` to also validate verdict
payloads adds new failure paths. If a previously-accepted ledger now
fails because some old verdict had unsorted `reason_codes`, the
extension constitutes a tightening that retroactively rejects history.

**Mitigation:** before merging U5, run the extended validator against
the production ledger to count newly-failing events. If non-zero,
either (a) tighten only for new events via a `legacy_pre_seq` cutoff,
or (b) backfill receipts/verdicts to comply.

### 8.5 Generation determinism

A non-deterministic generator (e.g. dict iteration order, locale-
dependent formatting) would make `--check` flap. **Mitigation:** sorted
keys, sorted lists, fixed encoding (UTF-8), no timestamps in output,
no environment variables read.

### 8.6 CI workflow churn

Adding the agreement-test pytest invocation to
`payload_meta.yml` increases CI surface. Mitigation: scope path
filters; ensure failures actually block merge per `CLAUDE.md` §
"CI Workflows."

### 8.7 Receipt-without-verdict edge case

Recap §11 lists only failure cases. The trace adds: a `RECEIPT` event
that references no `verdict_id` (or references a `verdict_id` that
does not exist in the ledger) must also fail. **Mitigation:** included
in §5.2 red tests.

---

## 9. MAYOR Review Packet (Draft)

The packet that would be submitted to MAYOR for sealing. **MAYOR has
not seen this; this is a draft.**

```yaml
proposal:
  title: "Governance VM hardening — STEP_C implementation trace"
  proposer: HELEN          # orchestration only; HELEN does not sign
  trace_path: docs/traces/RALPH_LOOP_TRACE_STEP_C_GOVERNANCE_VM.md
  trace_sha256: <computed at proposal time>
  scope:
    units: [U1, U2, U3, U4, U5, U6, U7, U8]
    blocker: U1  # all subsequent units depend on authority drift resolution
  prerequisites:
    - kernel_amendment_required:
        true_for: [Path B, Path C]
        false_for: [Path A, Path A-min]
    - receipts_audit_required:
        for: U5 (replay-divergence risk)
  certificates_offered:
    - DETERMINISM_PROOF        # via U2 generator --check
    - HASH_CHAIN_INTACT        # via U6 acceptance gate
    - RECEIPT_LINKAGE_BOUND    # via U5
  reason_codes_proposed:
    - GOVERNANCE_HARDENING_STEP_C
    - REGISTRY_DRIFT_NAMED_NOT_RESOLVED
  required_fixes_acknowledged:
    - U1 path selection (A / B / C / A-min)
    - U3 schema location confirmation
    - U5 pre-merge ledger replay audit

acceptance:
  outcome_requested: PASS_OF_TRACE
  outcome_NOT_requested:
    - SHIP   # this trace does not implement; it proposes
    - LIVE   # no policy is live until MAYOR seals each unit
  decision_rule:
    - PASS if trace is structurally sound, risks named, blockers identified
    - WARN if MAYOR requires additional risk analysis before unit-by-unit review
    - BLOCK if drift cannot be resolved at this layer
```

**HELEN does not sign this packet.** HELEN composes it and routes to
MAYOR. MAYOR signs (or refuses).

---

## 10. Final Receipt Draft

If MAYOR signs `PASS_OF_TRACE`, the resulting receipt would shape:

```yaml
receipt:
  schema: RECEIPT_PAYLOAD_V1
  receipt_kind: VERDICT_RECEIPT
  receipt_id: <hex64-pinned>
  verdict_id: <hex64-pinned-from-MAYOR's-VERDICT>
  refs:
    ref_verdict_payload_hash_hex: <hex64>
    ref_verdict_cum_hash_hex: <hex64>
    ledger_length_before: <int>
    ledger_length_after: <int>
    prev_cum_hash_hex: <hex64>
    cum_hash_after_hex: <hex64>
  recomputed:
    recomputed_verdict_payload_hash_hex: <hex64>
    recomputed_verdict_cum_hash_hex: <hex64>
    recomputed_input_events_set_root_hex: <hex64>
    recomputed_awards_set_root_hex: <hex64>
  mirrors:
    active_policies_root_after_hex: <hex64>
    awards_set_root_hex: <hex64>
    determinism_proof_root_hex: <hex64>
  attestations:
    canonicalization_ok: true
    determinism_replay_ok: true
    quorum_proof_ok: true
    awards_set_ok: true
```

The receipt **only attests that the trace was reviewed and accepted as
a proposal**. It does **not** attest that any of U1–U8 are implemented
or live. Each unit requires its own VERDICT + RECEIPT pair when it
ships.

---

## Trace Footer

```
authority:        NON_SOVEREIGN
canon:            NO_SHIP
ledger_effect:    NONE
kernel_writes:    NONE
trace_status:     PROPOSAL
mayor_signed:     false
units_proposed:   8 (U1 .. U8)
files_to_create:  6
files_to_patch:   5 (LedgerKernel.v conditional on Path B/C)
red_tests_specd:  2 files, ~16 cases total
risks_named:      7
blocker:          U1 — authority drift (kernel vs registry vs recap)
```

`(NO CLAIM — TEMPLE — IMPLEMENTATION TRACE — RALPH STEP_C)`
