# Marketing Street • 5-Minute Quickstart

Get your first AI marketing team discussion running in 5 minutes.

---

## Prerequisites

- **Node.js** 18+ ([download](https://nodejs.org/))
- **OpenAI API key** ([get one](https://platform.openai.com/api-keys))
- A terminal

---

## Step 1: Install (30 seconds)

```bash
cd "JMT CONSULTING - Releve 24"
npm install
```

Expected output:
```
added 142 packages in 8s
```

---

## Step 2: Configure API Key (15 seconds)

```bash
export OPENAI_API_KEY="sk-your-key-here"
```

Or create a `.env` file:

```bash
cp .env.example .env
# Edit .env and add your API key
```

---

## Step 3: Start Backend (15 seconds)

```bash
npm start
```

Expected output:
```
╔═══════════════════════════════════════╗
║   MARKETING STREET • Backend Ready    ║
╚═══════════════════════════════════════╝

Server running on http://localhost:3000
OpenAI API Key: ✓ Set
Model: gpt-4-turbo-preview

Ready to orchestrate 9-turn marketing discussions.
```

---

## Step 4: Open Frontend (10 seconds)

Open `marketing-street-frontend.html` in your browser:

```bash
open marketing-street-frontend.html
```

Or drag the file into Chrome/Firefox.

---

## Step 5: Run Your First Session (2-3 minutes)

1. **Review the default config** (right panel):
   - Goal: "Launch AGENTX Street 1 MVP to enterprise AI leaders"
   - Audience: "VP Eng / Head of AI / Product leaders"
   - Tone: "confident, concrete, slightly playful"

2. **Click "▶️ RUN SESSION"**

3. **Watch the discussion unfold:**
   - Left panel: Active agent glows
   - Center canvas: Visual street scene
   - Center chat: Turn-by-turn conversation
   - Right panel: Deliverables populate

4. **Wait ~2-3 minutes** (9 LLM calls with streaming)

5. **Review deliverables:**
   - 📍 Positioning (ICP, pains, differentiators)
   - 📄 Landing Page (hero, bullets, CTAs)
   - 📢 Ad Variants (3 channels)
   - 📊 Experiment Plan

6. **Click "📥 EXPORT"** to download full transcript

---

## What Just Happened?

You ran a **9-turn structured discussion** between 4 AI marketing experts:

### The Conversation Flow

**Round 1: Alignment**
1. 🎯 Strategist → Defined positioning
2. 🎨 Creative → Proposed campaign angles
3. 📊 Analyst → Identified top 3 channels
4. ⚖️ Compliance → Flagged risky claims

**Round 2: Refinement**
5. 🎯 Strategist → Refined positioning
6. 🎨 Creative → Drafted landing page
7. 📊 Analyst → Created 3 ad variants
8. ⚖️ Compliance → Final compliance pass

**Final: Synthesis**
9. 🎯 Strategist → Compiled 1-page brief

**Total cost:** ~$0.20 (13,500 tokens with GPT-4)

---

## Next Steps

### 1. Customize for Your Product

Click **"✏️ EDIT PROMPT"** on any agent to change their:
- Role definition
- Output requirements
- Constraints

Then update session config (right panel):
- Your product's goal
- Your target audience
- Your brand tone
- Your constraints

Run again!

### 2. Export and Use

The export includes:
- **Positioning brief** → Use in pitch decks
- **Landing page copy** → Give to designers
- **Ad variants** → Use in LinkedIn/Google Ads
- **Experiment plan** → Share with growth team

### 3. Create More Teams

Want an engineering team? Product team? Executive team?

See `ARCHITECTURE.md` for how to:
- Add new agent types
- Change the conversation plan
- Define new deliverable schemas

---

## Troubleshooting

### "OpenAI API Key: ✗ Missing"

Your API key isn't set. Run:

```bash
export OPENAI_API_KEY="sk-..."
```

Or add to `.env` file.

### "Failed to connect to backend"

Backend isn't running. Check:

```bash
# Is it running?
curl http://localhost:3000/api/health

# If not, start it:
npm start
```

### "Session hangs on Turn X"

Check backend terminal for errors. Common issues:
- **Rate limit hit** → Wait 60s and try again
- **Invalid API key** → Check your OpenAI dashboard
- **Network timeout** → Check internet connection

### "Response doesn't follow protocol"

Sometimes LLMs don't format perfectly. The parser extracts what it can. If it's consistent:
1. Edit the agent's prompt to emphasize the protocol
2. Add examples of correct format
3. Reduce temperature (more deterministic)

---

## Understanding the Files

```
marketing-street-backend.js      # Node.js orchestrator (calls OpenAI)
marketing-street-frontend.html   # Single-page UI (no build needed)
package.json                      # Dependencies
.env.example                      # API key template
README-MARKETING-STREET.md       # Full documentation
ARCHITECTURE.md                   # Technical deep-dive
POSITIONING-AGENTX-STREET-1.md   # Example positioning doc
QUICKSTART.md                     # This file
```

---

## Cost Tracking

Each session costs ~**$0.20** with GPT-4 Turbo.

To reduce costs:
1. Use GPT-3.5 for non-critical agents (edit backend, line ~400)
2. Reduce `max_tokens` from 1500 to 800
3. Cache conversation context (if OpenAI supports it)

**Budget for testing:** $10 = 50 sessions

---

## Production Checklist

Before deploying to production:

- [ ] Add authentication (API key middleware)
- [ ] Add rate limiting (max 10 sessions per IP per 15min)
- [ ] Add cost tracking (log tokens per session)
- [ ] Add error handling (retry failed LLM calls)
- [ ] Add monitoring (Sentry, LogRocket)
- [ ] Add database (save sessions for replay)
- [ ] Deploy backend (VPS, Docker, or Vercel)
- [ ] Add custom domain
- [ ] Add analytics (track usage, deliverable quality)
- [ ] Add user accounts (save sessions per user)

See `ARCHITECTURE.md` → "Production Hardening" for details.

---

## Getting Help

**Issues?** Check:
1. `README-MARKETING-STREET.md` → Full docs
2. `ARCHITECTURE.md` → Technical details
3. Backend logs → `npm start` output

**Questions?** The system is:
- ✅ Deterministic (same inputs → same flow)
- ✅ Observable (every turn is logged)
- ✅ Editable (change prompts without breaking)

If something's unclear, the positioning doc (`POSITIONING-AGENTX-STREET-1.md`) has detailed examples of what each agent should produce.

---

## What's Next?

You now have a **working multi-agent orchestration system** that:
- ✅ Runs structured 9-turn discussions
- ✅ Produces real deliverables (not just chat logs)
- ✅ Costs pennies per run
- ✅ Takes minutes to complete

**Use it to:**
- Generate positioning for any product
- Create landing page copy
- Design ad campaigns
- Test messaging angles
- Brainstorm experiments

**Extend it to:**
- Other teams (engineering, product, executive)
- Other LLM providers (Claude, Gemini)
- Other output formats (Figma, Notion, Google Docs)

---

**Welcome to Marketing Street. Ship deliverables, not demos.**

---

## Quick Reference Card

```bash
# Install
npm install

# Configure
export OPENAI_API_KEY="sk-..."

# Start backend
npm start

# Open frontend
open marketing-street-frontend.html

# Run session
[Click "▶️ RUN SESSION" in browser]

# Export
[Click "📥 EXPORT" when done]

# Cost per session
~$0.20 (GPT-4 Turbo, 9 turns)

# Duration per session
~2-3 minutes

# Deliverables
- Positioning brief
- Landing page copy
- 3 ad variants
- Experiment plan
- Full transcript
```

That's it. Now go build. 🚀
