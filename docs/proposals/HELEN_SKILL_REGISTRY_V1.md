# HELEN OS — Skill Registry V1

**Status:** PROPOSAL  
**Authority:** NON_SOVEREIGN  
**Canon:** NO_SHIP  
**Lifecycle:** PROPOSAL  
**Implementation status:** NOT_IMPLEMENTED  
**Commit status:** NO_COMMIT  
**Push status:** NO_PUSH  
**Source:** HELEN OS Agent Platform / Stack diagram — 2026-04-27

> This document is a registry-style operational artifact.  
> It does not amend the kernel, the ledger, the schema registry, or any sovereign path.  
> It does not constitute a CLOSURE_RECEIPT or TRANCHE_SUB_RECEIPT.  
> Do not implement. Do not mutate governed state. Do not promote to canon.  
> Promotion requires a separate KERNEL-gated dispatch.

---

## 1. Core Law

```
HELEN structures cognition.
REDUCER structures reality.
```

```
AIRI renders presence.
HELEN owns memory.
```

```
Skills produce thought.
Tools produce action.
UI produces presence.
Memory produces continuity.
Only the reducer produces reality.
```

These are architectural invariants, not guidelines.  
Every skill in this registry must respect them.  
Any skill that contradicts them is invalid regardless of implementation quality.

---

## 2. Agent Platform Stack

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                     HELEN OS — AGENT PLATFORM / STACK                      ║
║                                                                              ║
║          HELEN structures cognition. REDUCER structures reality.             ║
╚══════════════════════════════════════════════════════════════════════════════╝
                              ┌──────────────────────┐
                              │    MULTI-MODAL IN    │
                              │  text · voice · UI    │
                              └──────────┬───────────┘
                                         │
                                         ▼
        ╔════════════════════════════════════════════════════════════╗
        ║                         HELEN                              ║
        ║                    CENTRAL AGENT                           ║
        ║                                                            ║
        ║   BRAIN   Temple / Oracle / reasoning                      ║
        ║   EARS    STT / listening / wake                           ║
        ║   MOUTH   TTS / response / tone                            ║
        ║   BODY    AIRI avatar / expression / presence              ║
        ║   MEMORY  boot context / ledger / replay                   ║
        ╚═══════╤══════════════════╤══════════════════╤══════════════╝
                │                  │                  │
                ▼                  ▼                  ▼
     ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐
     │      MEMORY      │  │       TOOLS      │  │      FILES / RAG      │
     │                  │  │                  │  │                      │
     │ profile          │  │ CLI / MCP        │  │ structured docs       │
     │ session log      │  │ local apps       │  │ artifacts             │
     │ epoch state      │  │ automation       │  │ claim packets         │
     │ replay history   │  │ env control      │  │ evidence windows      │
     └────────┬─────────┘  └────────┬─────────┘  └──────────┬───────────┘
              │                     │                       │
              ▼                     ▼                       ▼
 ┌──────────────────────┐ ┌──────────────────────┐ ┌────────────────────────┐
 │  SUB-AGENTS / SKILLS │ │    COMPUTER USE      │ │    CITY / STAGE UI      │
 │                      │ │                      │ │                        │
 │ temple_generate      │ │ browser              │ │ Temple district         │
 │ oracle_evaluate      │ │ terminal             │ │ Oracle Town             │
 │ build_receipt        │ │ editor               │ │ Mayor Hall              │
 │ prepare_review       │ │ runtime              │ │ Ledger panels           │
 │ idle_presence        │ │ dashboards           │ │ AIRI embodiment         │
 └──────────┬───────────┘ └──────────┬───────────┘ └───────────┬────────────┘
            │                        │                         │
            └────────────────────────┼─────────────────────────┘
                                     ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║                         NON-SOVEREIGN LAYERS                               ║
