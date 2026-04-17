# 🏛️ ORACLE TOWN

**Hierarchical Multi-Agent Governance System**

Transform natural language inputs into verified, shippable claims through a constitutional civic simulation.

---

## 🎯 What is ORACLE TOWN?

ORACLE TOWN is a scalable governance framework that combines:

- **ChatDev**: Structured turn protocol, orthogonal agent roles, deliverables-focused
- **AI Town (Stanford)**: Spatial simulation, emergent behaviors, agent memory
- **ORACLE SUPERTEAM**: Constitutional governance, binary verdicts, obligation tracking

### Architecture

```
INPUT → CLAIM COMPILER
  ↓
STREETS (4 agents/street, ChatDev-style turns)
  ↓
BUILDINGS (2-4 streets aggregated)
  ↓
DISTRICTS (4 domains: Legal/Technical/Business/Social)
  ↓
TOWN HALL (QI-INT scoring + invariants check)
  ↓
MAYOR (final verdict: SHIP / NO_SHIP)
  ↓
REMEDIATION ROADMAP (if NO_SHIP)
```

---

## 🚀 Quick Start

### Installation

```bash
# No dependencies needed for MVP (uses mock LLM)
cd oracle-town

# For production with real LLMs:
# pip install openai anthropic
```

### Basic Usage

```python
import asyncio
from oracle_town import process_text

async def main():
    verdict = await process_text(
        "Launch a marketing campaign collecting user emails for newsletter"
    )
    print(f"Decision: {verdict.decision}")
    print(f"Rationale: {verdict.rationale}")

asyncio.run(main())
```

### CLI Usage

```bash
# Single claim
python oracle-town/cli.py "Launch tourism campaign with GPS tracking"

# Interactive mode
python oracle-town/cli.py --interactive

# Specify domain
python oracle-town/cli.py --domain=policy "Implement GDPR policy"

# Batch processing
python oracle-town/cli.py --batch=claims.txt
```

---

## 📊 Example Output

**Input:**
```
Launch a tourism campaign targeting millennials. Collect visitor emails and GPS location
data for personalized recommendations. Use Google Maps API. Budget: 50k EUR.
Goal: 20% increase in bookings. Launch in 3 months.
```

**Output:**
```
❌ FINAL VERDICT: NO_SHIP

Blocking Reasons:
  1. GDPR consent mechanism: Implement cookie consent banner for GPS tracking
  2. Mobile optimization: Mobile UX needs work

REMEDIATION ROADMAP (2 steps)

[Step 1] Implement GDPR consent mechanism: Implement cookie consent banner for GPS tracking
  │ Effort: LOW
  │ Timeline: 1 week
  │ Responsible: Legal & Compliance District
  │ Evidence: consent_flow_diagram, legal_sign_off
  └─ Success: Legal team signs off on GDPR consent mechanism with documented evidence

[Step 2] Optimize Mobile optimization: Mobile UX needs work
  │ Effort: MEDIUM
  │ Timeline: 2-3 weeks
  │ Responsible: Social & Impact District
  │ Evidence: ux_metrics, mobile_test_results
  └─ Success: UX metrics meet target thresholds (specified in obligation)
```

---

## 🏗️ System Components

### Core Components

- **ClaimCompiler**: Transforms natural language → structured claim
- **StreetAgent**: Base class for all agents (enforces turn protocol)
- **BuildingSupervisor**: Aggregates street reports
- **DistrictSupervisor**: Produces district verdict with vote weight
- **TownHallAgent**: QI-INT v2 scoring + invariants checking
- **MayorAgent**: Final binary verdict + remediation generation
- **OracleTownOrchestrator**: Main execution engine

### Districts (MVP: Legal only, Production: 4 districts)

1. **Legal & Compliance** (vote weight: 1.0, KILL authority)
   - GDPR Street: Privacy, Legal Counsel, Vendor Auditor, Integrator

2. **Technical & Security** (vote weight: 1.0, KILL authority)
   - _Coming soon_

3. **Business & Operations** (vote weight: 0.75)
   - _Coming soon_

4. **Social & Impact** (vote weight: 0.70)
   - _Coming soon_

---

## 🎓 Key Concepts

### Turn Protocol (ChatDev-inspired)

Every agent MUST respond with:
```
## CONTRIBUTION
[Agent's primary analysis/findings]

## QUESTION
[Directed to specific other agent or next phase]

## ACTION
[What happens next based on findings]
```

### QI-INT v2 Scoring

Quantum Interference Integration calculates final score:

```
a_{district} = vote_weight × e^(i × phase)
A_c = Σ a_{district}
S_c = |A_c|²
```

Where phase = 0 (APPROVE) to π (KILL)

### Constitutional Rules (immutable)

1. IF kill_switch → NO_SHIP (immediate)
2. ELSE IF blocking_obligations > 0 → NO_SHIP
3. ELSE IF invariants_failed → NO_SHIP
4. ELSE IF score < 0.75 → NO_SHIP
5. ELSE → SHIP

### Monotonic Weakening

Remediation never strengthens claims, only reduces scope:
- Feature (Tier A) → Pilot (Tier B) → Experiment (Tier C)
- Never: Pilot → Feature

---

## 📈 Cost & Performance

