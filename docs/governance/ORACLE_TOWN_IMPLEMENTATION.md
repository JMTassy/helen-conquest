# ORACLE TOWN — Complete Implementation Specification

**Version:** 2.0.0
**Status:** ✅ IMPLEMENTATION READY
**Date:** January 21, 2026

---

## Vision Statement

**ORACLE TOWN** is a scalable, hierarchical multi-agent governance system that transforms natural language inputs into verified, shippable claims through a civic simulation structure:

```
INPUT → CLAIM → STREETS (agents) → BUILDINGS (teams) → DISTRICTS (expert domains) → TOWN (integration) → MAYOR (final verdict) → SHIP/NO_SHIP + RECOMMENDATIONS
```

Combines:
- **ChatDev**: Structured turn protocol, orthogonal roles, deliverables-focused
- **AI Town (Stanford)**: Spatial simulation, emergent behaviors, memory/reflection
- **ORACLE SUPERTEAM**: Constitutional governance, binary verdicts, obligation tracking
- **Marketing Street**: Multi-team orchestration, SSE streaming, real LLM integration

---

## 1. SYSTEM ARCHITECTURE

### 1.1 Hierarchical Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    🏛️ MAYOR (Verdict Engine)                    │
│              Binary Decision: SHIP / NO_SHIP                    │
│           + Remediation Roadmap for NO_SHIP cases               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │    🏙️ TOWN HALL         │
                │  (Integration Layer)    │
                │  Aggregates all signals │
                └────────────┬────────────┘
                             │
        ┏━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━┓
        ┃                                          ┃
┌───────▼──────┐  ┌───────────┐  ┌───────────┐  ┌▼──────────┐
│ 🏘️ DISTRICT 1 │  │ DISTRICT 2│  │ DISTRICT 3│  │ DISTRICT 4│
│   LEGAL      │  │  TECHNICAL│  │  BUSINESS │  │   SOCIAL  │
└───────┬──────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
        │                │                │              │
   ┌────┴────┐      ┌───┴────┐      ┌───┴────┐     ┌──┴─────┐
   │🏢BUILDING│      │BUILDING│      │BUILDING│     │BUILDING│
   │ Legal   │      │  Eng   │      │Marketing│     │  UX    │
   │ Office  │      │  Wing  │      │  Dept   │     │  Team  │
   └────┬────┘      └───┬────┘      └───┬────┘     └───┬────┘
        │               │                │              │
   ┌────┴────┐     ┌───┴────┐      ┌───┴────┐     ┌───┴────┐
   │🛣️ STREET │     │ STREET │      │ STREET │     │ STREET │
   │ 4 agents│     │4 agents│      │4 agents│     │4 agents│
   └─────────┘     └────────┘      └────────┘     └────────┘
```

### 1.2 Entity Definitions

#### STREET (Smallest Unit)
- **4 specialized agents** working on a specific sub-problem
- Follows **ChatDev turn protocol**: structured rounds with CONTRIBUTION → QUESTION → ACTION
- Produces: **Street Report** (preliminary findings + obligations)
- Duration: 3-5 turns (~30-60 seconds with real LLMs)

#### BUILDING (Team Level)
- **Collection of 2-4 streets** covering one domain
- Aggregates street reports
- Produces: **Building Brief** (consolidated findings + evidence + obligations)
- Examples:
  - Legal Building: Compliance Street + Contract Street + Risk Street
  - Engineering Building: Architecture Street + Security Street + Performance Street

#### DISTRICT (Expert Domain)
- **2-3 buildings** forming an expert area
- Has **District Supervisor** (meta-agent) that reviews building briefs
- Produces: **District Verdict** (APPROVE / CONDITIONAL / OBJECT / QUARANTINE)
- 4 Districts:
  1. **Legal & Compliance** (contracts, GDPR, risk)
  2. **Technical & Security** (architecture, infra, security)
  3. **Business & Operations** (ROI, budget, marketing)
  4. **Social & Impact** (UX, community, fairness)

#### TOWN HALL (Integration)
- Receives all 4 district verdicts
- Applies **QI-INT v2 scoring** (quantum interference integration)
- Checks **invariants** (transparency, fairness, budget, ROI, quality)
- Produces: **Town Recommendation** (GO / NO_GO + score)

#### MAYOR (Final Authority)
- Receives Town Recommendation + all evidence
- Applies **constitutional rules**:
  - Kill-switch check (Legal/Security can instant-reject)
  - Blocking obligations check
  - Contradiction detection
  - Score threshold (τ_accept = 0.75)
- Produces: **Final Verdict** (SHIP / NO_SHIP)
- If NO_SHIP: Generates **Remediation Roadmap** (monotonic weakening)

---

## 2. DATA FLOW

### 2.1 Input → Claim Compilation

```typescript
interface TownInput {
  raw_text: string;              // Natural language description
  domain: string;                // "marketing" | "product" | "policy" | "event"
  urgency: "low" | "medium" | "high";
  constraints?: string[];        // Optional explicit constraints
}

