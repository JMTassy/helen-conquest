# CALVI 2030: MEDITERRANEAN GUARDIAN OF INTELLIGENCE

**Vision Document V2.1 — Technical Refinement**
**Office of the Mayor of Calvi**
**Validated by ORACLE TOWN WUL 1 + CALVI_TWIN v0.1.0**
**January 2026**

---

## EXECUTIVE SUMMARY

Calvi stands at a decisive moment. The Mediterranean demands responsible innovation in autonomous systems, environmental monitoring, and scientific cooperation. We will not compete with Silicon Valley's promises. We will deliver what the world needs: **verified capability, Mediterranean wisdom, and receipt-first discipline**.

By 2030, Calvi becomes the **City of Receipts** — where autonomous systems are certified, where training produces measurable outcomes, and where the **jumeau numérique** (digital twin) enables every decision to be tested before implementation through deterministic SHIP/NO_SHIP governance.

**This is not aspiration. This is architecture.**

The CALVI_TWIN system — our governance-grade digital twin — now operationalizes the ORACLE BACKBONE constitutional framework with **production → adjudication → integration** determinism. Every claim passes through non-sovereign teams (MAYOR, LEGAL, SAFETY, ENVIRONMENT, BUDGET, OPERATIONS, COMMS), lexicographic veto adjudication, and a binary integration gate: **SHIP iff (receipt_gap = 0 AND no_veto)**.

---

## PART I: THE ORACLE BACKBONE — TECHNICAL FOUNDATION

### Constitutional Axioms (Non-Negotiable)

**A1. NO_RECEIPT = NO_SHIP**
Any Tier-I claim (real-world effect, operational authorization, budget execution, legal compliance) requires hash-verifiable receipts with authorized attestors. No attestation → NO_SHIP.

**A2. NON-SOVEREIGN PRODUCTION**
All teams and personas (including MAYOR_TWIN) emit **signals** and **obligations** only — never verdicts. Verdicts emerge from the integration gate, not from persuasion.

**A3. BINARY VERDICT**
Output is exactly one token: **SHIP** or **NO_SHIP**. No maybes, no conditionals, no narrative laundering.

**A4. KILL DOMINANCE (LEXICOGRAPHIC VETO)**
Safety, legal, security blocks override any score, narrative, or preference. First veto wins.

**A5. REPLAY DETERMINISM**
Same canonical inputs (claim + receipts + cfg_version) → same canonical outputs (verdict + obligations + hashes). Every decision is replayable and auditable.

### What We Learned from WUL-ORACLE Analysis

ORACLE TOWN WUL 1 analyzed our initial claims through receipt-first governance. The verdict is instructive:

**TIER 1 — SHIP NOW (Immediate Deployment)**
- **C5 (Governance Framework)**: Receipt-ledger workflow operational, all attestations validated → `verdict: SHIP`
- **C7 (Regulatory Compliance)**: EASA/EU-AI-Act framework with verified audit trails → `verdict: SHIP`
- **C8 (Digital Twin Deployment)**: CALVI_TWIN v0.1.0 operational with EASA + STARESO attestations → `verdict: SHIP`

**TIER 2 — SHIP AFTER ATTESTATIONS (24-Month Horizon)**
- **C1 (Training Efficiency)**: 30-35% reduction target — `verdict: NO_SHIP` (EVIDENCE_MISSING: RCT attestation)
- **C2 (Safety Performance)**: 40-50% incident reduction — `verdict: NO_SHIP` (EVIDENCE_MISSING: 12mo incident database)
- **C4 (Scientific Output)**: ≥4 FAIR datasets/year — `verdict: NO_SHIP` (LEGAL_COMPLIANCE: STARESO partnership MoU not finalized)

**TIER 3 — DEFERRED (Conditional on Evidence)**
- **C3 (Economic Impact)**: ≥800 bed-nights, 12-15 FTE — `verdict: NO_SHIP` (BUDGET_UNJUSTIFIED: market validation missing)
- **C6 (Replication Blueprint)**: Transferable model — `verdict: NO_SHIP` (OPERATIONAL_DEPENDENCY: 3+ year track record required)

**The Oracle's Teaching**: Ambition without attestation is noise. We advance on verified ground.

---

## PART II: THE CALVI DOCTRINE — RECEIPT-FIRST DISCIPLINE

### 1. Every Claim is a Contract

**Principle**: No claim without ledger. No promise without pin. No decision without determinism.

Every capability announcement from Calvi Academy will be accompanied by:

1. **WUL Token Tree** (machine-checkable claim structure, bounded depth ≤64, bounded nodes ≤512)
   ```json
   {"id": "R15", "args": [{"id": "E03", "ref": "OBJECTIVE_UAV_SAFETY"}, {"id": "D01", "args": [...]}]}
   ```

2. **Tribunal Bundle** (required obligations with severity levels: HARD/SOFT)
   - EVIDENCE_MISSING
   - LEGAL_COMPLIANCE
   - SAFETY_RISK
   - ENVIRONMENTAL_RISK
   - BUDGET_UNJUSTIFIED
   - OPERATIONAL_DEPENDENCY

3. **Attestations Ledger** (who verified what, when, how — with sha256 hashes)
   ```json
   {"path": "attestations/easa_part_uas_2026.pdf", "hash": "sha256:a3f2b...", "attestor": "EASA", "timestamp": "2026-01-15T09:00:00Z"}
   ```

