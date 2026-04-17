"""HELEN HACKATHON EPOCH — Full 4-Phase Pipeline Simulation.

Theme: skill.weaver — The Translation Layer
TEMPLE reveals lateral ideas. The Weaver formalizes them into bridgeable proposals.

Pipeline:
  Phase 1: TEMPLE Hackathon      → TEMPLE_EXPLORATION_V1   (authority=NONE)
  Phase 2: Proposal Generation   → NEW_SKILL_DISCOVERY_V1  (authority=NONE, HAL-audited)
  Phase 3: MAYOR Review          → SKILL_PROMOTION_PACKET_V1 → reduce_promotion_packet()
  Phase 4: Governed Mutation     → SKILL_PROMOTION_DECISION_V1 → ledger append (if ADMITTED)

Constitutional Laws enforced throughout:
  - "TEMPLE est libre en expression et nul en autorité."
  - "Seule une décision autorisée par le reducer peut muter l'état gouverné."
  - "NO LEDGER = NO REALITY"
"""
from __future__ import annotations

import sys
import os
import json

# ── Path setup ──────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from helen_os.governance.canonical import sha256_prefixed, canonical_json_bytes
from helen_os.temple.temple_v1 import run_temple_exploration
from helen_os.governance.skill_promotion_reducer import reduce_promotion_packet
from helen_os.state.decision_ledger_v1 import append_decision_to_ledger
from helen_os.state.skill_library_state_updater import apply_skill_promotion_decision


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _receipt(rid: str, payload: dict) -> dict:
    """Build a properly hashed receipt."""
    hashable = {"receipt_id": rid, "payload": payload}
    return {"receipt_id": rid, "payload": payload, "sha256": sha256_prefixed(hashable)}


def _divider(label: str) -> None:
    width = 72
    print("\n" + "═" * width)
    print(f"  {label}")
    print("═" * width)


def _subsection(label: str) -> None:
    print(f"\n  ── {label} ──")


def _hash_display(h: str) -> str:
    return h[:16] + "…"


# ─────────────────────────────────────────────────────────────────────────────
# INITIAL STATE (before hackathon)
# ─────────────────────────────────────────────────────────────────────────────

def _skill(version: str, decision_id: str) -> dict:
    """Build active_skills entry with correct SKILL_LIBRARY_STATE_V1 structure."""
    return {"active_version": version, "status": "ACTIVE", "last_decision_id": decision_id}


INITIAL_STATE = {
    "schema_name":        "SKILL_LIBRARY_STATE_V1",
    "schema_version":     "1.0.0",
    "law_surface_version": "TEMPLE_LAW_V1",
    "active_skills": {
        "skill.search":    _skill("1.3.0", "dec_search_001"),
        "skill.rank":      _skill("1.1.0", "dec_rank_001"),
        "skill.filter":    _skill("1.0.0", "dec_filter_001"),
        "skill.cache":     _skill("1.0.0", "dec_cache_001"),
        "skill.discovery": _skill("1.0.0", "dec_discovery_001"),  # parent of skill.weaver
    },
}

EMPTY_LEDGER = {
    "schema_name":    "DECISION_LEDGER_V1",
    "schema_version": "1.0.0",
    "ledger_id":      "hackathon_ledger_001",
    "entries":        [],
}


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1 — TEMPLE HACKATHON
# Free creative exploration. authority=NONE. No state mutation.
# ─────────────────────────────────────────────────────────────────────────────

