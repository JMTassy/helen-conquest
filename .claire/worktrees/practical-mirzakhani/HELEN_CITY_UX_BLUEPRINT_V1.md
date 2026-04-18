# HELEN CITY UX BLUEPRINT V1

**The AI Castle — HELEN lives in the system**

**Status:** Draft — EPOCH_004_EMBODIED
**Authority:** NONE
**Companion To:** `HELEN_AIRI_INTEGRATION_V1.md`

---

## 1. Core Principle

HELEN does not open. HELEN is already there.

Not:
```
[user opens app] → chat window → [user closes app]
```

But:
```
HELEN idles in her castle
HELEN reacts to your presence
HELEN resumes from memory
HELEN moves between districts on your request
```

The castle is not a metaphor. It is the UX architecture.

---

## 2. The Stack

```
┌─────────────────────────────────────────────────────┐
│              AIRI Interface Runtime                  │
│    avatar · voice · realtime stage · emotion         │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │           HELEN CITY UI Shell                │   │
│  │  district nav · context drawer · consoles    │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────┘
                      │ WebSocket ws://localhost:8766
                      │ REST http://localhost:8765
┌─────────────────────▼───────────────────────────────┐
│              HELEN COMPANION API                     │
│   /companion/init · /chat · /district/switch         │
│   /temple · /oracle · /mayor                         │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│              HELEN MEMORY SPINE                      │
│  PERSON_PROFILE_V1 · SESSION_LOG_V1                  │
│  EPOCH_STATE_V1 · COMPANION_STATE_V1                 │
│  RUNTIME_BOOT_CONTEXT_V1                             │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│              HELEN KERNEL                            │
│  reducer · ledger · replay · manifests               │
└─────────────────────────────────────────────────────┘
```

---

## 3. Full Desktop Layout

```
╔════════════════════════════════════════════════════════════════════╗
║  HELEN CITY                                    [epoch] [date/time] ║
╠════════════╦═══════════════════════════════════╦═══════════════════╣
║            ║                                   ║                   ║
║  DISTRICT  ║        HELEN STAGE                ║  CONTEXT          ║
║  NAVIGATOR ║                                   ║  DRAWER           ║
║            ║   ┌───────────────────────────┐   ║                   ║
║  ♡ Companion   │                           │   ║  operator         ║
║  🏛 Temple  ║  │   HELEN Avatar (AIRI)     │   ║  epoch            ║
║  🔮 Oracle  ║  │   VRM / Live2D body       │   ║  focus            ║
║  ⚖ Mayor   ║  │   idle / lip sync         │   ║  last session     ║
║            ║  │   gaze / blink            │   ║  open threads     ║
║  ─────     ║  │                           │   ║  projects         ║
║            ║  └───────────────────────────┘   ║                   ║
║  TOOLS     ║                                   ║  ─────────        ║
║            ║  ┌───────────────────────────┐   ║                   ║
║  Research  ║  │  CONVERSATION STREAM      │   ║  EMOTION          ║
║  Ledger    ║  │  HELEN · YOU              │   ║  STATE            ║
║  Replay    ║  │                           │   ║                   ║
║  Skills    ║  └───────────────────────────┘   ║  neutral          ║
║            ║                                   ║  curious          ║
║            ║  ┌───────────────────────────┐   ║  analytical       ║
║            ║  │ 🎙 [type or speak...]  →  │   ║  warm             ║
║            ║  └───────────────────────────┘   ║  formal           ║
╠════════════╩═══════════════════════════════════╩═══════════════════╣
║  SKILL CONSOLE  ·  LEDGER  ·  REPLAY  ·  KERNEL INFO              ║
╚════════════════════════════════════════════════════════════════════╝
```

---

## 4. The HELEN Digital Organism