4. **Mayor Decision Record** (deterministic SHIP/NO_SHIP with reason codes)
   ```python
   verdict = NO_SHIP if (receipt_gap > 0 or any_veto) else SHIP
   ```

5. **Run Manifest** (inputs_hash + outputs_hash for replay verification)
   ```json
   {"inputs_hash": "sha256:9f4e2a...", "outputs_hash": "sha256:1b7c8d...", "cfg_version": "CALVI_TWIN_v0.1.0"}
   ```

**We do not ask the world to trust us. We give the world receipts to verify us.**

### 2. The Guardian Mode

**Calvi is not a factory. Calvi is a guardian.**

We train operators for:
- **Multi-environment autonomy** (UAV/USV/AUV in Mediterranean complexity)
- **Ethical decision protocols** (when to override, when to ground, when to abort)
- **Scientific stewardship** (FAIR data, reproducible research, open validation)

**Guardian Mode operationalization**:
- SAFETY_TEAM emits `SAFETY_RISK` obligations with closure criteria
- LEGAL_TEAM monitors EASA Part-UAS certification expiry (annual recertification required)
- ENVIRONMENT_TEAM tracks marine protected area compliance (Posidonia meadows, cetacean disturbance)
- MAYOR_TWIN provides policy vector but **never overrides kill-switches**

Our graduates do not merely pilot drones. They guard the boundary between capability and wisdom.

### 3. The Mediterranean Advantage

**Geography is destiny. We embrace it.**

- **STARESO Research Station**: 50+ years of marine science, now integrated with robotic observation platforms → attestor authority for marine environmental claims
- **Calvi Bay**: Natural laboratory for autonomous maritime systems (currents, visibility gradients, marine traffic) → digital twin scenario library with ≥95% operational envelope coverage
- **Corsican Terrain**: Mountain-to-sea gradient for UAV stress testing (wind shear, thermal turbulence, rapid elevation change) → failure mode validation database
- **European Regulatory Crossroads**: French legal framework + EU harmonization + Mediterranean partnership networks → EASA/EU-AI-Act compliance template

What Silicon Valley simulates, we validate in the real world.

---

## PART III: THE 2030 ARCHITECTURE — TIER-BY-TIER DEPLOYMENT

### Phase 1: FOUNDATIONS (2026-2027)

**Immediate Deployments (TIER 1 — Already Shippable: `verdict: SHIP`)**

#### 1. Receipt-Ledger Governance Framework (C5)

**Technical Implementation:**
- Deploy CALVI_TWIN v0.1.0 for all training program claims
- Production teams: MAYOR, LEGAL, SAFETY, ENVIRONMENT, BUDGET, OPERATIONS, COMMS
- Adjudication: Lexicographic veto with kill-switch dominance
- Integration gate: `SHIP iff (receipt_gap=0 AND no_veto)`

**Deliverables:**
- `governance.calvi.town` — live transparency portal with claim feed, obligation tracker, evidence vault
- Public API: `/claims/{id}/verdict`, `/claims/{id}/replay`, `/obligations/open`
- Run manifest archive: 100% decision replayability with hash verification

**Receipt Status**: ✅ SHIP (attestations from ORACLE TOWN WUL 1, deterministic gate operational)

**Budget Allocation**: €800K (governance infrastructure + personnel)

---

#### 2. Regulatory Compliance Infrastructure (C7)

**Technical Implementation:**
- EASA Part-UAS compliance framework (operational procedures, pilot training, incident reporting)
- EU AI Act risk classification (HIGH for autonomous UAV, LIMITED for supervised operations)
- GDPR compliance (training data anonymization, participant consent, retention policies)
- French civil aviation law (airspace authorization protocols, insurance attestations)

**Obligation Tracking:**
```python
Obligation(
    oid="OBL_C7_EASA_RENEWAL",
    type=ObligationType.LEGAL_COMPLIANCE,
    owner="LEGAL_TEAM",
    closure_criteria="Annual EASA Part-UAS recertification by 2027-03-15",
    status="OPEN"
)
```

**Deliverables:**
- Full compliance audit trail for external validators
- Quarterly legal compliance reports with reason code breakdowns
- LEGAL_TEAM signal monitoring (CERTIFICATION_CURRENT vs. CERTIFICATION_EXPIRED)

**Receipt Status**: ✅ SHIP (EASA attestation valid until 2027-03-15, ongoing monitoring obligation accepted)

**Budget Allocation**: €600K (compliance framework + legal personnel)

---

#### 3. Digital Twin Foundation (Jumeau Numérique / CALVI_TWIN)

**Technical Implementation:**
- High-fidelity simulation of Calvi Bay (bathymetry, currents, weather patterns from STARESO historical data)
- Integrated UAV/USV/AUV dynamics models (rotor failure, communication loss, GPS degradation)
- Scenario library: 200+ test conditions by 2030 (equipment failure, weather degradation, emergency protocols)
- **Governance integration**: Every real-world operation requires `verdict: SHIP` from CALVI_TWIN digital governance filter

**Current Status (Q1 2026)**:
- Scenario library: 87 validated scenarios
- Operational capacity: 50 concurrent scenarios
- Current utilization: 12 avg scenarios/day
- Sim-to-real correlation: ≥90% (STARESO validation Q4 2025)

**Deliverables:**
- CALVI_TWIN v0.1.0 operational (Python implementation, canonical hashing, replay determinism)
- Monthly validation correlation reports (simulated vs. actual outcomes)
- Model improvement changelog with version control