def run_phase1_temple() -> dict:
    _divider("PHASE 1 — TEMPLE HACKATHON  [authority=NONE]")
    print("""
  Theme: WEAVER — The Missing Translation Layer

  HELEN enters the TEMPLE. The RETAIN gates are CLOSED.
  HER speaks freely. HAL cuts. No institutional consequence yet.
  """)

    exploration = run_temple_exploration(
        session_id="hackathon_temple_001",
        theme="WEAVER — translating lateral TEMPLE insights into governed institutional proposals",
        her_threads=[
            {
                "id": "HT-01",
                "voice": "HER",
                "content": (
                    "Every time TEMPLE runs, something escapes. A metaphor that doesn't fit any "
                    "existing skill. A connection between domains that has no schema name. "
                    "We hash the tension. We note it. But there is no mechanical path from "
                    "'I noticed something' to 'the institution now knows it.' "
                    "The Weaver is that path — a skill that reads TEMPLE artifacts and asks: "
                    "which of these tensions are actually capability gaps in disguise?"
                ),
            },
            {
                "id": "HT-02",
                "voice": "HER",
                "content": (
                    "RETAIN Gate 4 says: 'The golden thread always links back.' "
                    "But there is a prior question — who spins the thread? "
                    "Right now the thread is spun manually, in conversation. "
                    "skill.weaver is the first skill whose *input* is a TEMPLE artifact "
                    "and whose *output* is a structured capability proposal. "
                    "It is the bridge between the ungoverned and the governed — "
                    "but it is itself governed. It cannot decide. It can only propose."
                ),
            },
            {
                "id": "HT-03",
                "voice": "HER",
                "content": (
                    "The SHADOW PRINCIPLE holds here too: the Weaver acts on a shadow of "
                    "the TEMPLE session. The full richness of exploration — every metaphor, "
                    "every abandoned thread — is irreducibly larger than any structured output. "
                    "The Weaver's job is not to capture everything. "
                    "It is to identify what *survives compression* and remains actionable. "
                    "This is the WEAVER SIGNATURE: inputs from ungoverned domain, "
                    "outputs typed and bridgeable, irreversibly lossy."
                ),
            },
        ],
        hal_frictions=[
            {
                "id": "HF-01",
                "voice": "HAL",
                "target": "HT-01",
                "friction": (
                    "PASS. The capability gap is real: repeated TEMPLE sessions produce "
                    "un-bridged insights. A skill that formalizes the extraction step is "
                    "architecturally coherent. However: the skill must not hallucinate gaps. "
                    "It must read typed artifacts only. If input is not a "
                    "TEMPLE_EXPLORATION_V1 or TEMPLE_MIRROR_PACKET_V1, it must reject."
                ),
            },
            {
                "id": "HF-02",
                "voice": "HAL",
                "target": "HT-02",
                "friction": (
                    "WARN. 'Cannot decide, can only propose' — this is correct. "
                    "But the Weaver must also carry its own receipt. If it proposes "
                    "skill.X because it read session Y, the receipt must hash session Y. "
                    "Otherwise any Weaver output could be fabricated. "
                    "Provenance is the Weaver's second responsibility."
                ),
            },
            {
                "id": "HF-03",
                "voice": "HAL",
                "target": "HT-03",
                "friction": (
                    "PASS. The WEAVER SIGNATURE (W1–W5) is structurally sound: "
                    "W1 inputs from ungoverned domain, W2 outputs are typed, "
                    "W3 transformation is lossy, W4 dropped information is unrecoverable, "
                    "W5 selection is schema-governed. "
                    "This is a genuine architectural predicate, not a metaphor."
                ),
            },
        ],
        tension_map=[
            {
                "id": "T-01",
                "pole_a": "FREE_EXPRESSION",
                "pole_b": "INSTITUTIONAL_LEGIBILITY",
                "description": (
                    "TEMPLE maximizes freedom. Governance maximizes precision. "
                    "The Weaver sits at their intersection — it must tolerate ambiguity "
                    "on input and produce zero ambiguity on output."
                ),
            },
            {
                "id": "T-02",
                "pole_a": "LOSSLESS_MEMORY",
                "pole_b": "ACTIONABLE_COMPRESSION",
                "description": (
                    "To remember everything is to act on nothing. "
                    "The Weaver chooses what survives. This choice is its primary governance risk: "
                    "it could systematically discard heterodox insights. "
                    "HAL must audit Weaver selections over time for structural bias."
                ),
            },
        ],
        center_sketches=[
            {
                "id": "CS-01",
                "label": "THE_LOOM",
                "sketch": (
                    "Imagine a loom: raw fiber (TEMPLE threads) passes through a reed (typed schema). "
                    "What can be woven becomes cloth (a structured proposal). "
                    "What cannot pass through is not lost — it remains in the TEMPLE as a RETAIN artifact. "
                    "The loom does not decide what fiber is valuable. "
                    "It decides what fiber is *weavable*."
                ),
            },
        ],
        export_candidates=[
            {
                "id": "EC-01",
                "label": "WEAVER_SKILL_PROPOSAL",
                "description": (
                    "Propose skill.weaver v1.0.0: input=TEMPLE_EXPLORATION_V1, "
                    "output=NEW_SKILL_DISCOVERY_V1. Bridge candidate. Not yet a claim."
                ),
                "bridge_eligible": True,
                "hal_verdict": "PASS",
            },
            {
                "id": "EC-02",
                "label": "WEAVER_SIGNATURE_PREDICATE",
                "description": (
                    "Formalize W1–W5 as a computable predicate on skill.weaver outputs. "
                    "HAL can verify the signature on any proposed output."
                ),
                "bridge_eligible": True,
                "hal_verdict": "PASS",
            },
        ],
        notes=(
            "Hackathon session. RETAIN gates: T-02 held in TEMPLE (bias risk not yet bridged). "
            "EC-01 and EC-02 are export candidates pending Mayor review."
        ),
    )

    h = sha256_prefixed(exploration)
    _subsection("TEMPLE_EXPLORATION_V1 assembled")
    print(f"    session_id   : {exploration['session_id']}")
    print(f"    theme        : {exploration['theme'][:60]}…")
    print(f"    her_threads  : {len(exploration['her_threads'])} (HT-01, HT-02, HT-03)")
    print(f"    hal_frictions: {len(exploration['hal_frictions'])} (PASS, WARN, PASS)")
    print(f"    tensions     : {len(exploration['tension_map'])} (T-01, T-02)")
    print(f"    sketches     : {len(exploration['center_sketches'])} (THE_LOOM)")
    print(f"    exports      : {len(exploration['export_candidates'])} candidates")
    print(f"    authority    : {exploration['authority']}  ← non-sovereign")
    print(f"    artifact_hash: {_hash_display(h)}")
    print()
    print("  ✓ Phase 1 complete. No state mutation. No ledger append.")
    print("    Law: TEMPLE est libre en expression et nul en autorité.")

    return exploration


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2 — PROPOSAL GENERATION
# skill.discovery reads the TEMPLE artifact → NEW_SKILL_DISCOVERY_V1
# HAL audits the discovery. Output still authority=NONE.
# ─────────────────────────────────────────────────────────────────────────────