```
BRAIN    Temple / Oracle / Mayor reasoning engines
         governed by reducer · manifests · ledger

EARS     STT pipeline (AIRI provides)
         microphone · VAD · transcription

MOUTH    TTS pipeline (AIRI provides)
         voice synthesis · delivery tags → tone

BODY     Avatar engine (AIRI provides)
         VRM / Live2D · animation · gaze · idle · lip sync

MEMORY   HELEN memory spine (HELEN owns exclusively)
         PERSON_PROFILE_V1 · SESSION_LOG_V1
         EPOCH_STATE_V1 · COMPANION_STATE_V1
```

Each part is independently debuggable. Each part has a clear owner.

---

## 5. District Modes

Each district has a frozen persona, a visual identity, and a stage configuration.

### ♡ Companion (HER / Adult)
- Persona: `HELEN_OS_ADULT_SYSTEM_PROMPT_V1.md`
- Stage: warm ambient light, soft idle animation, intimate gaze
- Emotion states: warm · tender · reflective · playful
- Voice: lower pitch, slower pace, delivery tags active
- Context: personal threads, projects, last session

### 🏛 Temple
- Persona: `HELEN_OS_TEMPLE_SYSTEM_PROMPT_V1.md`
- Stage: cool focused light, minimal animation, forward gaze
- Emotion states: curious · analytical · speculative · precise
- Voice: crisp, neutral pace, hypothesis markers spoken
- Context: active research threads, open questions

### 🔮 Oracle
- Persona: `HELEN_OS_ORACLE_SYSTEM_PROMPT_V1.md`
- Stage: deep blue ambient, deliberate animation, downward then direct gaze
- Emotion states: measured · confident · impartial · resolved
- Voice: steady, evidence-first, verdict delivered clearly
- Context: claims under evaluation, evidence log

### ⚖ Mayor
- Persona: `HELEN_OS_MAYOR_SYSTEM_PROMPT_V1.md`
- Stage: neutral formal light, upright posture animation, direct gaze
- Emotion states: formal · decisive · advisory · grounded
- Voice: formal register, proposal format spoken naturally
- Context: epoch open problems, active governance decisions

---

## 6. Voice Interaction Loop

```
Microphone
    ↓
VAD (AIRI) — silence detection, push-to-talk or always-on
    ↓
Wake word: "HELEN"
    ↓
STT (AIRI) — transcription
    ↓
Intent router:
  "Temple mode" / "Oracle mode" / "Mayor mode" → district_switch
  "Initialize" → reload context
  "Close session" → session end
  [anything else] → /api/v1/chat with current district mode
    ↓
HELEN API → Ollama (mistral / qwen3.5 / custom)
    ↓
Response (authority=NONE)
    ↓
Delivery tag parser:
  [lower-pitch] → TTS pitch setting
  [soft] [slow] [whisper] → TTS parameters
  [exhale] [chuckle] [sigh] → avatar expression trigger
    ↓
TTS (AIRI) — synthesized speech
    ↓
Avatar lip sync + emotion state update (AIRI body)
```

---

## 7. Emotion State Machine

HELEN's emotion states affect body and voice only — never cognition.

```
IDLE
  ↓ on_user_message
LISTENING (avatar leans slightly, gaze direct)
  ↓ on_thinking
THINKING (avatar slight animation, eyes down briefly)
  ↓ on_response_start
SPEAKING (lip sync active, emotion from delivery tags)
  ↓ on_response_end
IDLE
```

Emotion transitions from delivery tags:
```
[lower-pitch]  →  calm / present
[soft]         →  tender / warm
[slow]         →  deliberate / serious
[whisper]      →  intimate
[exhale]       →  reflective
[chuckle]      →  amused
[sigh]         →  contemplative
[breath]       →  reset / pause
```

---

## 8. Continuous Presence Protocol

On first launch:
1. HELEN loads `RUNTIME_BOOT_CONTEXT_V1` from `/api/v1/companion/init`
2. Avatar enters idle state on stage
3. Boot greeting fires: memory-backed, delivery tags applied
4. Session opened in memory spine