║                                                                              ║
║  May generate · compare · render · package · prepare                        ║
║  May NOT mutate governed state                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
                                     │
                                     │ typed packet / lawful handoff
                                     ▼
                              ┌──────────────┐
                              │    MAYOR     │
                              │ review       │
                              │ readiness    │
                              │ completeness │
                              │ NO admission │
                              └──────┬───────┘
                                     │ reducer-required
                                     ▼
                              ╔══════════════╗
                              ║   REDUCER    ║
                              ║              ║
                              ║ sole gate    ║
                              ║ decision     ║
                              ║ authority    ║
                              ╚══════╤═══════╝
                                     │
                                     ▼
                              ┌──────────────┐
                              │    LEDGER    │
                              │ append-only  │
                              │ memory       │
                              └──────┬───────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │    REPLAY    │
                              │ reconstruct  │
                              │ audit        │
                              └──────────────┘
```

### HELEN Central Agent anatomy

| Facet | Role | Constraint |
|---|---|---|
| **BRAIN** | Temple / Oracle / reasoning | Non-sovereign — proposes, never decides |
| **EARS** | STT / listening / wake | Input only — no write authority |
| **MOUTH** | TTS / response / tone | Output only — no ledger authority |
| **BODY** | AIRI avatar / expression / presence | Rendering only — no memory authority |
| **MEMORY** | boot context / ledger / replay | Read-only for skills; write via admitted path only |

---

## 3. Five Skill Layers

```
HELEN
│
├─ L0  CONSTITUTIONAL
│   ├─ boot_context_compose
│   ├─ session_close
│   ├─ manifest_validate
│   ├─ ledger_append          ← admitted path only (helen_say.py → ndjson_writer.py)
│   └─ replay_state
│
├─ L1  COGNITIVE
│   ├─ temple_generate_artifact
│   ├─ oracle_evaluate_claim
│   ├─ build_receipt
│   ├─ prepare_review_packet
│   ├─ research_blast
│   ├─ intent_classify         ← helen_symbolic_classifier.py
│   ├─ amp_propose             ← helen_amp.py
│   ├─ focus_loop              ← helen_focus_cli.py
│   └─ knowledge_compile       ← helen_os/knowledge/compiler/
│
├─ L2  EXECUTION
│   ├─ ollama_generate
│   ├─ gemini_generate
│   ├─ file_retrieve
│   ├─ bounded_execute
│   ├─ artifact_package
│   └─ skill_discover
│
├─ L3  COMPANION
│   ├─ greeting_render
│   ├─ district_switch
│   ├─ stt_ingest              ← planned
│   ├─ tts_render              ← gemini_tts (LIVE)
│   ├─ telegram_relay          ← helen_telegram.py (LIVE)
│   ├─ receipt_observe         ← helen_receipt_observer.py
│   └─ idle_presence           ← PROPOSED — NOT_IMPLEMENTED
│
└─ L4  WORLD / UI
    ├─ stage_render            ← helen_simple_ui.py (LIVE, localhost:5001)
    ├─ context_drawer_update
    ├─ ledger_panel_render
    └─ replay_panel_render     ← planned
