# Marketing Street • Production MVP

**ChatDev-inspired 4-agent marketing orchestrator with real LLM backend**

A disciplined, minimal architecture for running structured multi-agent marketing discussions that produce actual deliverables.

---

## 🎯 What This Is

A **production-ready system** where 4 specialized marketing agents collaborate to generate:

- **Positioning brief** (ICP, pains, differentiators, pitch)
- **Landing page copy** (hero, bullets, CTAs)
- **3 ad variants** (one per acquisition channel)
- **Experiment plan** (metrics, success criteria)
- **Risk table** (compliance-safe rewrites)
- **1-page launch brief**

### The 4 Agents (Orthogonal Roles)

| Agent | Role | Output | Failure Mode Prevention |
|-------|------|--------|------------------------|
| 🎯 **Positioning Strategist** | Define ICP, value prop, narrative spine | Concrete positioning (no hype) | Avoids "revolutionary/innovative" language |
| 🎨 **Creative Director** | Campaign angles, landing page copy, metaphors | Bold but concrete creative | Every concept has rationale |
| 📊 **Performance Analyst** | Top 3 channels, experiments, metrics | Ruthless prioritization | No vanity metrics |
| ⚖️ **Brand & Compliance** | Rewrite risky claims, ensure tone consistency | Risk table with safer alternatives | Never deletes ideas—only rewrites safely |

---

## 🏗️ Architecture

### Backend (`marketing-street-backend.js`)
- **Node.js + Express** server
- **OpenAI API** integration (GPT-4 Turbo)
- **Server-Sent Events (SSE)** for real-time streaming
- **9-turn conversation protocol** (Round 1 → Round 2 → Final Synthesis)
- **Structured JSON export** (schema-enforced deliverables)

### Frontend (`marketing-street-frontend.html`)
- **Single HTML file** (zero build step)
- **Canvas street visualization** (active speaker glow)
- **Editable prompt cards** per agent
- **Real-time chat feed** with turn-by-turn updates
- **Deliverables panel** (auto-populated from backend)

### Conversation Protocol (Enforced Server-Side)

Each agent **must** respond with:
1. **CONTRIBUTION** — their main analysis/proposal
2. **QUESTION** — exactly one question to another agent
3. **ACTION** — what should happen next

This prevents "4 monologues" and forces real collaboration.

### The 9-Turn Plan

**Round 1: Alignment** (4 turns)
1. Strategist → Define positioning
2. Creative → Propose campaign angles
3. Analyst → Identify top 3 channels
4. Compliance → Flag risks

**Round 2: Refinement** (4 turns)
5. Strategist → Refine positioning
6. Creative → Draft landing page copy
7. Analyst → Create 3 ad variants
8. Compliance → Final compliance pass

**Final: Synthesis** (1 turn)
9. Strategist → Compile 1-page brief + structured JSON

**Total LLM calls: 9** (not 40)

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd "JMT CONSULTING - Releve 24"
npm install
```

### 2. Set OpenAI API Key

```bash
export OPENAI_API_KEY="sk-..."
```

Or create a `.env` file:

```
OPENAI_API_KEY=sk-...
```

### 3. Start Backend

```bash
npm start
```

You should see:

```
╔═══════════════════════════════════════╗
║   MARKETING STREET • Backend Ready    ║
╚═══════════════════════════════════════╝

