# WUL-ORACLE Implementation Roadmap

## Current Status

### ✅ Completed
1. Updated kernel with A00_ATOM primitive (arity 0)
2. Created `src/oracle/` package with:
   - `builders.py` (structured token trees with id/args)
   - `scoring.py` (progress % computation)
   - `shipping.py` (LaTeX/code/text shipment generation)
3. Created `src/superteam/` package structure

### 🔄 In Progress
- Implementing complete specification matching your provided code

### ⏳ Remaining Tasks
1. Complete `src/superteam/improve.py` with your exact specification
2. Update `src/wul/validate.py` to use structured format validation
3. Verify `src/receipt/compute_gap.py` matches specification
4. Ensure `src/mayor/decide.py` has all required functions
5. Create new `wul_oracle_cli.py` with 3-mode flow
6. Test complete end-to-end workflow

## Key Implementation Differences

### Your Specification vs Current System

| Component | Your Spec | Current Impl | Action |
|-----------|-----------|--------------|--------|
| Token Tree Format | `{"id": "R15", "args": [...]}` | `{"D01": {"R15": [...]}}` | ✅ Updated in builders.py |
| Kernel | Flat `primitives` dict with A00_ATOM | Nested discourse/entities/relations | ✅ Updated core_kernel.json |
| WUL Validator | `_validate_node_shape()` | Dict-key based | ⏳ Needs update |
| Architecture | Modular (oracle/, superteam/) | Monolithic emulator file | 🔄 In progress |

## Complete Specification Reference

Your specification provides:

1. **Schemas** (2020-12, deterministic + meta split)
2. **WUL Kernel** (primitives with A00_ATOM for leaves)
3. **Validator** (structured format: id/args/ref)
4. **Receipt Gap** (count HARD unsatisfied obligations)
5. **Mayor Decision** (pure function with MayorInputs)
6. **Oracle Builders** (claim → structured WUL tree)
7. **Superteam Improve** (proposals with % evaluation)
8. **Shipping** (LaTeX/code/text with meta)
9. **CLI** (3-mode interactive flow)

## Next Immediate Steps

###  1. Complete superteam/improve.py

Based on your specification, this module needs:
- `@dataclass Improvement` with title, rationale, new_ledger, new_policies, mayor_percent, delta_percent
- `propose_improvements()` generating proposals with Mayor evaluation
- Support for: adding attestations, fixing kill switches, combined improvements

### 2. Update wul/validate.py

Must support structured token trees:
- Validate `{"id": "...", "args": [...], "ref": "..."}` format
- Check arity against primitives dict
- Enforce ref pattern for leaf nodes
- Support A00_ATOM (0-arity leaves)

### 3. Create wul_oracle_cli.py

Three-mode interactive flow:
```
Mode 1: Test a claim
  → build WUL tree (structured format)
  → validate against kernel
  → build tribunal + policies
  → compute receipt gap
  → Mayor decision

Mode 2: Superteam improve
  → show current blocking
  → generate improvement proposals
  → display Mayor % evaluation
  → apply selected improvement
  → recompute decision

Mode 3: Mayor ship
  → verify SHIP status
  → choose format (latex/code/text)
  → generate shipment artifact
  → save with meta
```

## Testing Strategy

1. **Unit Tests**
   - WUL validator with structured trees
   - Receipt gap computation
   - Mayor decision purity
   - Superteam proposals

2. **Integration Test**
   - Full 1→2→3 flow
   - "example" claim → NO_SHIP → improve → SHIP → shipment

3. **Expected Transcript**
```
> 1
Enter claim: example
Validation PASSED
Receipt gap: 1
Decision: NO_SHIP

> 2
Superteam proposal: Add TOOL_RESULT attestation
Mayor evaluation: 100% expected gap reduction
Apply? y
Updated receipt gap: 0
Updated decision: SHIP

> 3
Choose format: latex
SHIPMENT GENERATED
shipment_sha256=...
```

## POC Factory Integration Points

Once base emulator is complete, integration with POC Factory involves:

1. **Input Contract**: Isotown artifact bundle → attestations_ledger
2. **Tribunal Assembly**: Obligations from briefcase
3. **Mayor Decision**: Pure function of tribunal + ledger + policies
4. **Outcome**: SHIP (certified) or NO_SHIP (rejected with reasons)

## Files to Create/Update

### Create New
- [ ] `src/superteam/improve.py` (your exact spec)
- [ ] `wul_oracle_cli.py` (your exact 3-mode flow)

### Update Existing
- [ ] `src/wul/validate.py` (structured format support)
- [x] `src/wul/core_kernel.json` (primitives with A00_ATOM)
- [ ] Verify `src/receipt/compute_gap.py` (should be OK)
- [ ] Verify `src/mayor/decide.py` (should be OK)

### Already Matching Spec
- [x] `schemas/decision_record.schema.json` (2020-12, invariants)
- [x] `reason_codes.json` (allowlist)
- [x] `src/oracle/builders.py` (structured trees)
- [x] `src/oracle/scoring.py` (progress %)
- [x] `src/oracle/shipping.py` (LaTeX/code/text)

## Decision Point

**Current working emulator** (`wul_oracle_emulator_complete.py`) is operational but uses different format.

**Your specification** provides complete alternative implementation with:
- Structured token trees
- Modular architecture
- Exact transcripts

**Recommendation**: Complete your specification implementation as authoritative version, keep current as reference.

---

**Status**: Implementation in progress - completing modules to match your exact specification
**Last Updated**: 2026-01-17
**Reference**: Your complete code specification provided in latest message