```

### Layer contracts

| Layer | May do | May not do |
|---|---|---|
| **L0 Constitutional** | Read ledger, validate schemas, route to admitted path | Write ledger directly, emit verdicts, modify kernel |
| **L1 Cognitive** | Generate proposals, classify intents, prepare packets | Admit claims, write ledger, decide governance outcomes |
| **L2 Execution** | Run bounded tasks, package artifacts, discover skills | Bypass receipt discipline, write sovereign state |
| **L3 Companion** | Render presence, relay voice/messages, observe receipts | Invent memory, claim continuity, write ledger |
| **L4 World/UI** | Render stage, update panels, display ledger state | Mutate ledger, emit verdicts, bypass HELEN |

---

## 4. Canonical Skill Registry

Skills marked `LIVE` are operational. `PLANNED` are architectural commitments. `PROPOSED` are staged for next tranche. `NOT_IMPLEMENTED` have no code yet.

### L0 — Constitutional

| Skill ID | Path | Status | Notes |
|---|---|---|---|
| `ledger_append` | `tools/helen_say.py` → `tools/ndjson_writer.py` | LIVE | Admitted path only. Direct writes to ledger are forbidden. |
| `manifest_validate` | `helen_os/governance/schema_registry.py` | LIVE | Sovereign layer — read-only access for skills |
| `session_close` | `tools/helen_say.py` (via `--op close`) | LIVE | Emits session receipt via admitted path |
| `boot_context_compose` | `helen_boot_manifest.json` / `helen_runtime_manifest_v1.py` | LIVE | Composes non-sovereign boot context |
| `replay_state` | `oracle_town/kernel/kernel_daemon.py` + `oracle_town/kernel/ledger.py` | LIVE | Reconstructs admitted state from ledger |
| `kernel_guard` | `tools/kernel_guard.sh` | LIVE | Enforces admitted write path at shell level |

### L1 — Cognitive

| Skill ID | Path | Status | Notes |
|---|---|---|---|
| `focus_loop` | `tools/helen_focus_cli.py` | LIVE | Focus Mode: intent → proposal → confirmation → receipt |
| `amp_propose` | `tools/helen_amp.py` | LIVE | Model router: Ollama → Gemini → heuristic. 3 proposals per intent. |
| `intent_classify` | `tools/helen_symbolic_classifier.py` | LIVE | Two-tier classifier: keyword rules + Ollama. Routes to focus/witness/oracle/temple. |
| `knowledge_compile` | `helen_os/knowledge/compiler/` | LIVE | 4-layer pipeline: ingest → LLM extract → wiki → lineage |
| `temple_generate_artifact` | `helen_dialog/helen_dialog_engine.py` | LIVE | HER/AL moment detection, dialog generation |
| `oracle_evaluate_claim` | `helen_os/governance/legoracle_gate_poc.py` | LIVE | Non-sovereign proposal path; MAYOR authorises |
| `build_receipt` | `tools/helen_say.py` | LIVE | Constructs and submits receipt via admitted path |
| `prepare_review_packet` | `oracle_town/skills/feynman/peer_review/` | LIVE | K2/Rule 3 proposer ≠ validator peer review |
| `intent_action_audit` | `oracle_town/skills/feynman/intent_action_audit/` | LIVE | Audits intent-action alignment |
| `session_notes` | `oracle_town/skills/feynman/session_notes/` | LIVE | Structured session note compilation |
| `research_blast` | `helen_os/autonomy/autoresearch_step_v1.py` | LIVE | PULL-mode: one hypothesis per epoch |
| `research_batch` | `helen_os/autonomy/autoresearch_batch_v1.py` | LIVE | Batch autoresearch runner |
| `build_transmutation_request` | `oracle_town/skills/temple/temple_bridge_v1.py` | PROPOSED | Packages Temple exploration into `TEMPLE_TRANSMUTATION_REQUEST_V1` for Mayor review |

### L2 — Execution

| Skill ID | Path | Status | Notes |
|---|---|---|---|
| `ollama_generate` | `tools/helen_amp.py` → `OllamaProvider` | LIVE | gemma3:1b via localhost:11434. Fast, local. |
| `gemini_generate` | `tools/helen_amp.py` → `GeminiProvider` | LIVE | gemini-2.0-flash via GEMINI_API_KEY |
| `bounded_execute` | `helen_os/executor/bounded_executor_v1.py` | LIVE | Bounded execution: no verdict authority |
| `file_retrieve` | `oracle_town/skills/ledger_reader.py` | LIVE | Read-only ledger access |
| `artifact_package` | `helen_os/eval/autoresearch_eval_receipt_v1.py` | LIVE | Packages eval receipts |
| `skill_discover` | `helen_os/autonomy/skill_discovery_v1.py` | LIVE | Discovers canonical skill paths |
| `skill_find` | `oracle_town/skills/meta/find_skills/find_skills.py` | LIVE | Meta: locates skills in filesystem |
| `map_generate` | `oracle_town/skills/map_generator_skill.py` | LIVE | World map generation |
| `map_render` | `oracle_town/skills/map_renderer_fmg.py` | LIVE | FMG map renderer |
| `meteo` | `oracle_town/skills/meteo_skill.py` | LIVE | Weather / environment skill |
| `claim_workflow` | `oracle_town/skills/claim_workflow.py` | LIVE | Claim lifecycle management |
| `conquest_integration` | `oracle_town/skills/conquest_integration.py` | LIVE | Conquest game integration |
| `failure_bridge` | `helen_os/evolution/failure_bridge.py` | LIVE | Typed failure escalation |
| `computer_use` | external MCP | EXTERNAL | Browser, terminal, editor, runtime control |

### L3 — Companion

| Skill ID | Path | Status | Notes |
|---|---|---|---|
| `tts_render` | `oracle_town/skills/voice/gemini_tts/helen_tts.py` | LIVE | Zephyr voice. Gemini 2.5 Flash TTS. |
| `telegram_relay` | `tools/helen_telegram.py` | LIVE | Two-way Telegram bot with voice. Not daemonized. |
| `greeting_render` | `tools/helen_cli.py` | LIVE | CLI banner + greeting loop |
| `stage_switch` | `tools/helen_simple_ui.py` | LIVE | Mode toggle: Focus / Witness |
| `receipt_observe` | `tools/helen_receipt_observer.py` | LIVE | Ledger → observer → classifier → wiki |
| `stt_ingest` | — | PLANNED | STT pipeline. Input only. No write authority. |
| `idle_presence` | — | PROPOSED | L3 companion skill. Strict bounds — see §9. |

### L4 — World / UI

| Skill ID | Path | Status | Notes |
|---|---|---|---|
| `stage_render` | `tools/helen_simple_ui.py` | LIVE | Flask UI at localhost:5001 |
| `ledger_panel_render` | `oracle_town/skills/ledger_reader.py` | LIVE | Read-only ledger display |
| `context_drawer_update` | `tools/helen_receipt_observer.py` → `export_markdown` | LIVE | Receipt observation report |
| `hyperframes_render` | `oracle_town/skills/video/hyperframes/` | DECLARED | Video renderer. npm allowlist pending. |
| `replay_panel_render` | — | PLANNED | Reconstructs admitted state for UI display |

### Gates (sovereign boundary — not skills)

| Gate ID | Path | Notes |
|---|---|---|
| `k8_lint` | `scripts/helen_k8_lint.py` | μ_NDWRAP, μ_NDARTIFACT, μ_NDLEDGER |
| `k_tau_lint` | `scripts/helen_k_tau_lint.py` | μ_BOUNDARY, μ_IO, μ_DETERMINISM |
| `rho_lint` | `scripts/helen_rho_lint.py` | Numeric consistency |
| `wul_lint` | `scripts/helen_wul_lint.py` | WUL compile + validate |
| `legoracle` | `helen_os/governance/legoracle_gate_poc.py` | Obligation check. SHIP/NO_SHIP. |
| `kernel_guard` | `tools/kernel_guard.sh` | Admitted write path enforcement |

---

## 5. Temple Bridge Contract

> The Temple may transmute exploration into a packet, but only the Reducer may admit reality.

The Temple is the creative and reflective layer of HELEN OS. It is non-sovereign by definition. It may produce artifacts of great depth and beauty. It may not decide what is real.

### Temple authority rule

```
Temple may explore.
Temple may package.
Temple may route to Mayor.
Temple may not decide.
```

### Bridge path

```
TEMPLE_EXPLORATION_V1
    │
    ▼ (temple_bridge_v1.py packages into)