Server running on http://localhost:3000
OpenAI API Key: ✓ Set
Model: gpt-4-turbo-preview
Ready to orchestrate 9-turn marketing discussions.
```

### 4. Open Frontend

Open `marketing-street-frontend.html` in your browser, or:

```bash
open marketing-street-frontend.html
```

---

## 📋 Default Session Config (Episode 1)

**Goal:** Launch AGENTX Street 1 MVP to enterprise AI leaders

**Audience:** VP Eng / Head of AI / Product leaders

**Tone:** confident, concrete, slightly playful

**Constraints:**
- No security guarantees
- No performance claims without qualifiers
- Avoid "autonomous AGI" language

**Deliverables:**
- Landing page hero/subhead/bullets/CTAs
- 3 ad angles (one per top channel)
- 1-page launch brief

---

## 🎮 How to Use

### Step 1: Customize Agent Prompts (Optional)

Click **"✏️ EDIT PROMPT"** on any agent card to modify their:
- **System prompt** (defines role and output requirements)
- Operating rules are locked server-side to maintain protocol

### Step 2: Configure Session

Modify in the right panel:
- 🎯 **Goal** — what you're launching
- 👥 **Audience** — who you're targeting
- 🎨 **Tone** — brand voice
- 🚫 **Constraints** — what to avoid

### Step 3: Run Session

Click **"▶️ RUN SESSION"**

Watch in real-time:
- **Left panel** — Active speaker glows
- **Center canvas** — Visual "street" shows active agent
- **Center chat** — Turn-by-turn discussion unfolds
- **Right panel** — Deliverables populate automatically

**Duration:** ~2-3 minutes (9 LLM calls with streaming)

### Step 4: Export

Click **"📥 EXPORT"** to download:
- **Markdown file** with full transcript + deliverables
- Structured JSON export (programmatically usable)

---

## 🔧 Technical Details

### Why SSE (Server-Sent Events)?

- **Simpler than WebSockets** for one-way streaming
- **Built into browsers** (no library needed)
- **Auto-reconnect** on connection drop
- **Progressive rendering** (shows turns as they complete)

### Why 9 Turns (Not More)?

- **Cost control** — Each session = 9 API calls (~$0.20 with GPT-4)
- **Time bounded** — Completes in 2-3 minutes
- **Forced prioritization** — Agents can't ramble

### Why Locked Operating Rules?

User-editable prompts allow customization, but **operating rules** are locked server-side to ensure:
- Every response follows **CONTRIBUTION/QUESTION/ACTION** format
- Agents avoid hype language (e.g., "revolutionary")
- Output is structured and parseable

### Structured Export Schema

The final turn produces JSON matching this schema:

```json
{
  "positioning": {
    "icp": "string",
    "primaryPains": ["...", "...", "..."],
    "differentiators": ["...", "...", "..."],
    "oneLiner": "...",
    "thirtyWordPitch": "...",
    "proofPointsNeeded": ["..."]
  },
  "landingPage": {
    "hero": "...",
    "subhead": "...",
    "bullets": ["...", "...", "...", "...", "...", "..."],
    "ctas": ["...", "...", "..."]
  },
  "adVariants": [
    {
      "channel": "...",
      "headline": "...",
      "body": "...",
      "cta": "...",
      "hook": "..."
    }
  ],
  "experimentPlan": [
    {
      "hypothesis": "...",
      "metric": "...",
      "successCriteria": "...",
      "timeline": "..."
    }
  ],
  "riskTable": [
    {
      "originalClaim": "...",
      "riskLevel": "low|medium|high",
      "saferAlternative": "..."
    }
  ],
  "brief": "..."
}
```

---

## 🎯 Production Hardening Checklist

- [x] Backend orchestration (no client-side API keys)
- [x] SSE streaming for real-time updates
- [x] Structured JSON export
- [x] Turn protocol enforcement
- [x] Editable prompts with locked rules
- [ ] **Authentication** (add API key auth for multi-user)
- [ ] **Rate limiting** (prevent abuse)
- [ ] **Replay with seed** (deterministic re-runs)
- [ ] **Conversation state persistence** (save/resume sessions)
- [ ] **Cost tracking** (log token usage per session)

---

## 🔄 Next: Create More "Streets"

The architecture is **team-agnostic**. Create new streets by:

1. Define 4 orthogonal roles
2. Write agent prompts
3. Define conversation plan (9 turns)
4. Define deliverable schema

### Examples:

**Engineering Street**
- 🔧 Backend Engineer
- 🎨 Frontend Engineer
- 🧪 QA Engineer
- 🚀 DevOps Engineer

**Product Street**
- 📊 Product Manager
- 🎨 Product Designer
- 🔬 User Researcher
- 📈 Growth PM

**Executive Street**
- 💼 CEO
- 💰 CFO
- 🔧 CTO
- 📢 CMO

---

## 📊 Cost Estimate

**Per session (9 turns):**
- Model: GPT-4 Turbo
- Average tokens per turn: ~1000 input + 500 output
- Total: ~13,500 tokens
- **Cost: ~$0.20 per session**

**For 100 sessions: ~$20**

---

## 🐛 Troubleshooting

### "OpenAI API Key: ✗ Missing"

Set your API key:

```bash
export OPENAI_API_KEY="sk-..."
```

### "Failed to connect to backend"

Ensure backend is running:

```bash
npm start
```

Check `http://localhost:3000/api/health`

### "Session hangs on Turn X"

Check backend logs for errors. Common issues:
- API rate limit hit
- Network timeout
- Malformed response from LLM

---

## 📚 References

### Conversation Protocol Inspiration
- **ChatDev** paper (multi-agent software dev)
- **Stanford Generative Agents** (believable agent behavior)

### OpenAI API Patterns
- [Conversation state management](https://platform.openai.com/docs/guides/conversation)
- [Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)

---

## 🎯 Why This Works

### 1. Disciplined Architecture
- No feature bloat
- Clear agent contracts
- Deterministic flow

### 2. Real Deliverables
- Not just chat logs
- Structured JSON output
- Immediately usable

### 3. Production-Ready
- Backend orchestration (safe)
- SSE streaming (real-time)
- Editable but bounded (can't break protocol)

### 4. Cost Efficient
- 9 calls (not 40)
- Completes in 2-3 minutes
- ~$0.20 per session

### 5. Extensible
- Add new agent types
- Change LLM providers
- Create new "streets"

---

## 📝 License

MIT

---

## 🚀 Ship It

This is **shippable today**. The system:
- Works offline (after setup)
- Produces real deliverables
- Costs pennies per run
- Takes 5 minutes to set up

**Next step:** Run your first session and iterate on the agent prompts until the output matches your brand voice.

---

**Built with the philosophy:** *"Do not just chat. Ship deliverables."*