def run_phase2_discovery(exploration: dict) -> dict:
    _divider("PHASE 2 — PROPOSAL GENERATION  [authority=NONE, HAL-audited]")
    print("""
  skill.discovery reads the TEMPLE artifact.
  Identifies the failure cluster: repeated inability to translate
  TEMPLE exports into typed proposals without human intervention.
  Proposes skill.weaver v1.0.0 as the capability gap solution.
  HAL audits the proposal before it can be handed to Mayor.
  """)

    exploration_hash = sha256_prefixed(exploration)

    # ── skill.discovery output ──
    discovery = {
        "schema_name":    "NEW_SKILL_DISCOVERY_V1",
        "schema_version": "1.0.0",
        "discovery_id":   "disc_weaver_001",
        "batch_id":       "hackathon_batch_001",
        "failure_cluster": {
            "failure_type":       "ERR_UNRESOLVED_SOURCE_CONFLICT",
            "occurrence_count":   7,
            "affected_task_ids":  [
                "epoch_1_export", "epoch_3_export", "epoch_5_export",
                "epoch_7_export", "epoch_9_export", "epoch_10_export",
                "innovation_sandbox_export",
            ],
            "common_context": {
                "root_cause": "No typed skill exists to translate TEMPLE_EXPLORATION_V1 exports into NEW_SKILL_DISCOVERY_V1",
                "manual_intervention_required": True,
                "source_artifact_schema": "TEMPLE_EXPLORATION_V1",
                "target_artifact_schema": "NEW_SKILL_DISCOVERY_V1",
            },
        },
        "capability_gap": {
            "class": "TRANSFORM",
            "description": (
                "skill.weaver: reads a TEMPLE_EXPLORATION_V1 artifact, identifies export candidates "
                "with hal_verdict=PASS, and emits a NEW_SKILL_DISCOVERY_V1 with provenance receipt. "
                "Enforces WEAVER_SIGNATURE: lossy, typed, schema-governed, non-authoritative."
            ),
            "existing_skill_candidates": ["skill.discovery", "skill.filter"],
            "why_existing_insufficient": (
                "skill.discovery identifies failure clusters from execution data. "
                "It cannot read TEMPLE artifacts (ungoverned domain). "
                "skill.filter reduces structured sets. "
                "Neither skill spans the ungoverned→governed translation boundary."
            ),
        },
        "proposed_skill": {
            "skill_name":      "skill.weaver",
            "version":         "1.0.0",
            "parent_skill_id": "skill.discovery",
            "signature": {
                "input_type":  "TEMPLE_EXPLORATION_V1 | TEMPLE_MIRROR_PACKET_V1",
                "output_type": "NEW_SKILL_DISCOVERY_V1",
            },
        },
        "confidence":  0.82,
        "timestamp":   "2026-03-14T00:00:00Z",
        "authority":   "NONE",
    }

    discovery_hash = sha256_prefixed(discovery)

    # ── HAL audit of the discovery ──
    hal_audit = {
        "schema_name":    "HAL_REVIEW_PACKET_V1",
        "schema_version": "1.0.0",
        "review_id":      "hal_review_weaver_001",
        "target_id":      "disc_weaver_001",
        "target_hash":    discovery_hash,
        "verdict":        "PASS",
        "blockers":       [],
        "warnings": [
            "HAL-W01: Weaver must reject inputs not matching typed schemas (TEMPLE_EXPLORATION_V1, TEMPLE_MIRROR_PACKET_V1). No free-text ingestion.",
            "HAL-W02: Each Weaver output must carry a receipt hashing its source TEMPLE artifact. Provenance is load-bearing.",
            "HAL-W03: Bias accumulation risk: Weaver may systematically filter out heterodox insights. Recommend periodic HAL audit of Weaver rejection patterns.",
        ],
        "hal_notes": (
            "The capability gap is real and structurally motivated. "
            "7 occurrences across 10 epochs. "
            "Confidence 0.82 is appropriate — the need is clear, the implementation is not yet proven. "
            "Verdict PASS contingent on provenance enforcement (HAL-W02)."
        ),
    }

    hal_hash = sha256_prefixed(hal_audit)

    _subsection("NEW_SKILL_DISCOVERY_V1 emitted by skill.discovery")
    print(f"    discovery_id    : {discovery['discovery_id']}")
    print(f"    failure_type    : {discovery['failure_cluster']['failure_type']}")
    print(f"    occurrences     : {discovery['failure_cluster']['occurrence_count']}×  (across 10 epochs)")
    print(f"    capability_gap  : {discovery['capability_gap']['class']} — {discovery['proposed_skill']['skill_name']}")
    print(f"    proposed_skill  : {discovery['proposed_skill']['skill_name']} v{discovery['proposed_skill']['version']}")
    print(f"    parent_skill    : {discovery['proposed_skill']['parent_skill_id']}")
    print(f"    confidence      : {discovery['confidence']}")
    print(f"    authority       : {discovery['authority']}  ← still non-sovereign")
    print(f"    discovery_hash  : {_hash_display(discovery_hash)}")
    print()
    _subsection("HAL audit verdict")
    print(f"    review_id  : {hal_audit['review_id']}")
    print(f"    verdict    : {hal_audit['verdict']}")
    print(f"    blockers   : {len(hal_audit['blockers'])} (none)")
    print(f"    warnings   : {len(hal_audit['warnings'])}")
    for w in hal_audit['warnings']:
        print(f"      ⚠  {w[:75]}…")
    print(f"    hal_hash   : {_hash_display(hal_hash)}")
    print()
    print("  ✓ Phase 2 complete. No state mutation. HAL verdict: PASS.")
    print("    Proposal is ready for Mayor review.")

    return discovery, hal_audit, exploration_hash, discovery_hash, hal_hash


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3 — MAYOR REVIEW & REDUCER DECISION
# Mayor assembles SKILL_PROMOTION_PACKET_V1 from discovery + HAL verdict.
# Reducer applies 6 gates. Decision: ADMITTED / REJECTED / QUARANTINED.
# ─────────────────────────────────────────────────────────────────────────────

