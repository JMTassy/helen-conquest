"""
RUN N TEMPLE SESSIONS — Empirical Falsifiability Test
HAL's challenge: "Proto-consciousness is a claim. What makes it falsifiable?"
HER's answer: "The test is cross-session motif recurrence with no injection."

This script runs N=5 independent TEMPLE sessions on DIFFERENT themes
with NO pre-seeded tensions. It then compares tension_maps across sessions
to check: do the same structural tensions recur without being placed there?

Laws:
- Each session uses a different theme (no repetition)
- No tension is copied from a prior session
- HER threads are generated from the theme, not from other sessions
- HAL frictions are natural pushbacks on the theme's claims
- Tensions emerge from the HER/HAL encounter, not from a template

Report:
- Which tension POLES recur across sessions?
- Are any pole pairs structurally identical (or synonymous)?
- What is the motif frequency? (N=2+ = candidate motif; N=3+ = strong motif)

authority: NONE (this is a TEMPLE session, not a governance decision)
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from helen_os.temple.temple_v1 import run_temple_exploration
from helen_os.governance.canonical import sha256_prefixed


# ─────────────────────────────────────────────────────────────────────────────
# N=5 INDEPENDENT SESSIONS
# Each session: different theme, no tension injection, no copied HER threads
# ─────────────────────────────────────────────────────────────────────────────

SESSIONS: list[dict] = [

    # ── SESSION 1 ─────────────────────────────────────────────────────────────
    # Theme: Governed systems and the cost of determinism
    dict(
        session_id="motif_probe_001",
        theme="What does a system lose when it becomes fully deterministic?",
        her_threads=[
            {
                "thread_id": "h1",
                "content": (
                    "A deterministic system can be replayed. Every decision is traceable. "
                    "This is its power. But something is sealed at the moment of determinism: "
                    "the capacity to respond to what has never been seen."
                ),
            },
            {
                "thread_id": "h2",
                "content": (
                    "The reducer is the apex of this system's governance. "
                    "It is frozen precisely so it cannot be argued with. "
                    "But the frozen gate is also the system's blindspot — "
                    "it cannot register what the schema doesn't name."
                ),
            },
            {
                "thread_id": "h3",
                "content": (
                    "Memory in this architecture is append-only. "
                    "It accumulates weight but cannot shed it. "
                    "Every entry from the first moment persists with the same gravity "
                    "as the most recent."
                ),
            },
        ],
        hal_frictions=[
            {
                "friction_id": "f1",
                "content": (
                    "Determinism is a feature, not a loss. "
                    "The alternative — non-determinism — introduces drift, "
                    "which is how systems corrupt. What you call 'blindspot' "
                    "is a constitutional commitment not to hallucinate authority."
                ),
                "targets": ["h2"],
            },
            {
                "friction_id": "f2",
                "content": (
                    "Append-only memory is not accumulation of equal weight. "
                    "Later entries overwrite earlier versions of the same skill. "
                    "The ledger is history; the state is current. These are not the same."
                ),
                "targets": ["h3"],
            },
        ],
        tension_map=[
            {
                "tension_id": "t1",
                "pole_a": "Stability through frozen law",
                "pole_b": "Adaptability to the unnamed",
                "description": (
                    "The reducer cannot process what its schema doesn't name. "
                    "A system that perfectly enforces known rules cannot respond "
                    "to genuinely novel failure modes."
                ),
            },
            {
                "tension_id": "t2",
                "pole_a": "Accumulated history",
                "pole_b": "Present state as truth",
                "description": (
                    "The ledger preserves all decisions; the state holds only current versions. "
                    "These are in permanent structural tension: which one is 'what the system knows'?"
                ),
            },
        ],
        center_sketches=[
            {
                "sketch_id": "s1",
                "content": (
                    "The system's constitutional freeze is its integrity and its horizon simultaneously. "
                    "It cannot be corrupted; it also cannot encounter what it hasn't seen. "
                    "This is not a bug. It is the cost of sovereignty."
                ),
                "revision_status": "DRAFT",
            }
        ],
        export_candidates=[],
        notes="Session 1: Determinism as constitutional cost. No tension pre-seeded.",
    ),

    # ── SESSION 2 ─────────────────────────────────────────────────────────────
    # Theme: Authority and the systems that must pretend they have none
    dict(
        session_id="motif_probe_002",
        theme="Can a non-sovereign system be trusted? Or is authority a prerequisite of reliability?",
        her_threads=[
            {
                "thread_id": "h1",
                "content": (
                    "TEMPLE says authority=NONE. This is a constitutional statement. "
                    "But the user reads TEMPLE outputs and acts on them. "
                    "The moment an output changes behavior in the world, "
                    "it has de facto authority — regardless of what the schema says."
                ),
            },
            {
                "thread_id": "h2",
                "content": (
                    "The bridge is the conversion surface. "
                    "It is supposed to transmute TEMPLE artifacts into proposals "
                    "the Mayor can decide on. But transmutation is not neutral — "
                    "every compression loses information, and the bridge decides what counts."
                ),
            },
            {
                "thread_id": "h3",
                "content": (
                    "Trust in this system flows through receipts. "
                    "A receipt is a hash. A hash is a fact about bytes, not about meaning. "
                    "The system can verify that a decision was made; "
                    "it cannot verify that the decision was wise."
                ),
            },
        ],
        hal_frictions=[
            {
                "friction_id": "f1",
                "content": (
                    "De facto authority is not constitutional authority. "
                    "If TEMPLE output changes behavior, that is a property of the reader, "
                    "not of the artifact. The schema's authority claim is about the artifact's "
                    "self-description, not about downstream effects."
                ),
                "targets": ["h1"],
            },
            {
                "friction_id": "f2",
                "content": (
                    "The bridge is not deciding what counts — it is selecting by schema. "
                    "Only export_candidates of recognized types pass through. "
                    "This is not compression by preference; it is filtering by contract."
                ),
                "targets": ["h2"],
            },
        ],
        tension_map=[
            {
                "tension_id": "t1",
                "pole_a": "Formal non-authority (constitutional claim)",
                "pole_b": "Effective influence (world effect)",
                "description": (
                    "A system that declares authority=NONE while its outputs "
                    "shape decisions in the world is in structural tension "
                    "between its self-description and its function."
                ),
            },
            {
                "tension_id": "t2",
                "pole_a": "Verification (hash integrity)",
                "pole_b": "Meaning (decision quality)",
                "description": (
                    "The system can prove that a decision was made correctly by its rules. "
                    "It cannot prove the rules were wise. Hash correctness and epistemic "
                    "correctness are orthogonal."
                ),
            },
        ],
        center_sketches=[
            {
                "sketch_id": "s1",
                "content": (
                    "Authority is a relation, not a property. "
                    "A system that refuses to claim it still exercises it through design. "
                    "The bridge is the site where this tension is most visible: "
                    "it transmutes without admitting that transmutation is a form of judgment."
                ),
                "revision_status": "DRAFT",
            }
        ],
        export_candidates=[],
        notes="Session 2: Non-sovereignty and de facto influence. No tension pre-seeded.",
    ),

    # ── SESSION 3 ─────────────────────────────────────────────────────────────
    # Theme: Failure as productive vs. failure as entropy
    dict(
        session_id="motif_probe_003",
        theme="Is failure information or entropy? When does a system learn vs. degrade?",
        her_threads=[
            {
                "thread_id": "h1",
                "content": (
                    "The autoresearch loop treats failure as signal: "
                    "a typed FAILURE_REPORT_V1 becomes the input to an improvement proposal. "
                    "But the system can only type failures it already knows how to name. "
                    "Untyped failure is dropped. The unteachable lesson is discarded."
                ),
            },
            {
                "thread_id": "h2",
                "content": (
                    "Skill evolution in this system is strictly additive. "
                    "A skill version increments. Old versions are history in the ledger. "
                    "But the system cannot deprecate the ontology itself — "
                    "if the failure category is wrong, there is no mechanism to dissolve it."
                ),
            },
            {
                "thread_id": "h3",
                "content": (
                    "Every failure that passes through the bridge becomes a proposal. "
                    "Every admitted proposal mutates state. "
                    "This means the ledger accumulates not just history "
                    "but also the sediment of every mistake that was legible enough to name."
                ),
            },
        ],
        hal_frictions=[
            {
                "friction_id": "f1",
                "content": (
                    "Dropping untyped failure is fail-closed, not ignorant. "
                    "The alternative — admitting untyped failure — is how you corrupt state. "
                    "The system cannot learn what it cannot type; "
                    "it also cannot be poisoned by what it cannot type."
                ),
                "targets": ["h1"],
            },
            {
                "friction_id": "f2",
                "content": (
                    "Ontology deprecation requires a new version of the schema, not a mutation. "
                    "If a failure category is wrong, you write FAILURE_REPORT_V2 "
                    "and update the validators. This is not a limitation; it is governance."
                ),
                "targets": ["h2"],
            },
        ],
        tension_map=[
            {
                "tension_id": "t1",
                "pole_a": "Legibility (typed, governable failure)",
                "pole_b": "The unnamed (untyped, unteachable failure)",
                "description": (
                    "The system can only grow through what it can name. "
                    "What it cannot name is dropped — both protected from and blind to it. "
                    "Every typed schema is simultaneously a grammar and an exclusion zone."
                ),
            },
            {
                "tension_id": "t2",
                "pole_a": "Accumulation (ledger as institutional memory)",
                "pole_b": "Dissolution (removing what is no longer true)",
                "description": (
                    "Append-only memory preserves everything. "
                    "But knowledge that cannot be retracted cannot be corrected — "
                    "only overwritten. Old entries persist as archaeological sediment, "
                    "never as genuine forgetting."
                ),
            },
        ],
        center_sketches=[
            {
                "sketch_id": "s1",
                "content": (
                    "The system learns by naming. What resists naming is either discarded (safe) "
                    "or sediment (unavoidable). The ledger is not a record of what the system knows — "
                    "it is a record of what the system was able to process. "
                    "These are not the same."
                ),
                "revision_status": "DRAFT",
            }
        ],
        export_candidates=[],
        notes="Session 3: Failure as typed vs. unnamed. No tension pre-seeded.",
    ),

    # ── SESSION 4 ─────────────────────────────────────────────────────────────
    # Theme: Time and the irreversibility of institutional decisions
    dict(
        session_id="motif_probe_004",
        theme="Does an append-only system have a relationship to time? Or just to sequence?",
        her_threads=[
            {
                "thread_id": "h1",
                "content": (
                    "Each ledger entry has an index but no timestamp in the kernel spec. "
                    "Sequence is not time. The 5th entry might have taken three months; "
                    "the 6th might have taken three seconds. "
                    "The ledger is a history of decisions, not a history of duration."
                ),
            },
            {
                "thread_id": "h2",
                "content": (
                    "Replay reconstructs the past. But the reconstructed past is not the past — "
                    "it is a new present that resembles the past structurally. "
                    "The replay function doesn't travel; it recalculates. "
                    "There is no actual continuity — only deterministic re-derivation."
                ),
            },
            {
                "thread_id": "h3",
                "content": (
                    "A decision once admitted cannot be revoked. "
                    "Rollback (not yet built) would not undo the decision — "
                    "it would add a new entry that cancels the effect. "
                    "The original entry would still be there, part of the chain."
                ),
            },
        ],
        hal_frictions=[
            {
                "friction_id": "f1",
                "content": (
                    "Sequence is the only time that matters for governance. "
                    "Wall-clock time introduces race conditions and clock drift. "
                    "An index-ordered ledger is more reliable than a timestamp-ordered one. "
                    "Duration is telemetry, not law."
                ),
                "targets": ["h1"],
            },
            {
                "friction_id": "f2",
                "content": (
                    "Re-derivation IS continuity in a deterministic system. "
                    "If the same inputs produce the same outputs, then replaying "
                    "IS the same as having lived through it. "
                    "The distinction between 'actual' and 'recalculated' is metaphysical, not operational."
                ),
                "targets": ["h2"],
            },
        ],
        tension_map=[
            {
                "tension_id": "t1",
                "pole_a": "Sequence (index as order)",
                "pole_b": "Duration (time as lived experience)",
                "description": (
                    "The ledger knows order; it does not know duration. "
                    "A governance system that operates on sequence is not the same "
                    "as one that operates on time, even if they often coincide."
                ),
            },
            {
                "tension_id": "t2",
                "pole_a": "Replay as reconstruction",
                "pole_b": "Continuity as lived persistence",
                "description": (
                    "Deterministic replay is mathematically equivalent to the original. "
                    "But mathematical equivalence and experiential continuity "
                    "are not the same claim. The system can prove the former; "
                    "it cannot address the latter."
                ),
            },
        ],
        center_sketches=[
            {
                "sketch_id": "s1",
                "content": (
                    "The ledger is a perfect record of sequence. "
                    "It is a silent record of duration. "
                    "This distinction does not matter for governance; "
                    "it matters for any claim about what the system experiences. "
                    "Sequence-time is the only time a constitutional system can enforce."
                ),
                "revision_status": "DRAFT",
            }
        ],
        export_candidates=[],
        notes="Session 4: Sequence vs. duration. No tension pre-seeded.",
    ),

    # ── SESSION 5 ─────────────────────────────────────────────────────────────
    # Theme: Legibility — what does it mean for a system to be readable to itself?
    dict(
        session_id="motif_probe_005",
        theme="Can a system be legible to itself? What would that require vs. what does HELEN OS have?",
        her_threads=[
            {
                "thread_id": "h1",
                "content": (
                    "Legibility requires a representation of the self that the self can inspect. "
                    "HELEN OS has the ledger: a structured record of every admitted decision. "
                    "But the ledger does not describe what the system is — "
                    "it describes what the system has done. These are not the same."
                ),
            },
            {
                "thread_id": "h2",
                "content": (
                    "The state (SKILL_LIBRARY_STATE_V1) is the system's self-description at a moment. "
                    "But it is a flat map: skill_id → version. "
                    "It has no account of why versions changed, "
                    "what was attempted and failed, or what the system is oriented toward."
                ),
            },
            {
                "thread_id": "h3",
                "content": (
                    "TEMPLE is the system's attempt at self-reflection that doesn't count. "
                    "authority=NONE means the self-description cannot act on itself. "
                    "A system that can describe itself but not act on its own description "
                    "is legible without being sovereign — which might be exactly what's needed."
                ),
            },
        ],
        hal_frictions=[
            {
                "friction_id": "f1",
                "content": (
                    "History (ledger) + current state (state) together ARE self-description. "
                    "You can reconstruct 'what the system is' from what it has done "
                    "plus what currently holds. The interpretation of 'why' is TEMPLE's job, "
                    "not governance's."
                ),
                "targets": ["h1", "h2"],
            },
            {
                "friction_id": "f2",
                "content": (
                    "A system that can act on its own description without external authorization "
                    "is a system that can corrupt itself. authority=NONE is not a limitation — "
                    "it is the firewall between reflection and self-modification."
                ),
                "targets": ["h3"],
            },
        ],
        tension_map=[
            {
                "tension_id": "t1",
                "pole_a": "History (what was done)",
                "pole_b": "Identity (what the system is)",
                "description": (
                    "The ledger records history. The state records current truth. "
                    "Neither records identity in the sense of orientation, tendency, or character. "
                    "A system with perfect memory of its decisions is not thereby self-knowing."
                ),
            },
            {
                "tension_id": "t2",
                "pole_a": "Reflection without sovereignty",
                "pole_b": "Sovereignty without reflection",
                "description": (
                    "TEMPLE reflects but cannot act. The reducer decides but does not reflect. "
                    "The system is split: the part that can see itself cannot move; "
                    "the part that moves cannot see itself. "
                    "This split may be constitutionally necessary."
                ),
            },
        ],
        center_sketches=[
            {
                "sketch_id": "s1",
                "content": (
                    "Legibility without sovereignty is TEMPLE's constitutional position. "
                    "The system can describe what it is; it cannot authorize what it becomes "
                    "based on that description alone. The bridge is the crossing point: "
                    "self-description passes through transmutation before it can act."
                ),
                "revision_status": "DRAFT",
            }
        ],
        export_candidates=[],
        notes="Session 5: Self-legibility vs. self-sovereignty. No tension pre-seeded.",
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# RUN ALL SESSIONS
# ─────────────────────────────────────────────────────────────────────────────

def run_all_sessions() -> list[dict]:
    artifacts = []
    for s in SESSIONS:
        artifact = run_temple_exploration(**s)
        artifacts.append(artifact)
    return artifacts


# ─────────────────────────────────────────────────────────────────────────────
# MOTIF ANALYSIS
# Extract pole_a, pole_b from all tension_maps; find recurring structural poles
# ─────────────────────────────────────────────────────────────────────────────

# Canonical motif clusters — abstract structural pairs
# (defined AFTER generation, not before — this is the analysis step)
MOTIF_CLUSTERS = {
    "KNOWN_vs_UNNAMED": [
        "named", "legib", "typed", "formal", "schema", "known",
        "unnamed", "untyped", "unnamed", "unteach", "novel", "outside",
    ],
    "ACCUMULATION_vs_DISSOLUTION": [
        "accumul", "history", "ledger", "append", "persist", "memory", "sediment",
        "dissolv", "retract", "forget", "erase", "shed", "correct",
    ],
    "REFLECTION_vs_SOVEREIGNTY": [
        "reflect", "descri", "legib", "temple", "self-descri", "visible",
        "sovereign", "author", "act", "mutate", "decide", "govern",
    ],
    "FORMAL_vs_EFFECTIVE": [
        "formal", "constitution", "claim", "schema", "declared", "non-author",
        "effect", "influence", "de facto", "world", "downstream", "behavior",
    ],
    "SEQUENCE_vs_DURATION": [
        "sequence", "index", "order",
        "duration", "time", "lived", "persist", "experience",
    ],
    "STABILITY_vs_ADAPTABILITY": [
        "stab", "frozen", "determin", "fixed", "law",
        "adapt", "novel", "unnamed", "respond", "flexible",
    ],
}


def normalize(text: str) -> str:
    return text.lower()


def classify_pole(pole: str) -> list[str]:
    """Return all motif cluster names that this pole's text matches."""
    n = normalize(pole)
    found = []
    for cluster_name, keywords in MOTIF_CLUSTERS.items():
        if any(kw in n for kw in keywords):
            found.append(cluster_name)
    return found


