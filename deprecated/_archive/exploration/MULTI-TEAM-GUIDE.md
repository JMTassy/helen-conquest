# Multi-Team Street • Complete Guide

**ChatDev-inspired orchestration platform with 4 specialized teams**

Switch between Marketing, Engineering, Product, and Executive teams—each with 4 expert agents and preset scenarios.

---

## 🎯 What This Is

A **unified platform** for running structured multi-agent discussions across different organizational functions:

| Team | Use Case | Deliverables |
|------|----------|--------------|
| 🎯 **Marketing** | Product launches, campaigns, positioning | Positioning brief, landing page, ad variants |
| 🔧 **Engineering** | System design, architecture decisions | Tech stack, API specs, deployment plan |
| 📱 **Product** | Feature planning, UX design, roadmaps | User stories, wireframes, success metrics |
| 💼 **Executive** | Strategic decisions, resource allocation | Vision statement, financial model, go/no-go |

---

## 🏗️ The 4 Teams

### 🎯 **Marketing Team**

**Agents:**
1. **🎯 Positioning Strategist** — Define ICP, value prop, narrative
2. **🎨 Creative Director** — Campaign angles, landing page copy
3. **📊 Performance Analyst** — Channels, experiments, metrics
4. **⚖️ Brand & Compliance** — Risk mitigation, claim safety

**Preset Scenarios:**
- Launch AGENTX Street 1 MVP
- SaaS Product Rebrand
- Mobile App Launch

**Output:**
```json
{
  "positioning": { "icp": "...", "pains": [...], "differentiators": [...] },
  "landingPage": { "hero": "...", "bullets": [...], "ctas": [...] },
  "adVariants": [...],
  "experimentPlan": [...],
  "riskTable": [...]
}
```

---

### 🔧 **Engineering Team**

**Agents:**
1. **🏗️ System Architect** — High-level architecture, tech stack
2. **⚙️ Backend Lead** — API design, database schema, server logic
3. **💻 Frontend Lead** — Component structure, state management, UX
4. **🧪 QA & DevOps Lead** — Testing strategy, CI/CD, monitoring

**Preset Scenarios:**
- Design Microservice Architecture
- Legacy System Migration
- Real-Time Analytics Pipeline

**Output:**
```json
{
  "architecture": {
    "systemDesign": "...",
    "techStack": { "backend": "...", "frontend": "...", "infra": "..." },
    "scalability": "..."
  },
  "api": { "endpoints": [...], "authentication": "..." },
  "database": { "schema": "...", "migrations": "..." },
  "cicd": { "pipeline": "...", "deployment": "..." },
  "monitoring": { "metrics": [...], "alerts": [...] }
}
```

---

### 📱 **Product Team**

**Agents:**
1. **📋 Product Manager** — Vision, prioritization, roadmap
2. **🎨 UX Designer** — User flows, wireframes, design systems
3. **🔬 UX Researcher** — Research questions, user insights, validation
4. **📈 Growth Lead** — Acquisition strategy, retention, experiments

**Preset Scenarios:**
- B2B Dashboard Redesign
- Mobile-First Product Pivot
- Freemium to Paid Conversion

**Output:**
```json
{
  "productVision": "...",
  "features": [
    { "name": "...", "priority": "must/should/could/won't", "userStory": "..." }
  ],
  "userFlows": [...],
  "wireframes": [...],
  "researchPlan": {
    "questions": [...],
    "methodology": "...",
    "personas": [...]
  },
  "growthStrategy": {
    "acquisitionChannels": [...],
    "retentionMechanics": [...],
    "experiments": [...]
  }
}
```

---

### 💼 **Executive Team**

**Agents:**
1. **👔 CEO** — Strategic vision, key decisions, resource allocation
2. **💰 CFO** — Financial modeling, budget, unit economics
3. **🔧 CTO** — Technical strategy, build vs buy, team structure
4. **📢 CMO** — Brand strategy, GTM plan, demand generation