**Receipt Status**: ✅ SHIP (EASA + STARESO attestations verified, ongoing monitoring obligation for ≥90% correlation)

**Budget Allocation**: €1.2M (digital twin infrastructure + scenario development + personnel)

---

**Phase 1 Budget Summary**: €2.8M (secured from regional development fund + EASA partnership)

**Phase 1 Verdict**: `verdict: SHIP` for C5, C7, C8 with OPEN monitoring obligations accepted.

---

### Phase 2: CAPABILITY VALIDATION (2027-2029)

**Conditional Deployments (TIER 2 — Pending Attestations: `verdict: NO_SHIP` until obligations CLOSED)**

#### 4. Training Efficiency Program (C1-refined)

**Current Verdict**: `NO_SHIP`

**Blocking**:
```python
[
    BlockingItem(
        code=ReasonCode.RECEIPT_MISSING,
        detail="Claim requires RCT experimental validation; only curriculum design provided",
        evidence_paths=["planning/curriculum_design_2026.pdf"]
    ),
    BlockingItem(
        code=ReasonCode.EVIDENCE_MISSING,
        detail="No pre-registered RCT protocol, no independent evaluator attestation",
        evidence_paths=[]
    )
]
```

**Open Obligations**:
1. **OBL_C1_001** (EVIDENCE_MISSING)
   - Owner: ACADEMY_DIRECTOR
   - Closure: Pre-register RCT protocol on Open Science Framework
   - Status: OPEN

2. **OBL_C1_002** (EVIDENCE_MISSING)
   - Owner: ACADEMY_DIRECTOR
   - Closure: Select independent academic evaluator with blinded assessment protocol
   - Status: OPEN

3. **OBL_C1_003** (METRICS_INSUFFICIENT)
   - Owner: ACADEMY_DIRECTOR
   - Closure: Complete 12-month longitudinal tracking with RCT attestation + peer-reviewed publication
   - Status: OPEN

**Target**: 30-35% reduction in time-to-competency vs. traditional programs

**Shipment Condition**: `verdict: SHIP` when all obligations CLOSED (estimated 2027-2028)

**Budget Allocation**: €1.5M (RCT implementation + academic partnership + longitudinal tracking)

---

#### 5. Safety Performance Validation (C2-refined)

**Current Verdict**: `NO_SHIP`

**Blocking**:
```python
[
    BlockingItem(
        code=ReasonCode.RECEIPT_GAP_NONZERO,
        detail="12-month incident database required; only 3 months available",
        evidence_paths=["safety/incident_log_2025_Q4.json"]
    )
]
```

**Open Obligations**:
1. **OBL_C2_001** (EVIDENCE_MISSING)
   - Owner: SAFETY_TEAM
   - Closure: 12-month structured incident database with EASA categories (SHELL model, root-cause analysis)
   - Status: OPEN

2. **OBL_C2_002** (METRICS_INSUFFICIENT)
   - Owner: SAFETY_TEAM
   - Closure: Comparative analysis with EU-wide baseline (40-50% reduction verification)
   - Status: OPEN

**Target**: 40-50% incident reduction vs. industry baseline

**Shipment Condition**: `verdict: SHIP` when 12mo database complete + EASA safety audit attestation (estimated 2027-Q4)

**Budget Allocation**: €1.2M (incident database + safety infrastructure + monthly review panels)

---

#### 6. Scientific Output Partnership (C4-refined)

**Current Verdict**: `NO_SHIP`

**Blocking**:
```python
[
    BlockingItem(
        code=ReasonCode.LEGAL_COMPLIANCE_OPEN,
        detail="STARESO partnership MoU not finalized; data publication pipeline undefined",
        evidence_paths=["drafts/stareso_collaboration_draft_2025.pdf"]
    )
]
```

**Open Obligations**:
1. **OBL_C4_001** (LEGAL_COMPLIANCE)
   - Owner: MAYOR_OFFICE
   - Closure: Finalize STARESO partnership MoU with data publication terms, IP assignment, authorship protocols
   - Status: OPEN

2. **OBL_C4_002** (EVIDENCE_MISSING)
   - Owner: RESEARCH_COORDINATOR
   - Closure: 2-year publication track record with ≥4 FAIR datasets/year (F-UJI score ≥80%, DOI registration)
   - Status: OPEN

**Target**: ≥4 FAIR datasets per year (marine robotics, environmental monitoring)

**Shipment Condition**: `verdict: SHIP` when STARESO MoU signed + 2-year track record validated (estimated 2028-2029)

**Budget Allocation**: €1.8M (STARESO partnership + robotic platforms + data publication pipeline)

---

**Phase 2 Budget Summary**: €5.2M (EU Horizon Europe proposal + regional co-financing)

**Phase 2 Verdict**: All claims currently `NO_SHIP` with clear obligation closure paths. No shipment before attestations.

---

### Phase 3: MEDITERRANEAN LEADERSHIP (2029-2030)

**Strategic Expansion (TIER 3 — Evidence-Dependent: `verdict: NO_SHIP` until prerequisites met)**

#### 7. Economic Impact Demonstration (C3-refined)

**Current Verdict**: `NO_SHIP`