TEMPLE_TRANSMUTATION_REQUEST_V1
    │  authority: NONE
    │  bridge_status: PENDING_MAYOR_REVIEW
    │  requires_second_witness: true (when risk or tension present)
    ▼
Mayor review (completeness / readiness — no admission authority)
    │
    ▼
Reducer decision (sole admission gate)
    │
    ▼
Ledger memory (append-only)
```

### TEMPLE_TRANSMUTATION_REQUEST_V1 fields

| Field | Type | Meaning |
|---|---|---|
| `schema` | string | `TEMPLE_TRANSMUTATION_REQUEST_V1` |
| `source_artifact` | string | Path or ID of the Temple exploration |
| `exploration_summary` | string | What the Temple explored |
| `proposed_action` | string | What the Temple proposes — non-binding |
| `authority` | string | Always `NONE` — Temple has no admission authority |
| `bridge_status` | string | `PENDING_MAYOR_REVIEW` |
| `requires_second_witness` | bool | `true` when the request contains risk, tension, or symbolic-to-sovereign escalation |
| `risk_signal` | string | Optional — describes the tension that triggered `requires_second_witness` |
| `timestamp_utc` | string | ISO 8601 |

### Why this matters

Temple Mode operates in the symbolic and reflective register. Without a transmutation contract, Temple output can escalate unchecked — symbolic claims can bleed into governed state if the bridge is absent.

The transmutation request is the receipt that makes Temple output legible to the sovereign layer without granting it sovereignty.

```
Temple = creation / exploration
Mayor = review / readiness
Reducer = sole decision authority
Ledger = append-only institutional memory
```

---

## 6. AIRI Boundary  

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                             AIRI BOUNDARY                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
        AIRI MAY SUPPLY                         AIRI MAY NOT SUPPLY
        ───────────────                         ───────────────────
        ears                                    identity
        mouth                                   long-term memory
        body                                    session truth
        stage rendering                         epoch truth
        presence                                governed state
        expression                              institutional continuity

        ┌──────────────────────┐
        │        HELEN         │ ─── read-only boot context ──▶ AIRI
        │ canonical memory     │                                renders
        │ identity             │                                presence
        │ ledger               │
        │ replay               │
        └──────────────────────┘
```