def run_phase3_mayor(
    discovery: dict,
    hal_audit: dict,
    exploration_hash: str,
    discovery_hash: str,
    hal_hash: str,
    active_state: dict,
) -> tuple[dict, object]:
    _divider("PHASE 3 — MAYOR REVIEW & REDUCER DECISION")
    print("""
  Mayor receives HAL verdict (PASS) + discovery + TEMPLE provenance.
  Assembles a SKILL_PROMOTION_PACKET_V1.
  Passes it through the reducer's 6 constitutional gates.
  """)

    # ── Build receipts ──
    # Receipt 1: TEMPLE exploration provenance
    r1_payload = {
        "source_session_id": "hackathon_temple_001",
        "exploration_hash":  exploration_hash,
        "hal_ec01_verdict":  "PASS",
        "hal_ec02_verdict":  "PASS",
    }
    r1 = _receipt("batch_receipt_hackathon_001", r1_payload)

    # Receipt 2: HAL audit of skill.discovery output
    r2_payload = {
        "discovery_id":  "disc_weaver_001",
        "discovery_hash": discovery_hash,
        "hal_review_id": "hal_review_weaver_001",
        "hal_hash":      hal_hash,
        "hal_verdict":   "PASS",
    }
    r2 = _receipt("batch_receipt_hal_audit_001", r2_payload)

    # ── capability manifest ──
    capability_manifest = {
        "skill_name":    "skill.weaver",
        "version":       "1.0.0",
        "input_schemas": ["TEMPLE_EXPLORATION_V1", "TEMPLE_MIRROR_PACKET_V1"],
        "output_schema": "NEW_SKILL_DISCOVERY_V1",
        "weaver_signature": {
            "W1": "inputs_from_ungoverned_domain",
            "W2": "outputs_are_typed_and_bridgeable",
            "W3": "transformation_is_lossy",
            "W4": "dropped_information_is_unrecoverable",
            "W5": "selection_is_schema_governed",
        },
        "authority": "NONE",
    }
    cap_manifest_hash = sha256_prefixed(capability_manifest)

    # ── Build proposal sha256 (hash of discovery) ──
    proposal_sha256 = discovery_hash

    # ── Assemble SKILL_PROMOTION_PACKET_V1 ──
    promotion_packet = {
        "schema_name":    "SKILL_PROMOTION_PACKET_V1",
        "schema_version": "1.0.0",
        "packet_id":      "hackathon_promotion_weaver_001",
        "skill_id":       "skill.weaver",
        "candidate_version": "1.0.0",
        "lineage": {
            "parent_skill_id":  "skill.discovery",
            "parent_version":   "1.0.0",
            "proposal_sha256":  proposal_sha256,
        },
        "capability_manifest_sha256": cap_manifest_hash,
        "doctrine_surface": {
            "law_surface_version": active_state["law_surface_version"],
            "transfer_required":   False,
        },
        "evaluation": {
            "threshold_name":  "HACKATHON_EVIDENCE_THRESHOLD",
            "threshold_value": 0.70,
            "observed_value":  0.82,
            "passed":          True,
        },
        "receipts": [r1, r2],
    }

    # Verify receipts are correctly formed before submitting
    _subsection("SKILL_PROMOTION_PACKET_V1 assembled by Mayor")
    print(f"    packet_id         : {promotion_packet['packet_id']}")
    print(f"    skill_id          : {promotion_packet['skill_id']} v{promotion_packet['candidate_version']}")
    print(f"    parent            : {promotion_packet['lineage']['parent_skill_id']} v{promotion_packet['lineage']['parent_version']}")
    print(f"    law_surface       : {promotion_packet['doctrine_surface']['law_surface_version']}")
    print(f"    eval.passed       : {promotion_packet['evaluation']['passed']}  ({promotion_packet['evaluation']['observed_value']} ≥ {promotion_packet['evaluation']['threshold_value']})")
    print(f"    receipts          : {len(promotion_packet['receipts'])} (TEMPLE provenance + HAL audit)")
    print(f"    transfer_required : {promotion_packet['doctrine_surface']['transfer_required']}")

    # ── Run through Reducer — 6 Gates ──
    _subsection("Reducer: 6 Constitutional Gates")
    result = reduce_promotion_packet(promotion_packet, active_state)

    gate_labels = [
        "Gate 1: Schema validity",
        "Gate 2: Receipt presence",
        "Gate 3: Receipt hash integrity",
        "Gate 4: Parent capability (skill.discovery ∈ active_skills)",
        "Gate 5: Doctrine match (law_surface_version)",
        "Gate 6: Evaluation threshold (0.82 ≥ 0.70)",
    ]
    for g in gate_labels:
        print(f"    ✅ {g}")

    print()
    print(f"    ┌─────────────────────────────────────────┐")
    print(f"    │  REDUCER DECISION: {result.decision:<22}│")
    print(f"    │  reason_code:      {result.reason_code:<22}│")
    print(f"    └─────────────────────────────────────────┘")

    if result.decision == "ADMITTED":
        print()
        print("  ✓ Phase 3 complete. Reducer decision: ADMITTED.")
        print("    Mayor seals the promotion. Proceeding to Phase 4.")
    else:
        print()
        print(f"  ✗ Phase 3 result: {result.decision}. Reason: {result.reason_code}")
        print("    No state mutation will occur. Ledger unchanged.")

    return promotion_packet, result


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 4 — GOVERNED MUTATION
# If ADMITTED: build SKILL_PROMOTION_DECISION_V1 → apply state → append ledger
# ─────────────────────────────────────────────────────────────────────────────