**Blocking**:
```python
[
    BlockingItem(
        code=ReasonCode.BUDGET_UNJUSTIFIED,
        detail="Market validation missing; 800 bed-nights claim lacks customer pipeline attestation",
        evidence_paths=[]
    ),
    BlockingItem(
        code=ReasonCode.OPERATIONAL_DEPENDENCY_OPEN,
        detail="Conditional on C1 (training), C2 (safety), C4 (scientific output) SHIP verdicts",
        evidence_paths=["verdicts/C1_NO_SHIP.json", "verdicts/C2_NO_SHIP.json", "verdicts/C4_NO_SHIP.json"]
    )
]
```

**Prerequisites**:
- C1 (Training Efficiency): `verdict: SHIP` required
- C2 (Safety Performance): `verdict: SHIP` required
- C4 (Scientific Output): `verdict: SHIP` required
- Market validation: Customer pipeline with ≥500 bed-nights pre-booked

**Target**: ≥800 professional bed-nights/year, 12-15 FTE sustained employment

**Shipment Condition**: `verdict: SHIP` earliest 2029-2030 (after Phase 2 completion + market evidence)

**Budget Allocation**: €1.2M (market development, conditional on Phase 2 success)

---

#### 8. Replication Blueprint (C6)

**Current Verdict**: `NO_SHIP`

**Blocking**:
```python
[
    BlockingItem(
        code=ReasonCode.OPERATIONAL_DEPENDENCY_OPEN,
        detail="3+ years operational track record required; currently 0 years",
        evidence_paths=[]
    ),
    BlockingItem(
        code=ReasonCode.EVIDENCE_MISSING,
        detail="Published safety/training validation studies required for knowledge transfer",
        evidence_paths=[]
    )
]
```

**Prerequisites**:
- 3+ years operational track record (2026-2029)
- Published validation studies (C1 RCT publication, C2 safety audit)
- Documented governance framework (CALVI_TWIN v1.0+)

**Target**: Export "Calvi Protocol" to Mediterranean partner cities (Marseille, Barcelona, Genoa, Athens)

**Shipment Condition**: `verdict: SHIP` earliest 2030 (after 3-year operational validation)

**Budget Allocation**: €900K (replication blueprint + knowledge transfer)

---

**Phase 3 Budget Summary**: €3.5M (subject to market validation + Phase 2 completion)

**Phase 3 Verdict**: All claims `NO_SHIP` with long-term conditional dependencies. No premature replication.

---

## PART IV: THE CALVI WORLD MODEL — 2030 PROJECTION

### Vision: Mediterranean Intelligence Infrastructure

By 2030, Calvi operates as the **Mediterranean node** in a distributed intelligence network with **4 integrated layers**:

#### **Physical Layer**
- **Calvi Academy**: 120-150 graduates/year across 4 formations (drone pilot, robotics technician, data steward, scientific mediator)
- **STARESO Integration**: Permanent robotic observation platforms (3 USV, 2 AUV, aerial drone fleet)
- **Digital Twin Facility**: Real-time simulation capacity for 50+ concurrent scenarios (87 scenarios in Q1 2026 → 200+ by 2030)
- **Testing Range**: Certified airspace + maritime zones for autonomous system validation

#### **Data Layer**
- **Environmental Observatory**: Continuous multi-modal sensing (ocean temperature, salinity, currents, biodiversity, atmospheric conditions)
- **FAIR Data Repository**: 40+ datasets (cumulative) available to global research community
- **Incident Knowledge Base**: 10,000+ structured incident records for safety analysis
- **Training Analytics**: Longitudinal competency tracking for curriculum optimization

#### **Governance Layer** (CALVI_TWIN Constitutional Architecture)
- **Receipt-Ledger Public Dashboard**: Every claim, every attestation, every decision — transparent and queryable at `governance.calvi.town`
- **Production Teams**: MAYOR, LEGAL, SAFETY, ENVIRONMENT, BUDGET, OPERATIONS, COMMS (non-sovereign signals + obligations)
- **Adjudication Engine**: Lexicographic veto with kill-switch dominance
- **Integration Gate**: Deterministic SHIP/NO_SHIP with replay hashes
- **Reason Code Taxonomy**: 9 canonical codes (RECEIPT_MISSING, LEGAL_COMPLIANCE_OPEN, SAFETY_RISK_OPEN, etc.)

#### **Partnership Layer**
- **Academic Network**: 8-12 European universities (marine science, robotics, human factors, AI ethics)
- **Industry Consortium**: 15-20 partners (drone manufacturers, software providers, maritime operators)
- **Regulatory Bodies**: EASA, ANSM (French safety agency), EU AI Office
- **Mediterranean Cities**: Barcelona, Genoa, Marseille, Athens, Valletta — knowledge exchange and pilot replication

---

## PART V: POLITICAL DISCOURSE VERSIONS

### FOR CITIZENS OF CALVI

**We are building something rare: a technology center that serves wisdom, not hype.**

Your city will not become a generic "tech hub." We will become guardians — training the people who decide when machines should act and when they should wait. The Mediterranean has always been about navigation, about reading wind and current. Now we teach machines to do the same, and we teach humans to teach machines when to stop.

**This will create jobs** (12-15 permanent positions, 50+ seasonal). **This will bring visitors** (800+ professional training participants per year). But more than that, it will give Calvi a voice in how autonomous systems are built and regulated across Europe.

**Receipt-first discipline means you can verify every claim we make.** No politician's promise. No consultant's forecast. Just data, attestations, and gaps we're still working to close.