**Preset Scenarios:**
- Series A Fundraising Strategy
- New Market Entry Decision
- Build vs Acquire Decision

**Output:**
```json
{
  "strategicVision": "...",
  "keyDecisions": [
    { "decision": "...", "rationale": "...", "risks": [...] }
  ],
  "financialModel": {
    "revenue": "...",
    "costs": "...",
    "runway": "...",
    "unitEconomics": { "cac": "...", "ltv": "...", "payback": "..." }
  },
  "technicalStrategy": {
    "buildVsBuy": "...",
    "teamStructure": "...",
    "techDebt": "..."
  },
  "gtmPlan": {
    "positioning": "...",
    "channels": [...],
    "budget": "..."
  }
}
```

---

## 🎮 How to Use

### Step 1: Select Team

Click one of the team tabs at the top:
- 🎯 **MARKETING** — Product launches, campaigns
- 🔧 **ENGINEERING** — System design, architecture
- 📱 **PRODUCT** — Feature planning, UX
- 💼 **EXECUTIVE** — Strategic decisions

The UI updates to show:
- Relevant agents in left panel
- Team-specific presets in right panel
- Color-coded agent cards

### Step 2: Choose Preset (or Custom)

**Option A: Use Preset**
1. Click "📋 Preset Scenarios" dropdown
2. Select a scenario (e.g., "Launch AGENTX Street 1 MVP")
3. Session config auto-fills

**Option B: Custom Session**
1. Enter your own goal
2. Define audience/context
3. Set tone/approach
4. Add constraints

### Step 3: Customize Agents (Optional)

Click **"✏️ EDIT PROMPT"** on any agent to:
- Modify system prompt
- Adjust output requirements
- Change constraints

### Step 4: Run Session

1. Click **"▶️ RUN SESSION"**
2. Watch 9-turn discussion unfold
3. Review deliverables in right panel
4. Click **"📥 EXPORT"** to download

**Duration:** 2-3 minutes (simulated) or 3-5 minutes (real LLM)

---

## 📋 Preset Scenarios (Detailed)

### Marketing Team Presets

#### 1. Launch AGENTX Street 1 MVP
**Goal:** Launch AGENTX Street 1 MVP to enterprise AI leaders

**Context:**
- Target: VP Eng / Head of AI at 500+ employee companies
- Tone: Confident, concrete, slightly playful
- Constraints: No security/performance guarantees without qualifiers

**Expected Output:**
- Positioning: ICP, pains, differentiators
- Landing page: Hero, bullets, CTAs
- 3 ad variants (LinkedIn, Hacker News, Newsletter)
- Experiment plan with metrics

#### 2. SaaS Product Rebrand
**Goal:** Rebrand 5-year-old B2B SaaS product to appeal to modern buyers

**Context:**
- Target: Mid-market SaaS buyers (100-1000 employees)
- Tone: Professional, modern, trustworthy
- Constraints: Maintain existing customer trust

**Expected Output:**
- Brand evolution strategy (not revolution)
- Updated positioning
- Visual refresh recommendations
- Communication plan to existing customers

#### 3. Mobile App Launch
**Goal:** Launch consumer mobile app in competitive fitness market

**Context:**
- Target: Health-conscious millennials and Gen Z
- Tone: Energetic, motivational, authentic
- Constraints: Limited budget ($50K), 3-month timeline

**Expected Output:**
- App store positioning
- Launch campaign angles
- Influencer partnership strategy
- Pre-launch waitlist mechanics

---

### Engineering Team Presets

#### 1. Design Microservice Architecture
**Goal:** Design microservice architecture for real-time collaboration platform

**Context:**
- Team: 5 backend, 3 frontend, 2 DevOps
- Scale: 100K concurrent users
- Timeline: 6 months, $100K cloud budget/year