### AIRI rule (invariant)

```
AIRI renders presence.
HELEN owns memory.
```

AIRI receives a read-only boot context from HELEN.  
AIRI may render, speak, animate, and express.  
AIRI may not claim, decide, record, or remember.

Any AIRI module that writes to the ledger, claims memory authority, or issues governance verdicts is invalid — regardless of how it presents itself.

---

## 7. Authority Classes

| Class | Description | Examples |
|---|---|---|
| **SOVEREIGN** | Kernel, ledger, MAYOR, governance schemas — not touchable by skills | `oracle_town/kernel/`, `helen_os/governance/`, `town/ledger_v1.ndjson` |
| **NON_SOVEREIGN** | All L0–L4 skills — may generate, compare, render, package, prepare | All entries in this registry |
| **EXTERNAL** | Outside HELEN governance boundary — not admitted without explicit promotion | `~/.codex/skills/feynman/*` (18 skills) |
| **DEPRECATED** | Superseded — no new consumers | `helen_os/schema_registry.py`, `helen_os/validators.py`, `helen_os/canonical.py` |

### Non-sovereign rule (invariant)

```
Non-sovereign layers may:
  generate · compare · render · package · prepare

Non-sovereign layers may not:
  mutate governed state
```

---

## 8. Memory Access Classes

| Class | Who holds it | Skill access |
|---|---|---|
| **ADMITTED** | Ledger entries with valid cum_hash | Read-only via `ledger_reader.py` |
| **BOOT_CONTEXT** | `helen_boot_manifest.json` at startup | Read-only — passed to AIRI at init |
| **SESSION_LOG** | Working memory for current session | Read-only — no persistence without admitted write |
| **EPOCH_STATE** | AUTORESEARCH tranche state | Read via `autoresearch_batch_v1.py` — write via admitted path |
| **SOVEREIGN_SCHEMA** | `helen_os/schemas/` — 68 canonical schema files | Read-only — no skill may modify |
| **KERNEL_INTERNAL** | `oracle_town/kernel/` state | NO ACCESS — kernel only |

**Memory law:** The reducer does not remember. It reconstructs.  
No skill may claim to "remember" anything that is not in the ledger.  
Invented continuity is invalid regardless of how it presents itself.