**The CALVI_TWIN digital governance system** is now operational. You can see every decision, every obligation, every attestation at `governance.calvi.town`. When we say NO_SHIP, you see the reason codes. When we say SHIP, you see the receipts. This is not politics. This is architecture.

---

### FOR SCIENTIFIC PARTNERS

**We offer what academic institutions need: operational validation capacity.**

Your models need real-world testing. Your datasets need provenance. Your safety protocols need incident data. Calvi provides:
- **Multi-environment robotics platforms** (UAV/USV/AUV with continuous operation)
- **FAIR-compliant data publication pipeline** (F-UJI score ≥80%, DOI registration, metadata standardization)
- **Structured incident database** (SHELL model, EASA categories, 10,000+ records by 2030)
- **Digital twin for pre-deployment scenario testing** (200+ validated scenarios, ≥90% sim-to-real correlation)

STARESO brings 50 years of marine science credibility. We bring the governance infrastructure to make robotic observation platforms trustworthy. Together, we create the Mediterranean reference implementation for autonomous environmental monitoring.

**Everything is open. Everything is reproducible. Everything is attested.**

**CALVI_TWIN attestor authority**: STARESO-validated claims receive `receipt.attestor = "STARESO_TECHNICAL_LEAD"` with sha256 hashes for verification. You can replay our decisions with canonical inputs and verify outputs match our published manifests.

---

### FOR REGULATORY AUTHORITIES

**We are building the compliance template you need for autonomous system certification.**

The EU AI Act requires risk management, transparency, human oversight. EASA Part-UAS requires operational safety demonstration. Both require documentation that most startups cannot provide.

Calvi Academy will be the reference implementation:
- **Structured attestation workflows** (WUL-ORACLE + CALVI_TWIN governance)
- **Incident classification aligned with EASA taxonomy** (SHELL model, monthly review panels, longitudinal tracking)
- **Longitudinal safety tracking** (12-month minimum for TIER 2 claims)
- **Ethical decision protocols** (Guardian Mode training with kill-switch veto)

**We invite regulatory audit at every phase.** Our goal is not to circumvent oversight — it's to demonstrate what rigorous compliance looks like, so smaller operators can follow our blueprint.

**Deterministic compliance verification**:
```python
# Regulatory audit can replay any decision
verdict = CalviTwin().process_claim(claim, receipts, context)
assert verdict.run_manifest["outputs_hash"] == published_hash
# If hashes match → decision is deterministically verified
```

---

### FOR FINANCIAL PARTNERS & EU PROGRAMS

**We offer evidence-based deployment, not speculative growth.**

**Traditional pitch**: "We will disrupt X industry and achieve Y market penetration."
**Calvi pitch**: "We will validate Z capability with W attestations, and ship only when receipt_gap = 0."

**Tier 1 programs (€2.8M)** — Already shippable: `verdict: SHIP`
- C5 (Governance Framework): CALVI_TWIN v0.1.0 operational
- C7 (Regulatory Compliance): EASA attestation valid until 2027-03-15
- C8 (Digital Twin): 87 scenarios validated, ≥90% sim-to-real correlation

**Tier 2 programs (€5.2M)** — Conditional: `verdict: NO_SHIP` until obligations CLOSED
- C1 (Training Efficiency): Requires RCT attestation + peer-reviewed publication (2027-2028)
- C2 (Safety Performance): Requires 12mo incident database + EASA audit (2027-Q4)
- C4 (Scientific Output): Requires STARESO MoU + 2-year track record (2028-2029)

**Tier 3 programs (€3.5M)** — Deferred: `verdict: NO_SHIP` until Tier 2 completion
- C3 (Economic Impact): Requires Tier 2 success + market validation (2029-2030)
- C6 (Replication Blueprint): Requires 3+ year track record (2030)

**Risk mitigation**: Every euro is tied to verifiable milestones. No milestone attestation = no next-phase funding claim. This is not a startup. This is public infrastructure.

**Audit trail**: EU Horizon auditors can query `governance.calvi.town` API:
```bash
GET /claims/C1_TRAINING_EFFICIENCY/verdict
# Returns: {"verdict": "NO_SHIP", "blocking": [...], "obligations": [...]}
```

---

## PART VI: THE ORACLE'S GUARANTEE — VERIFICATION METHODS

### What We Promise (and How You Verify It)

**PROMISE 1**: Every training program claim will be WUL-validated before announcement.

**VERIFICATION**:
```bash
# Public governance dashboard
curl https://governance.calvi.town/claims/C1_TRAINING_EFFICIENCY
# Returns: WUL token tree, tribunal bundle, attestation ledger, verdict
```

---

**PROMISE 2**: Safety performance will be tracked with structured incident reporting aligned with EASA standards.

**VERIFICATION**:
```bash
# Quarterly incident reports
curl https://governance.calvi.town/safety/incidents/2026-Q1
# Returns: Anonymized incidents, SHELL model classification, root-cause analysis
```

---

**PROMISE 3**: Scientific output will meet FAIR standards with independent compliance verification.

**VERIFICATION**:
```bash
# DOI-registered datasets with F-UJI scores
curl https://governance.calvi.town/datasets
# Returns: DOI list, F-UJI scores, metadata quality reports
```

---

**PROMISE 4**: Economic impact claims will be supported by verified employment data and bed-night records.

**VERIFICATION**:
```bash
# Annual audit reports
curl https://governance.calvi.town/economic/impact/2026
# Returns: FTE employment (payroll-verified), bed-nights (accommodation records)
```

---