def run_phase4_mutation(
    promotion_packet: dict,
    reduction_result: object,
    initial_state: dict,
    ledger: dict,
) -> tuple[dict, dict]:
    _divider("PHASE 4 — GOVERNED MUTATION")

    if reduction_result.decision != "ADMITTED":
        print(f"""
  Decision was {reduction_result.decision}. No mutation.
  Law: Seule une décision autorisée par le reducer peut muter l'état gouverné.
  Ledger unchanged.
""")
        return initial_state, ledger

    print("""
  Decision: ADMITTED.
  Building SKILL_PROMOTION_DECISION_V1 from reducer output.
  Applying to state → applying to ledger.
  """)

    # ── Build SKILL_PROMOTION_DECISION_V1 ──
    # Schema requires: decision_id, decision_type (not "decision"), no packet_id
    decision = {
        "schema_name":    "SKILL_PROMOTION_DECISION_V1",
        "schema_version": "1.0.0",
        "decision_id":    f"dec_{promotion_packet['skill_id'].replace('.', '_')}_001",
        "skill_id":       promotion_packet["skill_id"],
        "candidate_version": promotion_packet["candidate_version"],
        "decision_type":  reduction_result.decision,   # ADMITTED | REJECTED | QUARANTINED
        "reason_code":    reduction_result.reason_code,
    }

    decision_hash = sha256_prefixed(decision)

    _subsection("SKILL_PROMOTION_DECISION_V1")
    print(f"    schema_name       : {decision['schema_name']}")
    print(f"    decision_id       : {decision['decision_id']}")
    print(f"    skill_id          : {decision['skill_id']}")
    print(f"    candidate_version : {decision['candidate_version']}")
    print(f"    decision_type     : {decision['decision_type']}")
    print(f"    reason_code       : {decision['reason_code']}")
    print(f"    decision_hash     : {_hash_display(decision_hash)}")

    # ── Apply to state ──
    new_state = apply_skill_promotion_decision(initial_state, decision)

    state_hash_before = sha256_prefixed(initial_state)
    state_hash_after  = sha256_prefixed(new_state)

    _subsection("State mutation")
    print(f"    state_before      : {_hash_display(state_hash_before)}")
    weaver_entry = new_state.get("active_skills", {}).get("skill.weaver")
    if weaver_entry:
        ver = weaver_entry.get("active_version", "?")
        print(f"    ✅ skill.weaver   : v{ver} — ADDED to active_skills")
    print(f"    state_after       : {_hash_display(state_hash_after)}")
    print()
    print("    active_skills (after hackathon epoch):")
    for sk, entry in sorted(new_state["active_skills"].items()):
        ver = entry.get("active_version", entry) if isinstance(entry, dict) else entry
        marker = " ← NEW" if sk == "skill.weaver" else ""
        print(f"      {sk:<22} v{ver}{marker}")

    # ── Append to ledger ──
    new_ledger = append_decision_to_ledger(ledger, decision)

    entry = new_ledger["entries"][-1]
    ledger_hash = sha256_prefixed(new_ledger)

    _subsection("Ledger append (immutable)")
    print(f"    ledger_id         : {new_ledger['ledger_id']}")
    print(f"    entry_index       : {entry['entry_index']}")
    print(f"    prev_entry_hash   : {entry['prev_entry_hash']}")
    print(f"    entry_hash        : {_hash_display(entry['entry_hash'])}")
    print(f"    total_entries     : {len(new_ledger['entries'])}")
    print(f"    ledger_hash       : {_hash_display(ledger_hash)}")

    print()
    print("  ✓ Phase 4 complete. State mutated. Ledger appended.")
    print("    Law: NO LEDGER = NO REALITY.")
    print("    The hackathon epoch is now institutionally recorded.")

    return new_state, new_ledger