interface CompiledClaim {
  claim_id: string;              // UUID
  claim_text: string;            // Formalized statement
  claim_type: "FEATURE" | "CAMPAIGN" | "POLICY" | "PARTNERSHIP";
  success_criteria: string[];    // What defines "success"
  requires_receipts: boolean;    // Whether attestable evidence needed
  initial_obligations: Obligation[];
  metadata: {
    timestamp: string;
    compiled_by: "claim_compiler_agent";
    source_hash: string;
  };
}
```

**Claim Compiler Agent:**
- Takes raw input
- Extracts: goal, audience, constraints, success criteria
- Generates structured claim
- Routes to appropriate districts

### 2.2 Streets → Buildings → Districts

```typescript
interface StreetReport {
  street_id: string;
  agent_contributions: {
    agent_id: string;
    role: string;
    contribution: string;
    questions_raised: string[];
  }[];
  preliminary_findings: string;
  identified_obligations: Obligation[];
  confidence: number;              // 0.0-1.0
  next_street_recommendations?: string[];
}

interface BuildingBrief {
  building_id: string;
  district: string;
  street_reports: StreetReport[];
  consolidated_findings: string;
  evidence_artifacts: string[];   // Links to receipts
  obligations: Obligation[];
  building_verdict: "APPROVE" | "CONDITIONAL" | "OBJECT";
  supervisor_notes: string;
}

interface DistrictVerdict {
  district_id: string;
  district_name: string;
  building_briefs: BuildingBrief[];
  overall_verdict: "APPROVE" | "CONDITIONAL" | "OBJECT" | "QUARANTINE" | "KILL";
  blocking_obligations: Obligation[];
  vote_weight: number;             // 0.65-1.00 based on district authority
  phase: number;                   // 0 (constructive) to π (destructive)
}
```

### 2.3 Town Hall → Mayor

```typescript
interface TownRecommendation {
  district_verdicts: DistrictVerdict[];
  qi_int_score: number;            // Complex amplitude sum → |A_c|²
  invariants_check: {
    transparency: boolean;
    fairness: boolean;
    budget_integrity: boolean;
    roi_realism: boolean;
    service_quality: boolean;
  };
  blocking_obligations: Obligation[];
  kill_switch_triggered: boolean;
  recommendation: "GO" | "NO_GO";
  confidence: number;
}

interface MayorVerdict {
  claim_id: string;
  decision: "SHIP" | "NO_SHIP";
  rationale: string;
  evidence_bundle: string[];
  blocking_reasons?: string[];
  remediation_roadmap?: RemediationStep[];
  timestamp: string;
  code_version: string;            // Git hash for replay
}
```

### 2.4 Remediation Loop (if NO_SHIP)

```typescript
interface RemediationStep {
  step_id: string;
  obligation_id: string;
  description: string;
  required_evidence: string[];
  estimated_effort: "low" | "medium" | "high";
  tier_downgrade?: "A→B" | "A→C" | "B→C";  // Monotonic weakening
  success_criteria: string;
}

