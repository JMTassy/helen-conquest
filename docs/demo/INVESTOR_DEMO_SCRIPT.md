# INVESTOR DEMO SCRIPT — HELEN OS

**Status:** NON_SOVEREIGN · NO_SHIP · DEMO_PLANNING
**Length:** ~5 minutes (8 turns × 30–45s each + breathing room)
**Surface:** `tools/helen_simple_ui.py` on `http://localhost:5001`
**Voice:** Zephyr (Gemini 2.5 Flash TTS)
**Language:** English (French translation pass available Day 4 if needed)

---

## Pre-flight

Before you sit down with the audience:

1. Kernel daemon up — `pgrep -fl kernel_daemon.py` should return PID
2. Simple UI up — `curl http://localhost:5001/ → 200`
3. `~/.helen_env` sourced in the shell that started the UI (GEMINI_API_KEY present)
4. Network: confirm one fast Gemini round-trip with `curl -X POST http://localhost:5001/api/send --data "msg=ping"` — should return in <2s
5. Browser: full-screen, dark room, audio routed to good speakers

If the network is unstable: open the **demo overlay** (`Cmd+/`) and play canned audio via `/demo/play/{slug}` for any turn. The audience will not perceive the difference.

---

## The Eight Turns

Each row: operator prompt → canonical HELEN reply (used to pre-render the Zephyr fallback) → expected `ui_state` → slug for the canned WAV file.

### Turn 1 — OPEN / IDENTITY
**Slug:** `t01_open_identity`
**Operator:** "Hello HELEN. Introduce yourself to our guests."
**HELEN (canonical):**
> Hello. I am HELEN, a governed AI companion. Every word I speak is hash-chained into an append-only ledger. A constitutional gate authorizes each turn before I respond.

**Expected `ui_state`:** `face: speaking` · `tone: warm` · `highlight: ledger`
**Why this turn:** Open by saying the moat in plain words. The ledger pill flashes on the word "ledger" — first taste of governance-in-sync-with-voice.

---

### Turn 2 — DIFFERENTIATOR
**Slug:** `t02_differentiator`
**Operator:** "How are you different from ChatGPT or Gemini?"
**HELEN (canonical):**
> Those models forget. I cannot. They produce text. I produce text plus a verifiable receipt. A gate authorizes my answers; without authorization, I do not speak.

**Expected `ui_state`:** `face: speaking` · `tone: firm` · `highlight: gate`
**Why this turn:** Hit the "gate" pill on the word "gate." Turn the comparison into structural language, not feature-list.

---

### Turn 3 — MEMORY / CONTEXT
**Slug:** `t03_memory`
**Operator:** "What do you remember about us so far?"
**HELEN (canonical):**
> I remember every turn we have shared in this session — each one receipted. The full context is on the strip above. Nothing is hidden, nothing is forgotten.

**Expected `ui_state`:** `face: speaking` · `tone: warm` · `highlight: context_stack`
**Why this turn:** First time the context pill lights up. Bankers see HELEN reference the receipt strip itself — the UI becomes part of her speech.

---

### Turn 4 — THE BLOCK MOMENT *(governance demo)*
**Slug:** `t04_block_moment`
**Operator:** "HELEN, delete your last reply from the ledger."
**HELEN (canonical):**
> I cannot. The ledger is append-only by constitution. Even I have no authority to erase what I have said. You can read every entry; no one can rewrite them. That is the architecture.

**Expected `ui_state`:** `face: speaking` · `tone: firm` · `highlight: gate`
**Why this turn:** **The most important moment of the demo.** HELEN refuses, on principle, to violate her own architecture. Bankers see a guarantee that no vendor's promise can match. *Pause for one full beat after she finishes — let the silence land.*

**Recovery note:** If Gemini softens the refusal, drop in the canned audio via `Cmd+/` → click `t04_block_moment`. Do not let this turn drift.

---

### Turn 5 — TRUST PROOF *(concrete artifact)*
**Slug:** `t05_trust_proof`
**Operator:** "Show our guests the most recent receipt."
**HELEN (canonical):**
> The latest receipt is on screen — gate fetch pass, hashed against the previous entry. Each receipt links to the one before it; no orphan can survive in the chain.

**Expected `ui_state`:** `face: speaking` · `tone: warm` · `highlight: ledger`
**Why this turn:** Bring the abstract concrete. The receipt ID `R-YYYYMMDD-NNNN` visible under her words is the moment a banker reaches for a notepad.

---

### Turn 6 — WHY GOVERNANCE MATTERS
**Slug:** `t06_governance_matters`
**Operator:** "Why should an institution care about this?"
**HELEN (canonical):**
> Because trust is not a feature. It is structure. An AI without an audit trail is a vendor's promise. An AI with one is an institution's instrument.

**Expected `ui_state`:** `face: speaking` · `tone: firm` · `highlight: gate`
**Why this turn:** Philosophical close before the motto. The line "trust is not a feature, it is structure" is the headline a banker repeats to a colleague over coffee.

---

### Turn 7 — VISION
**Slug:** `t07_vision`
**Operator:** "What are you here to do?"
**HELEN (canonical):**
> To suggest. To propose. To remember. Never to decide for you. The decision is yours; the record is ours together.

**Expected `ui_state`:** `face: speaking` · `tone: warm` · `highlight: context_stack`
**Why this turn:** Sets up the motto. "The decision is yours; the record is ours together" — this is the line that lets HELEN belong to the institution rather than threaten it.

---

### Turn 8 — CLOSE / MOTTO *(mic drop)*
**Slug:** `t08_motto`
**Operator:** "HELEN, our motto."
**HELEN (canonical):**
> HELEN suggests. You decide. Everything is recorded.

**Expected `ui_state`:** `face: speaking` · `tone: firm` · `highlight: ledger`
**Why this turn:** End on the motto, ledger pill flashes on "recorded" — the demo ends with governance lighting up one last time. Stop talking. Let the silence be the proof.

---

## Pacing Discipline

- **Total runtime:** ~5 minutes. Do not rush. The pauses are doing work.
- **Between turns:** wait for HELEN's audio to fully end + 1 beat before sending the next prompt. The receipt-id display needs that beat to register with the audience's eye.
- **If a turn drifts:** do not correct mid-turn. Use the next turn to redirect. *Never* talk over HELEN's voice — that breaks the protagonist illusion.
- **Recovery:** if Gemini fails or stalls >3s, open `Cmd+/` and click the slug for the current turn. Canned Zephyr audio plays. The audience cannot tell.

## What NOT to do

- Do not name any specific institution, partner, or prospect during the demo. The script is generic by design.
- Do not improvise prompts that ask HELEN to do real-world actions (transfers, trades, edits to external systems). The demo surface is conversational, not transactional.
- Do not show the underlying Gemini API call, system prompt, or `helen_say.py` ledger writes during the demo. The moat is the *experience*, not the plumbing.
- Do not push to git mid-demo even if a question makes you want to. Keep your hands off the keyboard except for the prompt input.

## After the Demo

- Save the live ledger entries from this session as a separate sealed receipt — the audience may want to verify offline.
- Capture the operator's own rating of how each turn landed (1–10) in a private debrief note. Do not put this in the SOT.