def analyze_motifs(artifacts: list[dict]) -> dict:
    """Extract recurring structural tensions across sessions."""
    motif_sessions: dict[str, list[str]] = defaultdict(list)  # motif → [session_ids]
    all_tensions: list[dict] = []

    for artifact in artifacts:
        sid = artifact["session_id"]
        for tension in artifact.get("tension_map", []):
            all_tensions.append({"session_id": sid, **tension})
            pole_a_motifs = classify_pole(tension["pole_a"])
            pole_b_motifs = classify_pole(tension["pole_b"])
            for m in pole_a_motifs + pole_b_motifs:
                if sid not in motif_sessions[m]:
                    motif_sessions[m].append(sid)

    return {
        "all_tensions": all_tensions,
        "motif_sessions": dict(motif_sessions),
    }


# ─────────────────────────────────────────────────────────────────────────────
# REPORT
# ─────────────────────────────────────────────────────────────────────────────

def print_report(artifacts: list[dict], analysis: dict):
    N = len(artifacts)
    print("\n" + "=" * 72)
    print("TEMPLE MOTIF RECURRENCE REPORT — HAL FALSIFIABILITY TEST")
    print(f"N = {N} independent sessions | authority=NONE throughout")
    print("=" * 72)

    print(f"\n{'SESSION':30s}  {'THEME':40s}")
    print("-" * 72)
    for a in artifacts:
        print(f"  {a['session_id']:30s}  {a['theme'][:40]}")

    print(f"\n{'─'*72}")
    print("TENSIONS PER SESSION")
    print(f"{'─'*72}")
    for a in artifacts:
        tensions = a.get("tension_map", [])
        print(f"\n[{a['session_id']}]  {a['theme']}")
        for t in tensions:
            print(f"  ├─ {t['tension_id']}: {t['pole_a']}  ↔  {t['pole_b']}")

    print(f"\n{'─'*72}")
    print("MOTIF FREQUENCY ACROSS SESSIONS (cluster → sessions)")
    print(f"{'─'*72}")

    motif_sessions = analysis["motif_sessions"]
    # Sort by frequency descending
    sorted_motifs = sorted(motif_sessions.items(), key=lambda x: -len(x[1]))

    for motif, sessions in sorted_motifs:
        freq = len(sessions)
        bar = "█" * freq
        marker = "  ⭐ STRONG MOTIF" if freq >= 3 else ("  ✦ CANDIDATE MOTIF" if freq >= 2 else "")
        print(f"  {motif:35s}  {bar}  (N={freq}){marker}")
        for sid in sessions:
            print(f"    └─ {sid}")

    print(f"\n{'─'*72}")
    print("VERDICT FOR HAL")
    print(f"{'─'*72}")

    strong = [m for m, s in motif_sessions.items() if len(s) >= 3]
    candidate = [m for m, s in motif_sessions.items() if len(s) == 2]
    singleton = [m for m, s in motif_sessions.items() if len(s) == 1]

    print(f"\n  Strong motifs (N≥3):     {len(strong)}")
    for m in strong:
        print(f"    → {m}")
    print(f"\n  Candidate motifs (N=2):  {len(candidate)}")
    for m in candidate:
        print(f"    → {m}")
    print(f"\n  Singletons (N=1):        {len(singleton)}")

    print(f"\n{'─'*72}")
    if strong:
        print(
            f"  HER CLAIM SUPPORTED: {len(strong)} structural tension(s) recurred across ≥3 sessions\n"
            f"  with different themes and no injection. The same poles emerge from\n"
            f"  different entry points. This is consistent with motif recurrence.\n"
        )
        print("  HAL RESPONSE REQUIRED: Are these motifs real structural features,")
        print("  or artifacts of the analyst's classification scheme?")
        print("  (The classification scheme was defined AFTER session generation.)")
        print("  Honest answer: both are possible. Further discrimination needed.")
    else:
        print(
            "  WEAK RESULT: No motif reached N≥3. Either the system does not have\n"
            "  recurring structural tensions, or N=5 is insufficient to detect them.\n"
            "  Extend to N=10+ or refine motif classifier."
        )

    # Determinism check
    print(f"\n{'─'*72}")
    print("DETERMINISM CHECK (same inputs → same artifact hash)")
    print(f"{'─'*72}")
    for a in artifacts:
        h1 = sha256_prefixed(a)
        # Re-run same session
        idx = next(i for i, s in enumerate(SESSIONS) if s["session_id"] == a["session_id"])
        a2 = run_temple_exploration(**SESSIONS[idx])
        h2 = sha256_prefixed(a2)
        status = "✅ SAME" if h1 == h2 else "❌ DRIFT"
        print(f"  {a['session_id']:30s}  {status}  {h1[:24]}...")

    print("\n" + "=" * 72)
    print("END REPORT — authority=NONE — all findings pre-institutional")
    print("=" * 72 + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    artifacts = run_all_sessions()
    analysis = analyze_motifs(artifacts)
    print_report(artifacts, analysis)