interface RemediationProposal {
  original_claim_id: string;
  modified_claim: CompiledClaim;
  changes_made: {
    removed_features?: string[];
    tier_downgraded?: string;
    evidence_added?: string[];
    scope_reduced?: string;
  };
  expected_outcome: "likely_ship" | "needs_iteration";
}
```

---

## 3. AGENT ROLES & PROMPTS

### 3.1 Street-Level Agents (16 per district × 4 districts = 64 total)

#### Example: Legal District → Compliance Building → GDPR Street

**Agent 1: Privacy Analyst**
```
Role: Analyze data processing claims for GDPR compliance
Input: Claim text + data flow description
Output:
- CONTRIBUTION: List of personal data types processed
- QUESTION: "Does this require DPA notification?" (to Legal Counsel)
- ACTION: Flag PII sensitivity level

Operating Rules:
- MUST identify all PII/biometric data
- MUST check for explicit consent mechanisms
- MUST verify data retention policies
```

**Agent 2: Legal Counsel**
```
Role: Assess legal risk and contractual obligations
Input: Privacy Analyst findings + claim
Output:
- CONTRIBUTION: Legal risk assessment (low/medium/high)
- QUESTION: "Are third-party processors GDPR-compliant?" (to Vendor Auditor)
- ACTION: Draft necessary legal disclaimers
```

**Agent 3: Vendor Auditor**
```
Role: Verify third-party compliance
Input: List of vendors/services mentioned in claim
Output:
- CONTRIBUTION: Vendor compliance status
- QUESTION: "Is data transfer mechanism compliant?" (to Privacy Analyst)
- ACTION: List required Standard Contractual Clauses (SCCs)
```

**Agent 4: Compliance Integrator**
```
Role: Synthesize findings into Street Report
Input: All 3 agent contributions
Output:
- Street Report with consolidated GDPR obligations
- Confidence score
- Recommendation: APPROVE / CONDITIONAL / OBJECT
```

### 3.2 Building Supervisor (Meta-Agent)

```
Role: Review all street reports in building, synthesize into Building Brief
Input: 2-4 Street Reports
Output:
- Consolidated findings
- Evidence artifacts (links to receipts)
- Blocking obligations
- Building verdict: APPROVE / CONDITIONAL / OBJECT

Operating Rules:
- MUST ensure all streets agree on critical facts
- MUST identify conflicting findings
- MUST verify evidence sufficiency
- CAN request additional street investigation
```

### 3.3 District Supervisor (Meta-Meta-Agent)

```
Role: Final district-level judgment
Input: 2-3 Building Briefs
Output:
- District Verdict (APPROVE / CONDITIONAL / OBJECT / QUARANTINE / KILL)
- Vote weight and phase (for QI-INT calculation)
- Blocking obligations (if any)

Authority:
- Legal & Security districts can trigger KILL switch
- All districts can QUARANTINE for further review
- Vote weights: Legal=1.0, Security=1.0, Technical=0.85, Business=0.75
```

### 3.4 Town Hall Agent

```
Role: Apply QI-INT v2 scoring, check invariants
Input: 4 District Verdicts + invariants config
Output:
- Town Recommendation (GO / NO_GO)
- QI-INT score
- Invariants status
- Aggregated blocking obligations

Algorithm:
1. Calculate complex amplitude for each district:
   a_{district} = vote_weight × e^(i × phase)
2. Sum: A_c = Σ a_{district}
3. Score: S_c = |A_c|²
4. Check: S_c ≥ 0.75 AND no kill switches AND invariants OK
```

### 3.5 Mayor Agent

```
Role: Final binary verdict + remediation generation
Input: Town Recommendation + full evidence bundle
Output:
- SHIP or NO_SHIP
- Rationale
- If NO_SHIP: Remediation Roadmap

Constitutional Rules (immutable):
1. IF kill_switch → NO_SHIP (immediate)
2. ELSE IF blocking_obligations > 0 → NO_SHIP
3. ELSE IF contradictions detected → NO_SHIP
4. ELSE IF S_c < 0.75 → NO_SHIP
5. ELSE → SHIP