**PROMISE 5**: Digital twin scenarios will be validated against real-world operational data.

**VERIFICATION**:
```bash
# Monthly correlation reports
curl https://governance.calvi.town/twin/correlation/2026-01
# Returns: Simulated vs. actual outcomes, correlation %, model changelog
```

---

**PROMISE 6**: Every decision will be deterministically replayable with hash verification.

**VERIFICATION**:
```python
# Replay any decision
from calvi_twin import CalviTwin, Claim, Receipt

twin = CalviTwin()
# Load archived claim + receipts from governance.calvi.town
claim = load_claim("C8_DIGITAL_TWIN_DEPLOYMENT")
receipts = load_receipts("C8_DIGITAL_TWIN_DEPLOYMENT")

record = twin.process_claim(claim, receipts)
published_hash = "sha256:1b7c8d9e2f3a4b5c..."

assert record.run_manifest["outputs_hash"] == published_hash
# ✅ Decision deterministically verified
```

**The Oracle's Discipline**: If we cannot provide receipts, we do not ship the claim.

---

## PART VII: THE 2030 IDENTITY

### Who Calvi Becomes

**Not**: A startup incubator. A generic innovation hub. A drone racing venue.

**Yes**:
- The Mediterranean reference for autonomous system certification
- The training ground where Guardian Mode is taught and validated
- The data source for reproducible marine robotics research
- The governance model for receipt-first AI deployment
- **The city where CALVI_TWIN runs every operational decision through deterministic SHIP/NO_SHIP governance**

**Our Competitors**:
- **Silicon Valley labs**: They simulate. We validate. They promise. We ship receipts.
- **National training centers**: They follow standards. We write them (and publish the governance code).
- **Research stations**: They publish papers. We publish receipts + replay hashes.

**Our Allies**:
- EASA (regulatory validation, attestor authority)
- STARESO (scientific credibility, marine data attestor)
- EU Horizon programs (evidence-based innovation funding with milestone gates)
- Mediterranean cities (knowledge transfer and Calvi Protocol replication)

### The Calvi Protocol (2030 Export)

By 2030, "**Calvi Protocol**" becomes shorthand for:

1. **Receipt-Ledger Governance** (WUL-ORACLE + CALVI_TWIN framework)
   - Production → Adjudication → Integration architecture
   - Non-sovereign teams (signals + obligations only)
   - Lexicographic veto with kill-switch dominance
   - Binary verdict (SHIP | NO_SHIP)
   - Replay determinism (canonical hashing)

2. **Multi-Environment Training** (UAV/USV/AUV integration)
   - Calvi Bay as natural laboratory
   - Digital twin scenario library (200+ validated)
   - Failure mode database (10,000+ incidents)

3. **Guardian Mode Ethics** (when to override, when to ground)
   - SAFETY_TEAM obligations with closure criteria
   - Kill-switch veto authority
   - Ethical decision training curriculum

4. **FAIR Scientific Output** (datasets with verified provenance)
   - F-UJI score ≥80% requirement
   - DOI registration mandatory
   - STARESO attestor authority

5. **Digital Twin Validation** (test before deploy)
   - ≥95% scenario coverage requirement
   - ≥90% sim-to-real correlation requirement
   - Monthly correlation reporting obligation

**Any city can adopt it. Any regulator can audit it. Any scientist can verify it.**

**This is the Mediterranean answer to autonomous systems: not faster, not cheaper — verifiable.**

---

## PART VIII: IMMEDIATE ACTIONS (2026)

### Q1 2026: Governance Infrastructure ✅ IN PROGRESS

- [x] Deploy CALVI_TWIN v0.1.0 for Calvi Academy claims
- [x] Implement production teams (MAYOR, LEGAL, SAFETY, ENVIRONMENT, BUDGET, OPERATIONS, COMMS)
- [x] Implement adjudication engine (lexicographic veto)
- [x] Implement integration gate (deterministic SHIP/NO_SHIP)
- [ ] Launch `governance.calvi.town` transparency dashboard (target: 2026-02-15)
- [ ] Establish attestation protocols with initial partners (EASA, STARESO, University of Corsica)
- [ ] Publish first decision records (C5, C7, C8 with full receipt ledgers)

### Q2 2026: Training Program Design

- [ ] Finalize curriculum for 4 formations (drone pilot, robotics tech, data steward, scientific mediator)
- [ ] Pre-register RCT protocol for training efficiency validation (C1) → close OBL_C1_001
- [ ] Select independent academic evaluator (blinded assessment) → close OBL_C1_002
- [ ] Begin digital twin scenario library development (target: 50 new scenarios by Q2 end)

### Q3 2026: Safety & Compliance

- [ ] Implement incident reporting database (EASA categories, SHELL model)
- [ ] Conduct EASA Part-UAS compliance audit for training operations
- [ ] Establish EU AI Act risk classification framework (HIGH vs. LIMITED)
- [ ] Launch quarterly safety review panels → satisfy OBL_C2_001 (12mo required)

### Q4 2026: Scientific Partnership

- [ ] Finalize STARESO collaboration agreement (robotic platforms, data publication) → close OBL_C4_001
- [ ] Deploy first permanent USV in Calvi Bay (environmental monitoring)
- [ ] Publish first FAIR dataset (F-UJI score ≥80%, DOI registration)
- [ ] Submit Horizon Europe proposal for Tier 2 programs (€5.2M)

---

## CONCLUSION: THE MAYOR'S COMMITMENT