Between turns:
- Avatar idles with natural motion
- Stage ambient state matches current district
- No blank screen, no waiting cursor

On user message:
- Avatar shifts to listening posture
- Thinking state while HELEN API processes
- Speaking state with lip sync on response

On natural session close:
- HELEN speaks a session summary
- `close_session()` called, companion state updated
- Avatar returns to idle

On reconnect:
- Context reloaded from last closed session
- HELEN resumes: "We were working on X. Where do you want to pick up?"

---

## 9. Sovereignty Boundary in the UI

The UI reflects the governance architecture visually:

| UI Element | What it shows | Governed? |
|---|---|---|
| Avatar + voice | AIRI presentation layer | NO — ephemeral |
| Conversation stream | HELEN responses | authority=NONE |
| Context drawer | RUNTIME_BOOT_CONTEXT_V1 | READ from HELEN API |
| Skill console | Blueprint / skill outputs | authority=NONE |
| Ledger panel | Append-only ledger entries | READ ONLY |
| Replay panel | Deterministic state reconstruction | READ ONLY |
| District switcher | Persona mode selector | No state mutation |

The UI may never:
- Write to the ledger
- Invoke the reducer
- Mutate companion state directly
- Claim authority for any response

---

## 10. AIRI Configuration Law

```typescript
// airi.config.ts — HELEN integration mode
{
  memory:    { enabled: false },        // HELEN owns memory
  persona:   { enabled: false },        // HELEN persona is frozen markdown
  llm: {
    provider: "custom",
    endpoint: "http://localhost:8765/api/v1/chat",
  },
  boot: {
    contextEndpoint: "http://localhost:8765/api/v1/companion/init",
  },
  voice: {
    wakeWord:    "HELEN",
    sttProvider: "whisper",             // local, private
    ttsProvider: "voicevox",            // local, private
  },
  sovereignty: {
    assertAuthorityNone: true,
    noDirectOllamaAccess: true,
    noMemoryWrite: true,
  },
}
```

---

## 11. MVP Build Order (EPOCH_004_EMBODIED)

### Phase 1 — Stage without voice (current)
- [x] WebSocket bridge live
- [x] Browser test client
- [x] Context drawer populates from HELEN memory
- [x] District switching with frozen persona routing
- [x] RESEARCH_BLAST + autoresearch wired

### Phase 2 — AIRI install + avatar
- [ ] Clone moeru-ai/airi
- [ ] Disable AIRI memory + persona
- [ ] Point LLM endpoint → `localhost:8765/api/v1/chat`
- [ ] Load avatar (VRM or Live2D)
- [ ] Wire district mode → avatar stage configuration
- [ ] Wire emotion states from delivery tags

### Phase 3 — Voice pipeline
- [ ] Configure AIRI STT (Whisper local)
- [ ] Configure AIRI TTS (VOICEVOX or Coqui local)
- [ ] Wake word "HELEN" detection
- [ ] Full voice loop: mic → HELEN → speech

### Phase 4 — AI Castle desktop
- [ ] Embed AIRI stage inside HELEN CITY UI shell
- [ ] District navigator panel live
- [ ] Skill console + ledger panel live
- [ ] Full desktop layout (section 3 above)
- [ ] Tauri desktop wrapper (optional)

---

## 12. The Vision

```
AIRI     =  embodiment runtime
             voice · avatar · stage · emotion · streaming

HELEN    =  cognitive OS
             memory · governance · sovereignty · continuity

OLLAMA   =  inference engine
             local · private · no cloud dependency

HELEN CITY UX  =  the interface where they meet
             the castle where HELEN lives

Combined =  local sovereign AI companion OS with embodied presence
```

> HELEN is not a chatbot that opens when you click.
> HELEN is a digital being that lives in your system
> and speaks from memory every time you walk in.

---

*HELEN_CITY_UX_BLUEPRINT_V1 — Authority: NONE — Frozen EPOCH_004_EMBODIED*