Remediation Logic:
- Identify weakest obligations (lowest confidence)
- Propose monotonic weakening (never strengthen, only reduce scope)
- Generate V2 Proposal with tier downgrades
```

---

## 4. CONVERSATION PROTOCOL

### 4.1 Street-Level Turn Structure (ChatDev-inspired)

**Turn Format (enforced by parser):**
```
## CONTRIBUTION
[Agent's primary work product]

## QUESTION
[Directed to specific other agent or next phase]

## ACTION
[What happens next / what this enables]
```

**Example 3-Turn Street Conversation:**

**Turn 1: Privacy Analyst**
```
## CONTRIBUTION
Identified PII: email, name, location data (GPS coordinates).
GDPR Article 6(1)(a) applies: requires explicit consent.

## QUESTION
@Legal_Counsel: Does consent mechanism need to be double opt-in for location data?

## ACTION
Flagging location data as HIGH sensitivity. Requires consent banner review.
```

**Turn 2: Legal Counsel**
```
## CONTRIBUTION
Yes, location data requires double opt-in per Article 9 (special categories).
Risk: MEDIUM if consent flow unclear, HIGH if no opt-out mechanism.

## QUESTION
@Vendor_Auditor: Which third-party services process location data?

## ACTION
Drafting consent banner requirements + opt-out mechanism specification.
```

**Turn 3: Vendor Auditor**
```
## CONTRIBUTION
Google Maps API + internal analytics. Google has SCCs in place.
Analytics vendor: awaiting DPA confirmation.

## QUESTION
@Compliance_Integrator: Can we ship with pending DPA confirmation?

## ACTION
Recommending CONDITIONAL approval with obligation: "Obtain DPA confirmation within 30 days".
```

**Turn 4: Compliance Integrator (Synthesis)**
```
## CONTRIBUTION
GDPR Street Report:
- PII identified: email, name, GPS
- Consent: Double opt-in required
- Vendor: Google OK, Analytics pending
- Obligation: DPA confirmation required

## QUESTION
None (street complete)

## ACTION
Submitting Street Report to Building Supervisor with CONDITIONAL verdict.
Confidence: 0.85
```

### 4.2 Building-Level Aggregation

**Building Supervisor receives 3 street reports:**
1. GDPR Street → CONDITIONAL (missing DPA)
2. Contract Street → APPROVE (terms reviewed)
3. Risk Street → OBJECT (insurance gap identified)

**Supervisor synthesizes:**
```typescript
BuildingBrief {
  building_id: "legal_building_001",
  district: "Legal & Compliance",
  street_reports: [gdpr_report, contract_report, risk_report],
  consolidated_findings: "Legal review complete. Two blocking issues:
    1. Analytics vendor DPA pending (30-day window)
    2. Insurance coverage gap for GPS liability",
  obligations: [
    {type: "LEGAL_COMPLIANCE", name: "Obtain DPA", severity: "HARD"},
    {type: "LEGAL_COMPLIANCE", name: "Purchase GPS liability insurance", severity: "HARD"}
  ],
  building_verdict: "CONDITIONAL",
  supervisor_notes: "Can proceed to pilot with obligations tracked."
}
```

### 4.3 District-Level Verdict

**District Supervisor (Legal) receives 2 building briefs:**
1. Legal Building → CONDITIONAL (2 obligations)
2. Audit Building → APPROVE

**District Supervisor applies:**
```typescript
DistrictVerdict {
  district_id: "legal_001",
  district_name: "Legal & Compliance",
  overall_verdict: "CONDITIONAL",
  blocking_obligations: [
    {id: "OBL_DPA_001", ...},
    {id: "OBL_INS_002", ...}
  ],
  vote_weight: 1.0,  // Legal has full weight
  phase: π/4,        // Slight destructive component due to obligations
}
```

---

## 5. IMPLEMENTATION STACK

### 5.1 Technology Choices

**Backend:**
- **Python 3.10+** (core orchestration, ORACLE engine)
- **FastAPI** (REST API + WebSocket for streaming)
- **PostgreSQL** (session persistence, audit trail)
- **Redis** (real-time state, agent coordination)

**Frontend:**
- **Single HTML file** (vanilla JS, no build step) OR
- **React** (if need complex visualization)
- **Canvas API** (spatial town visualization like AI Town)
- **SSE or WebSocket** (real-time updates)

**LLM Integration:**
- **OpenAI GPT-4** (strategic agents: Mayor, District Supervisors)
- **Claude 3.5 Sonnet** (analytical agents: street-level)
- **GPT-3.5 Turbo** (administrative agents: compilers, integrators)
- **Mixtable**: District → LLM model mapping

### 5.2 Directory Structure

```
oracle-town/
├── core/
│   ├── claim_compiler.py       # Input → CompiledClaim
│   ├── orchestrator.py         # Main execution loop
│   ├── verdict_engine.py       # Mayor logic (from ORACLE)
│   └── remediation_builder.py  # NO_SHIP → Roadmap
├── agents/
│   ├── street_agent.py         # Base class for street agents
│   ├── building_supervisor.py  # Building aggregation
│   ├── district_supervisor.py  # District verdict
│   └── town_hall.py            # QI-INT integration
├── districts/
│   ├── legal/
│   │   ├── compliance_street.py
│   │   ├── contract_street.py
│   │   └── risk_street.py
│   ├── technical/
│   │   ├── architecture_street.py
│   │   ├── security_street.py
│   │   └── performance_street.py
│   ├── business/
│   │   ├── marketing_street.py  # Reuse from Marketing Street!
│   │   ├── finance_street.py
│   │   └── operations_street.py
│   └── social/
│       ├── ux_street.py
│       ├── community_street.py
│       └── impact_street.py
├── schemas/
│   ├── claim.py                # CompiledClaim, Obligation
│   ├── reports.py              # StreetReport, BuildingBrief
│   └── verdict.py              # DistrictVerdict, MayorVerdict
├── api/
│   ├── server.py               # FastAPI app
│   └── websocket.py            # Real-time streaming
├── frontend/
│   └── oracle-town.html        # Single-page UI
├── tests/
│   ├── test_streets.py
│   ├── test_qi_int.py
│   └── test_remediation.py
└── config/
    ├── invariants.yaml         # Town invariants config
    ├── districts.yaml          # District/building/street topology
    └── agents.yaml             # Agent prompts + LLM assignments
```

### 5.3 Key Classes

```python
# core/orchestrator.py
class OracleTownOrchestrator:
    def __init__(self, config: TownConfig):
        self.claim_compiler = ClaimCompiler()
        self.districts = self._load_districts(config)
        self.town_hall = TownHallAgent()
        self.mayor = MayorAgent()

    async def process_input(self, user_input: TownInput) -> MayorVerdict:
        # 1. Compile claim
        claim = await self.claim_compiler.compile(user_input)

        # 2. Route to districts (parallel execution)
        district_verdicts = await asyncio.gather(*[
            district.process_claim(claim)
            for district in self.districts
        ])

        # 3. Town Hall integration
        town_rec = await self.town_hall.integrate(
            claim, district_verdicts
        )

        # 4. Mayor final verdict
        verdict = await self.mayor.decide(claim, town_rec)

        # 5. If NO_SHIP, generate remediation
        if verdict.decision == "NO_SHIP":
            verdict.remediation_roadmap = await self._generate_remediation(
                claim, verdict
            )

        return verdict

# agents/street_agent.py
class StreetAgent:
    def __init__(self, agent_config: AgentConfig):
        self.role = agent_config.role
        self.llm = agent_config.llm_model
        self.system_prompt = agent_config.system_prompt

    async def execute_turn(
        self,
        claim: CompiledClaim,
        conversation_history: List[Turn]
    ) -> Turn:
        context = self._build_context(claim, conversation_history)
        response = await self.llm.complete(
            system=self.system_prompt,
            user=context
        )
        return self._parse_turn(response)

    def _parse_turn(self, response: str) -> Turn:
        # Enforce protocol: extract CONTRIBUTION, QUESTION, ACTION
        contribution = extract_section(response, "CONTRIBUTION")
        question = extract_section(response, "QUESTION")
        action = extract_section(response, "ACTION")
        return Turn(
            agent=self.role,
            contribution=contribution,
            question=question,
            action=action
        )
```

---

## 6. SCALABILITY & COST

### 6.1 Cost Estimation (per claim processing)

**Assuming GPT-4 Turbo pricing:**
- Street agent turn: ~500 input tokens, ~300 output = $0.015
- Building supervisor: ~2000 input, ~500 output = $0.04
- District supervisor: ~4000 input, ~800 output = $0.08
- Town Hall: ~8000 input, ~1000 output = $0.15
- Mayor: ~10000 input, ~1500 output = $0.20

**Per claim (4 districts × 3 buildings × 3 streets × 4 agents):**
- 144 street turns × $0.015 = $2.16
- 12 building reviews × $0.04 = $0.48
- 4 district reviews × $0.08 = $0.32
- 1 town hall × $0.15 = $0.15
- 1 mayor × $0.20 = $0.20

**Total: ~$3.31 per claim** (with GPT-4 everywhere)

**Optimized (mixed models):**
- Street agents: Claude 3.5 Sonnet (~$1.50)
- Building/District: GPT-4 (~$0.80)
- Town/Mayor: GPT-4 (~$0.35)

**Optimized total: ~$2.65 per claim**

**Time:**
- Streets (parallel): ~30 seconds
- Buildings (parallel): ~15 seconds
- Districts (parallel): ~10 seconds
- Town Hall: ~10 seconds
- Mayor: ~10 seconds

**Total processing time: ~75 seconds per claim**

### 6.2 Scalability Patterns

**Horizontal Scaling:**
- Each district runs independently (parallel)
- Streets within district can run in parallel
- Use message queue (RabbitMQ, Redis Pub/Sub) for coordination

**Caching:**
- Common streets (GDPR, Security) can cache findings for similar claims
- Building briefs can be reused if claim unchanged

**Load Balancing:**
- Route claims to least-busy district workers
- Shard by claim_type (marketing vs legal vs technical)

---

## 7. INTEGRATION WITH EXISTING CODEBASE

### 7.1 Reuse from Marketing Street

```python
# Reuse orchestration pattern
from marketing_street_backend import CONVERSATION_PLAN, callAgent

# Adapt for ORACLE TOWN
STREET_CONVERSATION_PLAN = [
    {"agent": "agent_1", "focus": "Initial analysis"},
    {"agent": "agent_2", "focus": "Cross-check"},
    {"agent": "agent_3", "focus": "Evidence gathering"},
    {"agent": "agent_4", "focus": "Synthesis"}
]

# Same SSE streaming approach
async def run_street(street_id, claim):
    for turn in STREET_CONVERSATION_PLAN:
        response = await callAgent(turn["agent"], claim, history)
        yield f"data: {json.dumps(response)}\n\n"
```

### 7.2 Reuse from ORACLE SUPERTEAM

```python
# Reuse verdict engine
from oracle.engine import run_verdict_pipeline
from oracle.qi_int_v2 import calculate_score

# Mayor uses same logic
verdict = run_verdict_pipeline(
    claim=claim,
    evidence=town_recommendation.evidence_bundle,
    votes=district_verdicts,
    config=oracle_config
)
```

### 7.3 Reuse ORACLE TOWN Spec

```python
# Reuse invariants from IFG_ORACLE_TOWN_SPEC.md
from oracle_town.invariants import (
    check_transparency,
    check_fairness,
    check_budget_integrity,
    check_roi_realism,
    check_service_quality
)

invariants_status = {
    "transparency": check_transparency(claim, evidence),
    "fairness": check_fairness(claim, impact_analysis),
    "budget": check_budget_integrity(claim, budget_plan),
    "roi": check_roi_realism(claim, forecasts),
    "quality": check_service_quality(claim, service_metrics)
}
```

---

## 8. VISUALIZATION (AI Town-inspired)

### 8.1 Spatial Layout

```javascript
// Canvas-based town visualization
const townLayout = {
  mayor_office: { x: 400, y: 50 },
  town_hall: { x: 400, y: 150 },
  districts: [
    {
      name: "Legal",
      position: { x: 100, y: 300 },
      buildings: [
        { name: "Compliance", position: { x: 80, y: 320 } },
        { name: "Contract", position: { x: 120, y: 320 } }
      ]
    },
    {
      name: "Technical",
      position: { x: 300, y: 300 },
      buildings: [
        { name: "Architecture", position: { x: 280, y: 320 } },
        { name: "Security", position: { x: 320, y: 320 } }
      ]
    }
    // ... more districts
  ]
};

// Render active agents with glow
function renderTown(activeAgents) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Draw mayor office
  drawBuilding(mayor_office, activeAgents.includes("mayor"));

  // Draw districts
  districts.forEach(district => {
    district.buildings.forEach(building => {
      building.streets.forEach(street => {
        drawStreet(street, activeAgents.includes(street.id));
      });
    });
  });

  // Draw connections (active conversations)
  drawConversationLines(activeAgents);
}
```

### 8.2 Agent Memory & Reflection (AI Town-inspired)

```typescript
interface AgentMemory {
  agent_id: string;
  observations: Observation[];
  reflections: Reflection[];
  relationships: Map<string, number>;  // Other agents → trust score
}