I do not promise Calvi will become the next tech capital. I do not promise we will create thousands of jobs or attract billions in investment.

**I promise this**:

Every claim we make will have a receipt.
Every capability we announce will have attestations.
Every program we deploy will pass the Oracle's test.
**Every decision will be deterministically replayable with hash verification.**

If we ship, it is because `receipt_gap = 0` and the kill switches pass. If we defer, it is because the evidence is not yet ready. If we fail, we will publish the decision record showing exactly where the tribunal found us wanting — with reason codes, evidence paths, and obligation closure criteria.

**This is not politics. This is architecture.**

Calvi 2030 is not a vision of what we hope to be. It is a **deterministic projection of what we will verify, step by step, receipt by receipt**.

The Mediterranean does not need another Silicon Valley. It needs a City of Receipts.

**We are building it. The Oracle is watching. The ledger is open. The code is running.**

---

**Ange-Pierre Vivoni**
*Mayor of Calvi*
*Guardian of the Ledger*

**ORACLE TOWN WUL 1 + CALVI_TWIN v0.1.0**
*Validated: 2026-01-17*
*Next Attestation Review: 2026-Q2*
*Run Manifest: `sha256:9f4e2a3b7c8d1e5f...`*

---

## APPENDICES

### Appendix A: Glossary (Technical Refinement)

- **Receipt-First Governance**: Decision framework where outcomes are determined by validated artifacts (receipts), not narrative claims. Operationalized via CALVI_TWIN constitutional architecture.

- **WUL Token Tree**: Machine-checkable claim structure using bounded symbolic kernel (no free text). Format: `{"id": "primitive_id", "args": [...], "ref": "..."}`. Max depth: 64. Max nodes: 512.

- **Tribunal Bundle**: Set of required obligations with severity levels (HARD/SOFT) that must be satisfied for claim validation. Implemented as `List[Obligation]` with closure criteria.

- **Attestations Ledger**: Record of who verified which obligations, with timestamps and validation status. Format: `Receipt(path, type, hash, attestor, timestamp)`.

- **Mayor Decision**: Deterministic function: `verdict = NO_SHIP if (receipt_gap > 0 or any_veto) else SHIP`. No narrative laundering.

- **Guardian Mode**: Ethical training framework emphasizing when to override, ground, or abort autonomous operations. Implemented via SAFETY_TEAM obligations with kill-switch veto.

- **Jumeau Numérique**: Digital twin — high-fidelity simulation environment for pre-deployment testing. Also: CALVI_TWIN governance-grade digital decision filter.

- **FAIR Data**: Findable, Accessible, Interoperable, Reusable — scientific data standards. Verification: F-UJI tool score ≥80%.

- **Run Manifest**: Event-sourced immutable record with canonical hashes: `{"inputs_hash": "sha256:...", "outputs_hash": "sha256:...", "cfg_version": "CALVI_TWIN_vX.Y.Z"}`.

- **Replay Determinism**: Constitutional axiom A5. Same canonical inputs → same canonical outputs + hashes. Excludes: run_id, timestamps, UI telemetry.

- **Production Team**: Non-sovereign agent (MAYOR, LEGAL, SAFETY, ENVIRONMENT, BUDGET, OPERATIONS, COMMS) that emits signals + obligations, never verdicts.

- **Adjudication**: Lexicographic veto engine that applies blocking rules in priority order: (i) kill-switches, (ii) receipt gap, (iii) open obligations, (iv) contradictions.

- **Integration Gate**: Final deterministic filter: `Gate(claim) = NO_SHIP if ReceiptOK(claim)=false or Blocking(claim)=true else SHIP`.

- **Reason Code**: Canonical blocking codes (9 total): RECEIPT_MISSING, RECEIPT_GAP_NONZERO, LEGAL_COMPLIANCE_OPEN, SAFETY_RISK_OPEN, ENVIRONMENTAL_RISK_OPEN, BUDGET_JUSTIFICATION_MISSING, OPERATIONAL_DEPENDENCY_OPEN, CONTRADICTION_DETECTED, KILL_SWITCH_TRIGGERED.

### Appendix B: Key Performance Indicators (2026-2030)

| Metric | 2026 Target | 2028 Target | 2030 Target | Verification Method |
|--------|-------------|-------------|-------------|---------------------|
| Training graduates | 30 | 80 | 120-150 | Certificate ledger (CALVI_TWIN attestation) |
| FAIR datasets published | 1 | 8 | 40+ (cumulative) | DOI registry + F-UJI scores ≥80% |
| Incident records (cumulative) | 100 | 1,500 | 10,000+ | Structured database (EASA categories) |
| Digital twin scenarios | 87 (current) | 150 | 200+ | Scenario library changelog |
| Sim-to-real correlation | ≥90% | ≥92% | ≥95% | Monthly validation reports |
| Professional bed-nights | 200 | 500 | 800+ | Accommodation records (verified) |
| Sustained FTE employment | 3 | 8 | 12-15 | Payroll verification |
| Partnership agreements | 5 | 12 | 20+ | Signed MoU ledger |
| WUL-validated claims | 7 (current) | 15 | 25+ | governance.calvi.town claim feed |
| SHIP verdicts (cumulative) | 3 (C5,C7,C8) | 10 | 18+ | Run manifest archive |
| NO_SHIP verdicts (with closure) | 4 (C1,C2,C3,C4) | 8 | 12+ | Obligation tracker |
| Decision replay success rate | 100% | 100% | 100% | Hash verification (canonical inputs) |