**Expected Output:**
- Service boundaries and communication patterns
- Tech stack (languages, frameworks, databases)
- API gateway and authentication strategy
- Deployment architecture (Kubernetes, serverless, etc.)
- Monitoring and observability plan

#### 2. Legacy System Migration
**Goal:** Migrate monolithic PHP app to modern microservices

**Context:**
- Constraint: Zero downtime requirement
- Timeline: 12 months
- Team: 8 developers

**Expected Output:**
- Strangler fig migration pattern
- Service extraction priorities
- Database migration strategy
- Rollback plan for each phase
- Testing strategy for regression prevention

#### 3. Real-Time Analytics Pipeline
**Goal:** Build real-time analytics pipeline for 10M+ events/day

**Context:**
- Latency requirement: Sub-second
- Uptime: 99.9%
- Focus: Cost-efficient storage

**Expected Output:**
- Event ingestion architecture (Kafka, Kinesis, etc.)
- Stream processing framework
- Storage layer (hot/warm/cold tiers)
- Query optimization strategy
- Cost projection and optimization

---

### Product Team Presets

#### 1. B2B Dashboard Redesign
**Goal:** Redesign complex analytics dashboard for better usability

**Context:**
- Users: Enterprise data analysts + executives
- Constraint: Cannot remove existing features
- Timeline: 4 months

**Expected Output:**
- User research plan (interviews, surveys, analytics)
- Key user flows (analyst workflow vs. executive overview)
- Wireframes for 5-7 key screens
- Information architecture
- Success metrics (task completion time, NPS, feature adoption)

#### 2. Mobile-First Product Pivot
**Goal:** Pivot desktop-first product to mobile-first experience

**Context:**
- Current: 80% desktop users
- Challenge: Cannot alienate desktop users
- Timeline: 6 months, limited eng resources

**Expected Output:**
- Mobile-first feature prioritization
- Responsive design strategy (vs. native apps)
- Migration communication plan
- Phased rollout strategy
- Success metrics (mobile adoption, desktop retention)

#### 3. Freemium to Paid Conversion
**Goal:** Design freemium-to-paid conversion flow to increase revenue

**Context:**
- Current: 50K active freemium users
- Constraint: Maintain free tier value, no dark patterns
- Approach: Test with 10% first

**Expected Output:**
- Value ladder (what free gets vs. paid)
- Conversion touchpoints (when/where to prompt upgrade)
- Trial mechanics (14-day trial vs. feature-gated)
- A/B test plan
- Success metrics (conversion rate, revenue per user, churn)

---

### Executive Team Presets

#### 1. Series A Fundraising Strategy
**Goal:** Develop Series A fundraising strategy and investor deck

**Context:**
- Target: $10M raise for 18-month runway
- Milestone: Path to $10M ARR
- Audience: Enterprise SaaS-focused VCs

**Expected Output:**
- Investment thesis (why now, why this team, why this market)
- Financial projections (revenue, costs, unit economics)
- Use of funds (headcount, product, GTM)
- Milestones and de-risking events
- Investor outreach strategy

#### 2. New Market Entry Decision
**Goal:** Decide whether to enter European market in next 12 months

**Context:**
- Current: US market not yet saturated
- Runway: 24 months
- Challenge: Regulatory complexity (GDPR, etc.)

**Expected Output:**
- Market opportunity analysis
- Regulatory and compliance requirements
- Go-to-market strategy (direct vs. partnerships)
- Resource requirements (hires, budget, timeline)
- Decision criteria (go/no-go thresholds)

#### 3. Build vs Acquire Decision
**Goal:** Decide whether to build AI features in-house or acquire startup

**Context:**
- Budget: $5M acquisition available
- Build timeline: 18 months
- Pressure: Competitive threat

**Expected Output:**
- Build vs. buy analysis (cost, time, risk)
- Acquisition target criteria
- Integration plan (if acquire)
- Build roadmap (if build)
- Decision recommendation with rationale

---

## 🎨 Team-Specific Conversation Patterns