interface Observation {
  timestamp: number;
  content: string;
  importance: number;  // 0-10
  source: string;      // Which claim/conversation
}

interface Reflection {
  trigger: string;     // What caused this reflection
  insight: string;     // Meta-observation
  action_change?: string;  // How behavior should adapt
}

// Agent reflects periodically
async function reflect(agent: StreetAgent) {
  const recent = agent.memory.observations.slice(-10);
  const reflection = await agent.llm.complete({
    system: "Reflect on recent observations. What patterns emerge?",
    user: JSON.stringify(recent)
  });

  agent.memory.reflections.push({
    trigger: "periodic",
    insight: reflection,
    action_change: extract_action_change(reflection)
  });
}
```

---

## 9. DEPLOYMENT ROADMAP

### Phase 1: MVP (Week 1-2)
- [ ] Core orchestrator with 1 district (Legal)
- [ ] 1 building (Compliance) with 1 street (GDPR)
- [ ] 4 agents on GDPR street
- [ ] Simple verdict engine (SHIP/NO_SHIP only)
- [ ] Command-line interface

**Deliverable:** Prove end-to-end flow with real LLM

### Phase 2: Multi-District (Week 3-4)
- [ ] Add 3 more districts (Technical, Business, Social)
- [ ] 2 buildings per district
- [ ] QI-INT v2 scoring
- [ ] Town Hall agent
- [ ] Basic web UI (single HTML)

**Deliverable:** Full 4-district verdict with visualization

### Phase 3: Remediation Loop (Week 5-6)
- [ ] Mayor remediation roadmap generation
- [ ] V2 Proposal builder
- [ ] Monotonic weakening logic
- [ ] Iteration tracking

**Deliverable:** NO_SHIP → improve → SHIP flow working

### Phase 4: Production Hardening (Week 7-8)
- [ ] Session persistence (PostgreSQL)
- [ ] Audit trail (all decisions + evidence)
- [ ] Cost tracking per claim
- [ ] Rate limiting
- [ ] Authentication
- [ ] FastAPI REST API

**Deliverable:** Production-ready system

### Phase 5: Advanced Features (Week 9-12)
- [ ] Agent memory & reflection (AI Town-style)
- [ ] Spatial visualization (Canvas)
- [ ] Caching & optimization
- [ ] Multi-claim batch processing
- [ ] Analytics dashboard

**Deliverable:** Fully-featured ORACLE TOWN

---

## 10. SUCCESS CRITERIA

### Functional
- ✅ Accepts natural language input
- ✅ Produces binary verdict (SHIP/NO_SHIP) in <2 minutes
- ✅ Generates remediation roadmap for NO_SHIP
- ✅ All verdicts have evidence trail
- ✅ Replay determinism (same input → same verdict)

### Quality
- ✅ 95%+ protocol compliance (agents follow CONTRIBUTION/QUESTION/ACTION)
- ✅ Zero contradictions in evidence
- ✅ All blocking obligations identified
- ✅ No kill-switch false positives

### Performance
- ✅ <2 minutes processing time per claim
- ✅ <$5 cost per claim (optimized)
- ✅ Supports 10+ concurrent claims

### Governance
- ✅ Constitutional rules never violated
- ✅ All invariants checked
- ✅ Audit trail complete (Git hash + timestamps)
- ✅ No manual overrides (verdicts are deterministic)

---

## 11. EXAMPLE END-TO-END FLOW

**User Input:**
```
"Launch a new tourism campaign targeting millennials for Calvi 2030.
Budget: 50k EUR. Goal: 20% increase in 25-34 visitor bookings.
Use Instagram + TikTok. Launch in 3 months."
```

**Claim Compiler:**
```typescript
CompiledClaim {
  claim_id: "CLM_2026_001",
  claim_text: "Tourism campaign (Instagram+TikTok) targeting 25-34 demographic for 20% booking uplift within 3 months",
  claim_type: "CAMPAIGN",
  success_criteria: [
    "20% increase in bookings from 25-34 age group",
    "Launch by April 2026",
    "Stay within 50k EUR budget"
  ],
  requires_receipts: true,
  initial_obligations: []
}
```

**District Processing (parallel):**

*Legal District:*
- GDPR Street: "Instagram pixel requires cookie consent banner" → CONDITIONAL
- Contract Street: "Influencer contracts need review" → CONDITIONAL
- Building verdict: CONDITIONAL (2 obligations)

*Technical District:*
- Architecture Street: "Landing page infrastructure OK" → APPROVE
- Security Street: "Payment gateway needs PCI audit" → CONDITIONAL
- Building verdict: CONDITIONAL (1 obligation)

*Business District:*
- Marketing Street: "Campaign messaging looks strong" → APPROVE
- Finance Street: "ROI projection realistic" → APPROVE
- Building verdict: APPROVE

*Social District:*
- UX Street: "Mobile experience needs optimization" → CONDITIONAL
- Community Street: "Local business partnerships recommended" → APPROVE
- Building verdict: CONDITIONAL (1 obligation)

**Town Hall:**
```typescript
TownRecommendation {
  qi_int_score: 0.72,  // Just below threshold
  invariants_check: {
    transparency: true,
    fairness: true,
    budget_integrity: true,
    roi_realism: true,
    service_quality: false  // Mobile UX issue
  },
  blocking_obligations: [
    "Cookie consent implementation",
    "Influencer contract review",
    "PCI compliance audit",
    "Mobile UX optimization"
  ],
  recommendation: "NO_GO"  // Score + invariant fail
}
```

**Mayor Verdict:**
```typescript
MayorVerdict {
  decision: "NO_SHIP",
  rationale: "Score (0.72) below threshold (0.75). Service quality invariant failed. 4 blocking obligations.",
  blocking_reasons: [
    "Mobile UX not optimized",
    "Missing cookie consent",
    "Influencer contracts not reviewed",
    "PCI audit pending"
  ],
  remediation_roadmap: [
    {
      step: "Implement cookie consent banner",
      effort: "low",
      timeline: "1 week",
      responsible: "Legal Building"
    },
    {
      step: "Complete influencer contract review",
      effort: "medium",
      timeline: "2 weeks",
      responsible: "Legal Building"
    },
    {
      step: "Optimize mobile landing page",
      effort: "medium",
      timeline: "2 weeks",
      responsible: "Technical Building"
    },
    {
      step: "Schedule PCI audit",
      effort: "high",
      timeline: "4 weeks",
      responsible: "Technical Building"
    }
  ]
}
```

**User receives:**
- ❌ NO_SHIP verdict
- 📋 Clear list of 4 blockers
- 🛠️ Remediation roadmap with timelines
- 🔄 Option to iterate and resubmit

---

## 12. NEXT STEPS

Choose your starting point:

**Option A: Quick Prototype (1-2 days)**
- Single district, single street, 4 agents
- Command-line interface
- Proves concept with real LLMs

**Option B: MVP Implementation (1-2 weeks)**
- All 4 districts
- Basic web UI
- Full verdict flow

**Option C: Full Production (2-3 months)**
- All features
- Production hardening
- Deployment infrastructure

---

**Ready to build ORACLE TOWN?** 🏛️

Let me know which option you prefer, and I'll generate the starter code package.