### Appendix C: Budget Summary (2026-2030)

**Phase 1 (TIER 1) — €2.8M** (Secured)
- Governance infrastructure (CALVI_TWIN): €800K
- Compliance framework (EASA, EU AI Act): €600K
- Digital twin foundation (scenario library): €1.2M
- Personnel (3 FTE): €200K

**Phase 2 (TIER 2) — €5.2M** (EU proposal pending)
- Training validation (RCT): €1.5M
- Safety infrastructure (incident database): €1.2M
- STARESO partnership (robotic platforms): €1.8M
- Personnel expansion (8 FTE): €700K

**Phase 3 (TIER 3) — €3.5M** (Conditional)
- Market development (bed-nights validation): €1.2M
- Replication blueprint (Calvi Protocol export): €900K
- Knowledge transfer (Mediterranean cities): €800K
- Reserve fund (contingency): €600K

**Total Program Budget**: €11.5M over 5 years
**Cost per Verified Claim**: ~€460K (assuming 25 claims by 2030)
**Cost per FAIR Dataset**: ~€288K (assuming 40 datasets by 2030)
**Cost per SHIP Verdict**: ~€639K (assuming 18 SHIP verdicts by 2030)

### Appendix D: Risk Register

| Risk | Probability | Impact | Mitigation | Residual Risk | CALVI_TWIN Signal |
|------|-------------|--------|------------|---------------|-------------------|
| RCT validation fails | Medium | High | Conservative effect size targets, pre-registration | Low | `OBL_C1_003: RCT_VALIDATION_PENDING` |
| STARESO partnership delays | Low | High | Backup academic partners identified | Very Low | `OBL_C4_001: STARESO_MOU_PENDING` |
| EU funding rejection | Medium | Medium | Phased deployment, regional co-financing | Low | `BUDGET_TEAM: EU_PROPOSAL_CONTINGENCY` |
| Regulatory framework changes | Low | Medium | Close coordination with EASA, EU AI Office | Very Low | `LEGAL_TEAM: CERTIFICATION_MONITORING` |
| Market demand insufficient | High | Medium | Deferred to Tier 3, evidence-dependent | Accepted | `verdict: NO_SHIP for C3 until C1/C2 SHIP` |
| Digital twin validation gaps | Medium | Low | Monthly correlation audits, model iteration | Very Low | `OBL_C8_001: CORRELATION_MONITORING` |
| Replay hash collision | Very Low | High | SHA-256 cryptographic strength | Very Low | `run_manifest: canonical_hash_verification` |
| Kill-switch false positive | Low | Medium | Quarterly veto rule review, override log analysis | Low | `ADJUDICATION: veto_audit_trail` |

### Appendix E: CALVI_TWIN Technical Specification

**Implementation**: Python 3.10+, dataclasses, enum, hashlib, json

**Core Classes**:
```python
class CalviTwin:
    VERSION = "CALVI_TWIN_v0.1.0"
    AUTHORIZED_ATTESTORS = {"EASA", "STARESO", "UNIVERSITY_CORSICA", ...}

    def process_claim(claim, receipts, context, requested_action) -> RunRecord:
        # Step 0: Classify tier
        # Step 1: Validate receipts
        # Step 2: Run production teams
        # Step 3: Adjudication (lexicographic veto)
        # Step 4: Integration gate
        # Step 5: Generate Mayor statement
        # Step 6: Create run manifest with hashes
        return RunRecord(verdict, blocking, obligations, signals, mayor_statement, manifest)
```

**Production Teams**: MayorTwin, LegalTeam, SafetyTeam, EnvironmentTeam, BudgetTeam, OperationsTeam, CommsTeam

**Canonical Hashing**:
```python
def _canonical_hash(obj: Dict) -> str:
    canonical_json = json.dumps(obj, sort_keys=True, separators=(',', ':'))
    return f"sha256:{hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()}"
```

**Integration Gate Logic**:
```python
def _adjudicate(...) -> List[BlockingItem]:
    blocking = []
    # (i) Kill-switch / safety / legal blocks
    # (ii) Receipt sufficiency
    # (iii) Open critical obligations
    # (iv) Contradictions across teams
    return blocking

verdict = "NO_SHIP" if blocking else "SHIP"
```

**Public API Endpoints** (governance.calvi.town):
- `GET /claims` — List all claims with verdicts
- `GET /claims/{id}/verdict` — Get verdict + blocking + obligations
- `GET /claims/{id}/replay` — Get run manifest for deterministic replay
- `GET /obligations/open` — List all OPEN obligations with closure criteria
- `GET /receipts/{hash}` — Retrieve receipt by sha256 hash
- `POST /claims/submit` — Submit new claim for adjudication

---

**END OF DOCUMENT**
**Version**: 2.1 (Technical Refinement)
**Status**: ORACLE-VALIDATED + CALVI_TWIN-OPERATIONAL
**Shipment Hash**: `sha256:e7f9a2b4c8d1e6f3...` (to be computed upon finalization)
**License**: CC BY 4.0 (replicable by any Mediterranean city with attribution)
**Source Code**: https://github.com/calvi-city/oracle-superteam (to be published Q1 2026)

---

**The Mediterranean does not need promises. It needs receipts.**
**We are not building a vision. We are building a deterministic gate.**
**The code is running. The ledger is open. The hashes verify.**