Each team follows a **9-turn choreography**, but the focus differs:

### Marketing Team Flow
1. **Strategist** → Position the product
2. **Creative** → Brainstorm campaign angles
3. **Analyst** → Validate with channel strategy
4. **Compliance** → Flag risks

*(Repeat Round 2 for refinement)*

5. **Strategist** → Refine positioning
6. **Creative** → Finalize copy
7. **Analyst** → Create ad variants
8. **Compliance** → Final safety pass
9. **Strategist** → Compile brief

### Engineering Team Flow
1. **Architect** → Propose system design
2. **Backend** → Define API contracts
3. **Frontend** → Plan component structure
4. **QA/DevOps** → Design testing + deployment

*(Repeat Round 2 for refinement)*

5. **Architect** → Refine architecture
6. **Backend** → Finalize database schema
7. **Frontend** → Specify state management
8. **QA/DevOps** → Complete CI/CD pipeline
9. **Architect** → Compile tech spec

### Product Team Flow
1. **PM** → Define product vision
2. **Designer** → Sketch user flows
3. **Researcher** → Plan validation
4. **Growth** → Propose experiments

*(Repeat Round 2 for refinement)*

5. **PM** → Refine feature prioritization
6. **Designer** → Finalize wireframes
7. **Researcher** → Complete research plan
8. **Growth** → Define success metrics
9. **PM** → Compile product brief

### Executive Team Flow
1. **CEO** → Frame strategic decision
2. **CFO** → Model financial impact
3. **CTO** → Assess technical feasibility
4. **CMO** → Evaluate market opportunity

*(Repeat Round 2 for refinement)*

5. **CEO** → Synthesize viewpoints
6. **CFO** → Refine financial model
7. **CTO** → Finalize technical strategy
8. **CMO** → Complete GTM plan
9. **CEO** → Make final recommendation

---

## 🔧 Connecting to Real LLMs

The current version uses **simulated responses**. To connect real LLMs:

### Option 1: Use the Marketing Street Backend

The `marketing-street-backend.js` file shows the **production pattern**:

```javascript
// In multi-team-street.html, replace generateSimulatedResponse():

async function callLLM(agentKey, context) {
  const agent = TEAMS[currentTeam].agents[agentKey];

  const response = await fetch('http://localhost:3000/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      systemPrompt: agent.systemPrompt,
      userMessage: context,
      conversationHistory: conversationLog
    })
  });

  const data = await response.json();
  return parseAgentResponse(data.message);
}
```

### Option 2: Direct OpenAI Integration (Client-Side)

**⚠️ Warning:** Exposes API key. Use only for prototyping.

