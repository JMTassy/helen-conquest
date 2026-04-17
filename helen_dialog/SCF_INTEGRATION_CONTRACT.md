# SCF ↔ Dialogue Box Integration Contract

**Status:** SPECIFICATION (Ready for implementation)
**Authority:** FALSE (Non-sovereign interface)
**Version:** v1.0

---

## Executive Summary

This document defines the **clean interface** between the **Spectral Cognitive Field (SCF)** module and the **Persistent Dialogue Box**.

**Key principle:** SCF is a **filter + telemetry** layer, not a **decision maker**.
- SCF reads non-sovereign data (memory, trace, parameters)
- SCF filters candidate evidence before submission to TownAdapter
- SCF emits telemetry to Channel C (run_trace)
- SCF never claims authority (authority=false always)
- SCF output is **non-binding** (HELEN/MAYOR still decide)

---

## Part I: Data Flow

```
┌─────────────────────────────────────────────────────────┐
│ L1: HELEN (Interface Layer)                             │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │ Candidate Evidence List  │
        │ E_t = [e_1, ..., e_n]  │
        └────────────┬────────────┘
                     │
        ┌────────────▼─────────────────────────┐
        │ SCF (Spectral Cognitive Field)      │
        │ ─────────────────────────────────── │
        │ • Read: M_t (Memory), T_t (Trace)   │
        │ • Filter: E_t by coherence + sym    │
        │ • Emit: telemetry to Channel C      │
        │ • Authority: always FALSE           │
        └────────────┬─────────────────────────┘
                     │
        ┌────────────▼──────────────┐
        │ Filtered Evidence List     │
        │ E'_t ⊆ E_t                │
        │ (still non-sovereign)      │
        └────────────┬───────────────┘
                     │
        ┌────────────▼────────────────────┐
        │ L1.5: MAYOR (Gate Layer)       │
        │ ─────────────────────────────  │
        │ • Schema validation (on E'_t)  │
        │ • Authority binding (verdict)  │
        │ • State mutation (if PASS)     │
        └────────────┬───────────────────┘
                     │
        ┌────────────▼────────────┐
        │ Channel A: Ledger       │
        │ (Only MAYOR writes)     │
        └─────────────────────────┘
```

---

## Part II: SCF Interface Contract

### Input: What SCF Reads

```python
class SCFInput:
    """Non-sovereign data that SCF consumes (read-only)."""

    # From dialogue state (non-authoritative)
    turn: int
    oauth: Dict[str, bool]
    verifier_enabled: bool

    # From MemoryKernel (Channel B)
    memory_facts: List[Dict]      # facts with status: OBSERVED/CONFIRMED/DISPUTED/RETRACTED
    memory_conflicts: List[Dict]  # events marked DISPUTED or RETRACTED

    # From RunTrace (Channel C)
    recent_trace_events: List[Dict]  # telemetry events from last K turns
    trace_anomalies: List[Dict]      # anomaly events

    # Parameters (frozen)
    scf_params: SCFParams  # versioned, deterministic
```

### Output: What SCF Produces

**Channel 1: Filtered Evidence**

```python
class SCFOutput:
    """Non-sovereign output for MAYOR gate."""

    # Filtered evidence (same schema as input, but subset)
    filtered_evidence: List[Dict]  # E'_t ⊆ E_t

    # (Still authority=false, still non-sovereign)
    # MAYOR validates these as usual
```

**Channel 2: Telemetry (Channel C)**

```python
class SCFTelemetry:
    """Diagnostic event, written to dialog.ndjson."""

    event_id: str = f"scf:{turn}"
    type: str = "scf_annotation_v1"  # Schema: scf_annotation_v1.schema.json

    # Deterministic metadata
    scf_version: str = "scf-v0.1"
    params_hash: str = sha256(canon(scf_params))

    # Filtering results
    evidence_in_count: int
    evidence_out_count: int

    # Coherence + symmetry (binned, not float)
    coherence_summary: {"low": int, "medium": int, "high": int}
    symmetry_flags: {"all_pass": bool, "fail_count": int, "fail_reason": str}

    # Tension spectrum (top eigenvalues, fixed-point)
    tension_modes: List[int]  # e.g., [950000, 210000, 45000, ...]

    authority: Literal[False]  # ALWAYS false
```

---

## Part III: Integration Points

### 3.1 Where SCF Fits in Dialogue Loop

**Current flow (without SCF):**
```python
def dialogue_turn(user_input):
    # L1: HELEN generates candidates
    candidates = build_prompt_and_call_llm(user_input)

    # L1.5: MAYOR validates
    verdict = mayor.validate(candidates)

    # Channel A: Append if PASS
    if verdict == "PASS":
        ledger.append(event)
```