### MVP (Mock LLM)
- **Cost**: $0 per claim
- **Time**: ~5 seconds per claim
- **Use case**: Testing, development, demos

### Production (Real LLMs)
- **Cost**: ~$2.65 per claim (optimized)
  - Streets: Claude 3.5 Sonnet (~$1.50)
  - Building/District: GPT-4 (~$0.80)
  - Town/Mayor: GPT-4 (~$0.35)
- **Time**: ~75 seconds per claim
- **Scalability**: Fully parallel at district level

---

## 🛠️ Development

### Project Structure

```
oracle-town/
├── core/
│   ├── claim_compiler.py       # Input → CompiledClaim
│   ├── orchestrator.py         # Main execution loop
│   ├── town_hall.py            # QI-INT integration
│   └── mayor.py                # Final verdict + remediation
├── agents/
│   ├── street_agent.py         # Base class (turn protocol)
│   ├── building_supervisor.py  # Building aggregation
│   └── district_supervisor.py  # District verdict
├── districts/
│   └── legal/
│       └── gdpr_street.py      # 4-agent GDPR analysis
├── schemas/
│   ├── claim.py                # TownInput, CompiledClaim, Obligation
│   ├── reports.py              # Turn, StreetReport, BuildingBrief
│   └── verdict.py              # TownRecommendation, MayorVerdict
└── cli.py                      # Command-line interface
```

### Adding a New Street

```python
from oracle_town.agents import StreetAgent

class SecurityAnalystAgent(StreetAgent):
    def __init__(self):
        system_prompt = """You are a Security Analyst.

        Identify security vulnerabilities...

        Output format:
        ## CONTRIBUTION
        [Your security analysis]

        ## QUESTION
        [Question to next agent]

        ## ACTION
        [Security actions required]"""

        super().__init__(
            agent_id="security_analyst_001",
            role="Security Analyst",
            system_prompt=system_prompt,
        )
```

### Adding a New District

```python
from oracle_town.core.orchestrator import District
from .security_street import SecurityStreet

technical_district = District(
    district_id="technical_001",
    district_name="Technical & Security",
    streets=[SecurityStreet(), PerformanceStreet()],
)
```

---

## 🧪 Testing

```bash
# Run core tests
python -m pytest oracle-town/tests/

# Test claim compiler
python oracle-town/core/claim_compiler.py

# Test GDPR street
python oracle-town/districts/legal/gdpr_street.py

# Test full orchestrator
python oracle-town/core/orchestrator.py
```

---

## 📚 Documentation

- **[ORACLE_TOWN_IMPLEMENTATION.md](../ORACLE_TOWN_IMPLEMENTATION.md)**: Complete 600+ line spec
- **[CLAUDE.md](../CLAUDE.md)**: Integration with existing codebase
- **[ARCHITECTURE.md](../ARCHITECTURE.md)**: System design deep-dive

---

## 🤝 Integration with Existing Codebase

ORACLE TOWN reuses components from:

1. **Marketing Street** (`marketing-street-backend.js`)
   - SSE streaming pattern
   - Agent orchestration
   - Turn protocol enforcement

2. **ORACLE SUPERTEAM** (`oracle-superteam/`)
   - QI-INT v2 scoring (`oracle/qi_int_v2.py`)
   - Verdict engine (`oracle/engine.py`)
   - Constitutional governance (`CONSTITUTION.md`)

3. **ORACLE TOWN Spec** (`oracle-superteam/IFG_ORACLE_TOWN_SPEC.md`)
   - Invariants (transparency, fairness, budget, ROI, quality)
   - Viability-thermostat system design

---

## 🎯 Roadmap

### ✅ Phase 1: MVP (Complete)
- [x] Core orchestrator
- [x] Legal district with GDPR street
- [x] Turn protocol enforcement
- [x] QI-INT scoring
- [x] Mayor verdict + remediation
- [x] CLI interface

### 🚧 Phase 2: Multi-District (In Progress)
- [ ] Technical & Security district
- [ ] Business & Operations district
- [ ] Social & Impact district
- [ ] Web UI (HTML + Canvas visualization)

### 📋 Phase 3: Production Features
- [ ] Real LLM integration (OpenAI, Anthropic)
- [ ] FastAPI server with WebSocket
- [ ] Session persistence (PostgreSQL)
- [ ] Agent memory & reflection (AI Town-style)
- [ ] Cost tracking & optimization
- [ ] Audit trail & replay

### 🚀 Phase 4: Advanced
- [ ] Spatial town visualization (Canvas)
- [ ] Multi-claim batch processing
- [ ] Analytics dashboard
- [ ] Custom district builder
- [ ] Agent marketplace

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

Built on insights from:
- **ChatDev** (Qian et al.): Structured multi-agent collaboration
- **AI Town** (Stanford): Emergent agent behaviors in spatial simulation
- **ORACLE SUPERTEAM**: Constitutional governance frameworks

---

## 🆘 Support

For issues, questions, or contributions:
- See [ORACLE_TOWN_IMPLEMENTATION.md](../ORACLE_TOWN_IMPLEMENTATION.md) for technical details
- Check [CLAUDE.md](../CLAUDE.md) for development guide

---

**Built with ❤️ by the ORACLE TOWN team**

_Transforming ideas into verified, shippable reality through constitutional multi-agent governance._