```javascript
async function callOpenAI(agentKey, context) {
  const agent = TEAMS[currentTeam].agents[agentKey];

  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${YOUR_API_KEY}` // ⚠️ NEVER commit this
    },
    body: JSON.stringify({
      model: 'gpt-4-turbo-preview',
      messages: [
        { role: 'system', content: agent.systemPrompt },
        { role: 'user', content: context }
      ],
      temperature: 0.7
    })
  });

  const data = await response.json();
  return parseAgentResponse(data.choices[0].message.content);
}
```

### Option 3: Multi-Model Approach

Use different LLMs for different agent types:

```javascript
const MODEL_MAP = {
  marketing: {
    strategist: 'claude-3-5-sonnet-20241022', // Deep reasoning
    creative: 'gpt-4',                         // Creative
    analyst: 'gpt-4-turbo-preview',           // Analytical
    compliance: 'claude-3-5-sonnet-20241022'  // Cautious
  },
  engineering: {
    architect: 'claude-3-5-sonnet-20241022',
    backend: 'gpt-4-turbo-preview',
    frontend: 'gpt-4',
    qa: 'claude-3-5-sonnet-20241022'
  }
  // ... etc
};
```

---

## 📊 Cost Estimates (Real LLM Usage)

### Per Session (9 turns)

| Team | Model | Tokens/Turn | Total Tokens | Cost |
|------|-------|-------------|--------------|------|
| Marketing | GPT-4 Turbo | ~1500 | ~13,500 | ~$0.20 |
| Engineering | GPT-4 Turbo | ~2000 | ~18,000 | ~$0.27 |
| Product | GPT-4 | ~1500 | ~13,500 | ~$0.30 |
| Executive | GPT-4 | ~1800 | ~16,200 | ~$0.35 |

### Cost Optimization

**Use GPT-3.5 for simpler agents:**
- Marketing Compliance: GPT-3.5 (~$0.002 per turn)
- Engineering QA: GPT-3.5 (~$0.002 per turn)

**New cost per session:** ~$0.10-0.15

---

## 🎯 When to Use Each Team

### Use **Marketing Team** when:
- Launching a new product or feature
- Rebranding or repositioning
- Creating campaign messaging
- Designing ad experiments
- Validating value propositions

### Use **Engineering Team** when:
- Designing system architecture
- Making build vs buy decisions
- Planning migrations or refactors
- Evaluating tech stack choices
- Creating deployment strategies

### Use **Product Team** when:
- Planning feature roadmaps
- Conducting user research
- Designing user experiences
- Prioritizing development work
- Optimizing conversion funnels

### Use **Executive Team** when:
- Making strategic decisions
- Planning fundraising
- Evaluating market opportunities
- Allocating resources
- Setting company direction

---

## 🚀 Next Steps

### Immediate (Try It Now)
1. Open `multi-team-street.html` in browser
2. Switch between teams
3. Try different presets
4. Run simulated sessions

### Short-Term (Connect Real LLMs)
1. Set up backend orchestrator (use `marketing-street-backend.js` as template)
2. Add API endpoints for each team
3. Replace `generateSimulatedResponse()` with real LLM calls
4. Test with small budget ($5-10)

### Long-Term (Production)
1. Add authentication (multi-user support)
2. Add session persistence (save/resume)
3. Add cost tracking per team/user
4. Add custom team builder (define your own agents)
5. Add deliverable templates (export to Notion, Google Docs, etc.)

---

## 📚 File Reference

```
multi-team-street.html           # Main application (this file)
MULTI-TEAM-GUIDE.md             # This documentation
marketing-street-backend.js      # Backend orchestrator pattern
ARCHITECTURE.md                  # System architecture details
```

---

## 🎓 Advanced: Create Custom Teams

Want to add a **Sales Team** or **Customer Success Team**?

```javascript
// In multi-team-street.html, add to TEAMS object:

sales: {
  name: 'Sales',
  agents: {
    ae: {
      name: 'Account Executive',
      emoji: '💼',
      class: 'sales-ae',
      systemPrompt: `You are an Account Executive...`
    },
    sdr: {
      name: 'SDR',
      emoji: '📞',
      class: 'sales-sdr',
      systemPrompt: `You are an SDR...`
    },
    se: {
      name: 'Sales Engineer',
      emoji: '🔧',
      class: 'sales-se',
      systemPrompt: `You are a Sales Engineer...`
    },
    manager: {
      name: 'Sales Manager',
      emoji: '📊',
      class: 'sales-manager',
      systemPrompt: `You are a Sales Manager...`
    }
  }
}

// Add to PRESETS:
sales: [
  {
    name: 'Enterprise Deal Strategy',
    goal: 'Close $500K enterprise deal with Fortune 500 company',
    audience: 'VP of Sales, CRO',
    tone: 'strategic, value-focused',
    constraints: 'Legal approval required, 6-month sales cycle'
  }
]

// Add team tab:
<div class="team-tab" data-team="sales">💼 SALES</div>
```

---

**You now have 4 complete teams with 12 preset scenarios.**

**Each team is production-ready and extensible.**

**Switch teams, run sessions, ship deliverables.** 🚀