**With SCF integrated:**
```python
def dialogue_turn_with_scf(user_input):
    # L1: HELEN generates candidates
    candidates = build_prompt_and_call_llm(user_input)

    # L1.5: SCF filters candidates (optional, non-sovereign)
    scf_input = SCFInput(
        memory=memory_kernel.latest(),
        trace=run_trace.latest(),
        params=scf_params
    )
    filtered_candidates, telemetry = scf.process(candidates, scf_input)

    # Emit SCF telemetry to Channel C
    run_trace.append(telemetry)

    # L1.75: MAYOR validates filtered_candidates (not original candidates)
    verdict = mayor.validate(filtered_candidates)

    # Channel A: Append if PASS
    if verdict == "PASS":
        ledger.append(event)
```

### 3.2 Integration Points in Code

**File:** `helen_dialog_engine.py`

Add hook in `process_turn()`:

```python
def process_turn(self, user_message: str, lmm_response: str) -> Dict[str, Any]:
    # ... existing code ...

    # Parse HELEN + MAYOR response
    helen_text, mayor_dict = self.parse_response(lmm_response)

    # NEW: Filter via SCF (if SCF available)
    if self.scf_engine is not None:  # SCF optional
        scf_input = self._build_scf_input()
        filtered_evidence, scf_telemetry = self.scf_engine.process(
            helen_text, scf_input
        )

        # Append SCF telemetry to Channel C
        self.append_event(scf_telemetry)

        # Use filtered evidence for downstream processing
        helen_text = filtered_evidence  # May be modified
    else:
        scf_telemetry = None

    # ... rest of existing code ...
```

### 3.3 SCF Configuration

SCF is **optional but recommended**. Configuration:

```json
{
  "scf_enabled": true,
  "scf_version": "scf-v0.1",
  "scf_params": {
    "alpha_fp": 1000000,
    "beta_fp": 500000,
    "gamma_fp": 250000,
    "coh_target_fp": 500000,
    "coh_band_fp": 100000,
    "sym_min_fp": 600000,
    "dim": 128,
    "scale_fp": 1000000,
    "version": "scf-v0.1"
  }
}
```

Store in `dialog_state.json`:

```json
{
  "version": "dialogue_state_v1",
  "scf_enabled": true,
  "scf_params_hash": "abc123...",
  ...
}
```

---

## Part IV: Authority Separation (Hard Boundary)

### What SCF CAN Do

✅ Read non-sovereign data (memory, trace)
✅ Compute coherence energy, symmetry scores
✅ Filter evidence by deterministic rules
✅ Emit telemetry (diagnostics, observations)
✅ Rank or prioritize candidates (non-binding)
✅ Suggest attention directions

### What SCF CAN'T Do

❌ Write to Channel A (ledger) directly
❌ Emit authority tokens (SHIP, SEAL, VERDICT, etc.)
❌ Change dialog_state.json (only MAYOR can)
❌ Mutate candidate evidence (only filter)
❌ Make binding decisions (only propose)
❌ Claim consciousness, feeling, or sentience

### Enforcement

Every SCF event must satisfy:

```python
assert scf_event.get("authority") == False
assert "SHIP" not in json.dumps(scf_event)
assert "VERDICT" not in scf_event.get("notes", "")
# ... check other forbidden tokens
```

Schema validation enforces: `"authority": Literal[False]` (const false)

---

## Part V: Determinism & Reproducibility

### Deterministic SCF

SCF is deterministic **given frozen parameters**:

```python
# Frozen at initialization
scf_params_hash = sha256(canon(scf_params))

# Every event includes this hash
scf_telemetry.params_hash = scf_params_hash

# Audit: if params_hash changes, SCF output may differ
```

### Replay Protocol for SCF

```
1. Load dialog.ndjson
2. Load dialog_state.json (including scf_params_hash)
3. Initialize SCF with params matching scf_params_hash
4. For each turn:
   - Extract SCF input (memory, trace, params)
   - Run SCF.process()
   - Verify scf_telemetry.params_hash matches
   - Verify filtered_evidence_hash matches
```

---

## Part VI: Testing & Validation

### Unit Tests (4 tests for SCF integration)

| Test | What | Acceptance |
|------|------|-----------|
| **T5** | SCF determinism | Same input → identical output, identical hash |
| **T6** | Authority ban (SCF) | No authority=true, no forbidden tokens in SCF events |
| **T7** | Filter accuracy | Coherence/symmetry filtering produces expected subset |
| **T8** | Telemetry integrity | scf_telemetry schema valid, params_hash matches |