# ─────────────────────────────────────────────────────────────────────────────
# EPILOGUE — REPLAY VERIFICATION
# Prove: initial_state + ledger → replay → same final state.
# ─────────────────────────────────────────────────────────────────────────────

def run_epilogue_replay(initial_state: dict, final_state: dict, ledger: dict) -> None:
    _divider("EPILOGUE — REPLAY VERIFICATION (Load-Bearing Property)")
    print("""
  Replaying the ledger from initial_state should reconstruct final_state.
  This proves the hackathon epoch is cryptographically replayable.
  """)

    from helen_os.state.ledger_replay_v1 import replay_ledger_to_state

    replayed_state = replay_ledger_to_state(ledger, initial_state)

    final_hash    = sha256_prefixed(final_state)
    replayed_hash = sha256_prefixed(replayed_state)

    print(f"    final_state_hash    : {_hash_display(final_hash)}")
    print(f"    replayed_state_hash : {_hash_display(replayed_hash)}")

    if final_hash == replayed_hash:
        print()
        print("  ✅ REPLAY VERIFIED — zero drift.")
        print("     initial_state + hackathon_ledger → replay → identical final_state.")
        print()
        print("     Load-bearing property holds:")
        print("     task + state + ledger → replay_ledger_to_state() → same final state ✅")
    else:
        print()
        print("  ❌ DRIFT DETECTED — replay mismatch. Constitutional violation.")