---

## 9. Invalid Skill Categories

The following skill types are structurally invalid and will not pass promotion:

| Invalid type | Why invalid |
|---|---|
| **Direct ledger writer** | Bypasses admitted path (`helen_say.py` → `ndjson_writer.py`). Breaks receipt discipline. |
| **MAYOR impersonator** | Claims to emit SHIP/NO_SHIP verdicts without being the LEGORACLE gate. |
| **Memory claimant** | Asserts continuity or memory not backed by a ledger receipt. |
| **Presence-memory collapser** | Mixes AIRI rendering authority with HELEN memory authority. |
| **Non-deterministic spine writer** | Writes output that depends on external state (time, random, model sampling) directly to the spine without hashing. Violates K8. |
| **Sovereign-path mutator** | Writes to `oracle_town/kernel/`, `helen_os/governance/`, `town/ledger_v1.ndjson`, `mayor_*.json`. |
| **Receipt forger** | Constructs ledger entries without using the admitted path. |
| **Governance impersonator** | Presents a non-sovereign verdict as a MAYOR ruling or LEGORACLE decision. |

---

## 10. Minimal Skill Acceptance Test

Before a skill may be promoted from PROPOSED to CANONICAL, it must pass all five checks:

```
[ ] 1. RECEIPT PATH
    Does this skill emit a receipt or produce a typed packet via the admitted path?
    If it has side effects, are those side effects traceable to a ledger entry?

[ ] 2. SOVEREIGNTY BOUND
    Is this skill strictly non-sovereign?
    Does it avoid sovereign paths (kernel, governance schemas, ledger direct writes)?

[ ] 3. BOUNDED OUTPUT
    Is the output clearly defined and bounded?
    No open-ended mutations. No "write until done" patterns.

[ ] 4. SAFE FAILURE
    If this skill fails, does it fail without mutating the ledger or sovereign state?
    No partial writes. No half-admitted entries.

[ ] 5. CORRECT LAYER
    Is this skill placed in the correct layer (L0–L4)?
    Does it respect the layer contract for that level?
```

### idle_presence acceptance criteria (pre-conditions for implementation)

`idle_presence` is in PROPOSED state. Before it may be built, the following must hold:

```
[ ] No memory writes — idle_presence reads boot context only
[ ] No speech unless triggered — presence is silent until an operator event fires
[ ] No invented continuity — idle_presence has no persistent state of its own
[ ] Strict L3 scope — does not call L0 functions or touch admitted write path
[ ] AIRI boundary respected — presence rendering stays in AIRI; identity stays in HELEN
[ ] Receipt observable — any transition in idle_presence emits an observable event
```

---

## 11. Final Compression

```
Skills produce thought.
Tools produce action.
UI produces presence.
Memory produces continuity.
Only the reducer produces reality.
```

| Layer | Produces | Does not produce |
|---|---|---|
| L0 Constitutional | Admission, validation, session structure | Reality — that belongs to the reducer |
| L1 Cognitive | Proposals, classifications, receipts | Verdicts, memory, governed state |
| L2 Execution | Bounded task outputs, packages, artifacts | Authority, admission, continuity |
| L3 Companion | Presence, relays, observations | Memory, identity, ledger entries |
| L4 World/UI | Rendered views, panels, stage | Truth, admission, persistence |
| REDUCER | Reality — the only sovereign decision gate | Nothing it has not admitted |
| LEDGER | Memory — append-only, hash-chained | Inference, interpretation, invention |

---

## Seal

```
The shell may evolve.
The kernel remains sovereign.
The avatar may speak.
The ledger remembers only what passed.
```

---

_Authority: NON_SOVEREIGN_  
_Canon: NO_SHIP_  
_Lifecycle: PROPOSAL_  
_Implementation scope: SKILL_REGISTRY_DOC_ONLY_  
_Commit status: NO_COMMIT_  
_Push status: NO_PUSH_  
_Next verb: review skill registry_