### Integration Test

```python
def test_scf_dialogue_integration():
    """End-to-end: HELEN → SCF → MAYOR → Ledger"""

    # Setup
    dialogue = DialogueEngine(...)
    scf = SpectralAnalyzer(params)

    # Run turn with SCF enabled
    result = dialogue.process_turn(
        user_msg="test input",
        lmm_response=mock_response,
        scf_engine=scf
    )

    # Verify
    assert result["scf_telemetry"]["authority"] == False
    assert result["scf_telemetry"]["type"] == "scf_annotation_v1"
    assert sha256_schema(result["scf_telemetry"]) matches scf_annotation_v1.schema.json
```

---

## Part VII: Migration Path (SCF Optional)

### Phase 0 (Current): No SCF
- Dialogue box works (T1–T4 passing)
- All evidence flows directly to MAYOR
- Moment detector works (receipt-grade v2)

### Phase 1: SCF Added
- SCF initialized as optional module
- If scf_enabled: filter evidence before MAYOR gate
- Telemetry emitted to Channel C (run_trace)
- All T5–T8 tests passing

### Phase 2: SCF Integrated
- SCF becomes standard layer (always enabled)
- HELEN prompts include SCF diagnostics
- MAYOR verdicts include SCF reason codes
- Dialogue box now depends on SCF

---

## Part VIII: Example Event Sequence

**Turn 5 with SCF:**

```json
{
  "event_id": "dlg:5:user",
  "type": "input",
  "content": "Test message"
}

{
  "event_id": "dlg:5:helen",
  "type": "proposal",
  "content": "[HER] I understand..."
}

{
  "event_id": "scf:5",
  "actor": "scf",
  "type": "scf_annotation_v1",
  "scf_version": "scf-v0.1",
  "params_hash": "abc123...",
  "evidence_in_count": 5,
  "evidence_out_count": 4,
  "coherence_summary": {"low": 0, "medium": 1, "high": 3},
  "symmetry_flags": {"all_pass": true, "fail_count": 0},
  "tension_modes": [950000, 210000, 45000],
  "authority": false
}

{
  "event_id": "dlg:5:mayor",
  "type": "verdict",
  "verdict": "PASS",
  "checks": ["SCHEMA_VALID", "SCF_COHERENCE_OK"],
  "reason_codes": ["SCF_filtered_1", ...]
}
```

---

## Part IX: Glossary

| Term | Meaning |
|------|---------|
| **Channel A** | Sovereign ledger (L) — write-gate only |
| **Channel B** | MemoryKernel (M) — non-sovereign facts |
| **Channel C** | RunTrace (T) — non-sovereign telemetry |
| **SCF** | Spectral Cognitive Field — coherence + symmetry filtering |
| **E_t** | Candidate evidence at turn t |
| **E'_t** | Filtered evidence (SCF output) |
| **Authority** | Mutates state (sovereign) — only MAYOR has this |
| **Telemetry** | Observation only (non-sovereign) — anyone can emit |

---

## Appendix: SCF Module Skeleton

```python
class SpectralAnalyzer:
    """Non-sovereign filtering + telemetry."""

    def __init__(self, params: SCFParams):
        self.params = params
        self.params_hash = sha256(canon(params))

    def process(
        self,
        candidates: List[Dict],
        scf_input: SCFInput
    ) -> Tuple[List[Dict], Dict]:
        """Filter candidates, return filtered + telemetry."""

        # Build operator from memory conflicts + trace anomalies
        A = self.build_operator(scf_input.memory, scf_input.trace)

        # Score each candidate
        filtered = []
        scores = {}

        for candidate in candidates:
            coherence = self.compute_coherence(A, candidate)
            symmetry = self.compute_symmetry(candidate)

            if self.accept(coherence, symmetry):
                filtered.append(candidate)

            scores[candidate.get("rid")] = {
                "coherence": coherence,
                "symmetry": symmetry
            }

        # Emit telemetry
        telemetry = {
            "event_id": f"scf:{scf_input.turn}",
            "type": "scf_annotation_v1",
            "scf_version": self.params.version,
            "params_hash": self.params_hash,
            "evidence_in_count": len(candidates),
            "evidence_out_count": len(filtered),
            "coherence_summary": self.bin_coherence(scores),
            "symmetry_flags": self.summarize_symmetry(scores),
            "tension_modes": self.top_eigenvalues(A),
            "authority": False
        }

        return filtered, telemetry
```

---

**Status:** Ready for implementation
**Next:** Implement SCF + run T5–T8 tests