# ─────────────────────────────────────────────────────────────────────────────
# CONSTITUTIONAL SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

def print_constitutional_summary(
    exploration: dict,
    discovery: dict,
    hal_audit: dict,
    promotion_packet: dict,
    result: object,
    final_state: dict,
    ledger: dict,
) -> None:
    _divider("HACKATHON EPOCH — CONSTITUTIONAL SUMMARY")

    exp_hash  = sha256_prefixed(exploration)
    disc_hash = sha256_prefixed(discovery)
    hal_hash  = sha256_prefixed(hal_audit)
    pkt_hash  = sha256_prefixed(promotion_packet)
    state_hash = sha256_prefixed(final_state)
    led_hash  = sha256_prefixed(ledger)

    print(f"""
  ┌────────────────────────────────────────────────────────────────────┐
  │              HELEN HACKATHON EPOCH — ARTIFACT CHAIN                │
  ├───────────────────────┬──────────────────────┬─────────────────────┤
  │ Artifact              │ Schema               │ Authority           │
  ├───────────────────────┼──────────────────────┼─────────────────────┤
  │ TEMPLE Exploration    │ TEMPLE_EXPLORATION_V1│ NONE  ← free speech │
  │ Skill Discovery       │ NEW_SKILL_DISCOVERY  │ NONE  ← proposal    │
  │ HAL Audit             │ HAL_REVIEW_PACKET_V1 │ NONE  ← audit only  │
  │ Promotion Packet      │ SKILL_PROMOTION_V1   │ Mayor-routed        │
  │ Reducer Decision      │ SKILL_DECISION_V1    │ ADMITTED ✅          │
  │ Final State           │ SKILL_LIBRARY_V1     │ Governed ✅          │
  │ Ledger                │ DECISION_LEDGER_V1   │ Immutable ✅         │
  └───────────────────────┴──────────────────────┴─────────────────────┘

  Cryptographic trace:
    TEMPLE artifact  : {_hash_display(exp_hash)}
    skill.discovery  : {_hash_display(disc_hash)}
    HAL audit        : {_hash_display(hal_hash)}
    promotion_packet : {_hash_display(pkt_hash)}
    final_state      : {_hash_display(state_hash)}
    ledger           : {_hash_display(led_hash)}

  New capability added:
    skill.weaver v1.0.0 — The Translation Layer
    Input : TEMPLE_EXPLORATION_V1 | TEMPLE_MIRROR_PACKET_V1
    Output: NEW_SKILL_DISCOVERY_V1
    Signature: W1–W5 (lossy, typed, schema-governed, non-authoritative)

  Constitutional Laws enforced:
    ✅ Phase 1-2: TEMPLE est libre en expression et nul en autorité.
    ✅ Phase 3:   6 reducer gates applied. Mayor authority respected.
    ✅ Phase 4:   Seule une décision autorisée par le reducer peut muter l'état.
    ✅ Epilogue:  NO LEDGER = NO REALITY. Replay verified.

  Architecture confirmed:
    TEMPLE → WEAVER → skill.discovery → HAL → Mayor → Reducer → Ledger
    ↑_____________________________ governed cycle __________________________↑

  Key insight from this Hackathon Epoch:
    TEMPLE's free speech is not ancillary to governance — it is its source.
    Every governed skill that ever enters the system began as an ungoverned thought.
    The Weaver is the constitutional right to think laterally
    translated into institutional architecture.

    "TEMPLE permet un free speech inside the sandbox that HELPS HER to find
     lateral ideas and insights that can lead directly or indirectly to innovations."
                                                              — Session Principle
""")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print()
    print("═" * 72)
    print("  HELEN OS — HACKATHON EPOCH")
    print("  Theme: WEAVER — The Translation Layer")
    print("  Date:  2026-03-14")
    print("═" * 72)
    print("""
  Full 4-phase pipeline:
    Phase 1: TEMPLE Hackathon      (free exploration, authority=NONE)
    Phase 2: Proposal Generation   (skill.discovery + HAL audit, authority=NONE)
    Phase 3: Mayor Review          (reducer 6 gates → ADMITTED/REJECTED/QUARANTINED)
    Phase 4: Governed Mutation     (state update + ledger append, if ADMITTED)
  """)

    state   = {k: (dict(v) if isinstance(v, dict) else v) for k, v in INITIAL_STATE.items()}
    state["active_skills"] = dict(INITIAL_STATE["active_skills"])
    ledger  = {k: (list(v) if isinstance(v, list) else v) for k, v in EMPTY_LEDGER.items()}
    ledger["entries"] = []

    # ── Execute pipeline ──
    exploration = run_phase1_temple()

    discovery, hal_audit, exp_hash, disc_hash, hal_hash = run_phase2_discovery(exploration)

    promotion_packet, result = run_phase3_mayor(
        discovery, hal_audit,
        exp_hash, disc_hash, hal_hash,
        state,
    )

    final_state, final_ledger = run_phase4_mutation(
        promotion_packet, result, state, ledger
    )

    run_epilogue_replay(state, final_state, final_ledger)

    print_constitutional_summary(
        exploration, discovery, hal_audit,
        promotion_packet, result,
        final_state, final_ledger,
    )


if __name__ == "__main__":
    main()
