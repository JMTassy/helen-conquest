# UI Integration Specification

## Purpose

This document defines how the MVP wireframe UI integrates with the constitutional-grade governance backend (schemas, reason codes, Mayor decision system).

---

## Architecture Decision

The UI implements the **constitutional governance system** defined in:
- `schemas/decision_record.schema.json` (2020-12, schema-enforced invariants)
- `reason_codes.json` (30 canonical codes)
- `DECISION_RECORD_DETERMINISM.md` (hashed vs non-hashed split)
- `REASON_CODES.md` (single source of truth)

**Not** the legacy `oracle/engine.py` system (different architecture, pre-constitution).

---

## Backend API Contract

### Artifact Storage API

**GET /api/runs/:run_id/artifacts/:path**
- Returns artifact blob (JSON or binary)
- Response headers include `X-SHA256-Hash` for verification

**GET /api/runs/:run_id/index**
- Returns `run_index.json` with:
```json
{
  "run_id": "uuid::...",
  "claim_id": "claim::...",
  "eq_pins": {
    "inputs_hash": "<64-hex>",
    "config_hash": "<64-hex>",
    "kernel_hash": "<64-hex>",
    "canon_impl_id": "rfc8785:v1"
  },
  "stages": [
    {
      "name": "S0_Concierge",
      "status": "COMPLETED",
      "artifacts": [
        {"path": "briefcase.json", "sha256": "...", "size": 1234}
      ]
    },
    {
      "name": "S5_Mayor",
      "status": "COMPLETED",
      "artifacts": [
        {"path": "decision_record.json", "sha256": "..."},
        {"path": "decision_record.meta.json", "sha256": "..."}
      ]
    }
  ],
  "summary": {
    "receipt_gap": 0,
    "kill_switches_pass": true,
    "decision": "SHIP"
  }
}
```

**POST /api/runs/:run_id/artifacts/:path**
- Upload artifact
- Validates schema if known artifact type
- Returns computed sha256

---

### Schema Validation API

**POST /api/validate/decision_record**
```json
{
  "artifact": { /* decision_record.json payload */ }
}
```

Response:
```json
{
  "valid": true | false,
  "errors": [
    {"gate": "schema", "code": "SCHEMA_VALIDATION_FAILED", "detail": "..."},
    {"gate": "allowlist", "code": "REASON_CODE_NOT_IN_ALLOWLIST", "detail": "..."},
    {"gate": "purity", "code": "PURITY_VIOLATION", "detail": "..."}
  ]
}
```

Three gates (matching test suite):
1. **Schema validation** — JSON Schema 2020-12 with `allOf` invariants
2. **Reason code allowlist** — All `blocking[].code` in `reason_codes.json`
3. **Purity check** — Recompute decision from hashed inputs, must match

---

### Receipt Gap Computation API

**GET /api/runs/:run_id/receipt_gap**

Computes from:
- `tribunal_bundle.json` (obligations list)
- `attestations_ledger.json` (satisfaction records)

Response:
```json
{
  "receipt_gap": 3,
  "missing_obligations": [
    {
      "name": "security_audit",
      "severity": "HARD",
      "expected_attestor": "team_security",
      "reason_code": "HARD_OBLIGATION_UNSATISFIED",
      "detail": "No valid attestation found"
    }
  ]
}
```

---

### Mayor Decision Computation API

**POST /api/runs/:run_id/compute_decision**

Request:
```json
{
  "mode": "recompute" | "upload",
  "payload": { /* decision_record.json if mode=upload */ }
}
```

If mode=recompute, backend:
1. Loads `tribunal_bundle.json`, `policies_eval.json`, `receipt_root_payload.json`
2. Computes hashes of each
3. Applies Mayor decision function:
   ```
   decision = SHIP iff (kill_switches_pass == true AND receipt_gap == 0)
   ```
4. Returns `decision_record.json`

If mode=upload, validates three gates (schema, allowlist, purity).

---

## Frontend State Model

### Global State (Redux/Context)

```typescript
interface AppState {
  // Authentication
  currentUser: {
    role: 'Concierge' | 'Superteam' | 'Factory' | 'Mayor' | 'Public'
  }

  // Registries (loaded at app start)
  reasonCodes: ReasonCode[]
  schemas: Record<string, JSONSchema>

  // Current run context
  currentRun: RunState | null
}

interface RunState {
  run_id: string
  claim_id: string
  eq_pins: EquivalencePins
  stages: StageState[]
  summary: RunSummary
}

interface StageState {
  name: string
  status: 'NOT_STARTED' | 'RUNNING' | 'COMPLETED' | 'FAILED'
  artifacts: ArtifactRecord[]
  reason_codes?: ReasonCodeRef[]  // if FAILED
}

interface RunSummary {
  receipt_gap: number
  kill_switches_pass: boolean
  decision: 'SHIP' | 'NO_SHIP' | 'PENDING'
  stage: string  // latest completed stage name
}
```

---

## Component Architecture

### Core Components

**RunsListView**
- Fetches `/api/runs` (paginated, filtered)
- Table columns: Run ID, Claim ID, Stage, Receipt Gap, Kill Switches, Decision, Updated
- Filter chips: Needs Mayor, Receipt gap > 0, Policy failed, Published

**RunDetailView**
- Fetches `/api/runs/:run_id/index`
- Top bar: Receipt Gap KPI, Missing obligations count, Kill switches, Decision
- Timeline: Stage cards with artifacts + hashes
- Tabs: Overview, Briefcase, Obligations, Tests, Attestations, Policies, Artifacts, Mayor

**BriefcaseBuilderWizard**
- Multi-step form (5 steps)
- Step 1: Pins & determinism
- Step 2: Required obligations (structured editor)
- Step 3: Requested tests (map to obligations)
- Step 4: Kill-switch policies (select from registry)
- Step 5: Route teams (toggles)
- Final: Freeze & Dispatch (one-way door)

**AttestationLedgerViewer**
- Fetches `/api/runs/:run_id/artifacts/attestations_ledger.json`
- Computes receipt gap locally or via API
- Table: obligation_name, severity, expected_attestor, actual_attestor, attestation_valid, policy_match, payload_hash, fingerprint
- Derived panels: Receipt Gap, Missing obligations list

**MayorDecisionPanel** (role-gated)
- Inputs panel (read-only hashes)
- Compute Decision: Trigger CI job OR Upload decision_record.json
- Three-gate validation (schema, allowlist, purity)
- Publish button (only enabled if all gates pass)

---

## UX Implementation Guardrails

### 1. Freeze is One-Way Door

```typescript
// BriefcaseBuilder.tsx
const handleFreeze = async () => {
  if (briefcase.frozen) {
    throw new Error('Cannot freeze: already frozen')
  }

  const briefcase_hash = await computeHash(briefcase)
  await api.post(`/api/briefcases/${briefcase.id}/freeze`, { briefcase_hash })

  // Disable all edit controls
  setEditMode(false)

  // Show immutable badge
  setFrozen(true)
}

// After freeze: all input fields disabled, only Fork Run button enabled
```

### 2. Payload vs Meta Visual Separation

```typescript
// ArtifactBadge.tsx
const ArtifactBadge = ({ artifact }) => {
  const isHashed = HASHED_ARTIFACTS.includes(artifact.path)

  return (
    <Badge color={isHashed ? 'blue' : 'gray'}>
      {isHashed ? 'Receipt-hashed payload' : 'Non-hashed meta'}
    </Badge>
  )
}

// Constants
const HASHED_ARTIFACTS = [
  'briefcase.json',
  'decision_record.json',
  'tribunal_bundle.json',
  'receipt_root_payload.json'
]
```

### 3. Reason Code Selection

```typescript
// ReasonCodeDropdown.tsx
const ReasonCodeDropdown = ({ value, onChange }) => {
  const { reasonCodes } = useAppState()

  return (
    <Select value={value} onChange={onChange}>
      {reasonCodes.map(code => (
        <Option key={code} value={code}>
          {code}
        </Option>
      ))}
    </Select>
  )
}

// Load reason codes at app start
const loadReasonCodes = async () => {
  const resp = await fetch('/api/registries/reason_codes')
  return resp.json()  // reason_codes.json
}
```

### 4. Decision Surfaces are Role-Exclusive

```typescript
// MayorTab.tsx
const MayorTab = () => {
  const { currentUser } = useAuth()

  // Do not render at all if not Mayor (not just disabled)
  if (currentUser.role !== 'Mayor') {
    return null
  }

  return <MayorDecisionPanel />
}
```

### 5. Receipt Gap is Primary KPI

```typescript
// RunDetailTopBar.tsx
const RunDetailTopBar = ({ run }) => {
  const handleReceiptGapClick = () => {
    // Navigate to Missing Obligations list
    navigate(`/runs/${run.run_id}#missing-obligations`)
  }

  return (
    <TopBar>
      <KPI
        label="Receipt Gap"
        value={run.summary.receipt_gap}
        onClick={handleReceiptGapClick}
        color={run.summary.receipt_gap > 0 ? 'red' : 'green'}
        size="large"
      />
      {/* ... other KPIs ... */}
    </TopBar>
  )
}
```

---

## Schema Integration Points

### 1. Validation at Upload

```typescript
// api.ts
const uploadArtifact = async (run_id: string, path: string, payload: any) => {
  const schema = getSchemaForPath(path)

  if (schema) {
    // Client-side pre-validation
    const errors = validateAgainstSchema(payload, schema)
    if (errors.length > 0) {
      throw new ValidationError(errors)
    }
  }

  // Server-side validation (canonical)
  const resp = await fetch(`/api/runs/${run_id}/artifacts/${path}`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })

  if (!resp.ok) {
    const errors = await resp.json()
    throw new ValidationError(errors)
  }

  return resp.json()
}

const getSchemaForPath = (path: string): JSONSchema | null => {
  const schemaMap: Record<string, string> = {
    'decision_record.json': 'decision_record.schema.json',
    'briefcase.json': 'briefcase.schema.json',
    'tribunal_bundle.json': 'tribunal_bundle.schema.json'
  }

  const schemaName = schemaMap[path]
  return schemaName ? schemas[schemaName] : null
}
```

### 2. Three-Gate Validation Display

```typescript
// MayorDecisionPanel.tsx
const validateDecision = async (decision_record: any) => {
  const resp = await api.post('/api/validate/decision_record', {
    artifact: decision_record
  })

  return resp.json()  // { valid, errors }
}

const GatesDisplay = ({ validationResult }) => {
  const gates = [
    { name: 'Schema', icon: '📋' },
    { name: 'Allowlist', icon: '📜' },
    { name: 'Purity', icon: '🔐' }
  ]

  return (
    <Stack>
      {gates.map(gate => {
        const gateErrors = validationResult.errors.filter(e => e.gate === gate.name.toLowerCase())
        const passed = gateErrors.length === 0

        return (
          <GateCard key={gate.name} passed={passed}>
            <Icon>{gate.icon}</Icon>
            <Label>{gate.name}</Label>
            {!passed && (
              <ErrorList>
                {gateErrors.map(err => (
                  <ErrorItem key={err.code}>
                    <Code>{err.code}</Code>
                    <Detail>{err.detail}</Detail>
                  </ErrorItem>
                ))}
              </ErrorList>
            )}
          </GateCard>
        )
      })}
    </Stack>
  )
}
```

---

## Hash Verification

All artifact displays must show hash verification:

```typescript
// ArtifactCard.tsx
const ArtifactCard = ({ artifact, run_id }) => {
  const [verified, setVerified] = useState<boolean | null>(null)

  useEffect(() => {
    const verify = async () => {
      const blob = await api.getArtifact(run_id, artifact.path)
      const computed = await computeSHA256(blob)
      setVerified(computed === artifact.sha256)
    }
    verify()
  }, [artifact, run_id])

  return (
    <Card>
      <FileName>{artifact.path}</FileName>
      <Hash>
        {artifact.sha256}
        <CopyButton value={artifact.sha256} />
      </Hash>
      {verified !== null && (
        <VerificationBadge verified={verified}>
          {verified ? '✓ Hash verified' : '✗ Hash mismatch'}
        </VerificationBadge>
      )}
    </Card>
  )
}
```

---

## MVP Acceptance Criteria Implementation Checklist

### ✅ Concierge can create/freeze briefcase and dispatch run
- [ ] BriefcaseBuilderWizard component (5 steps)
- [ ] POST `/api/briefcases` endpoint
- [ ] POST `/api/briefcases/:id/freeze` endpoint (one-way door)
- [ ] POST `/api/runs` endpoint (dispatch)

### ✅ Team packets can be uploaded and appear in Merger view
- [ ] POST `/api/runs/:run_id/artifacts/team_packets/:team_id.json`
- [ ] MergerView component with diff display
- [ ] Reason code dropdown for diffs

### ✅ Factory artifacts can be attached and rendered as stage cards
- [ ] POST `/api/runs/:run_id/artifacts/:path` (generic upload)
- [ ] StageCard component with status badge + artifacts list
- [ ] Timeline layout in RunDetailView

### ✅ Receipt Gap computed and displayed consistently
- [ ] GET `/api/runs/:run_id/receipt_gap` endpoint
- [ ] AttestationLedgerViewer component
- [ ] Receipt Gap KPI in RunDetailTopBar
- [ ] Missing obligations list with reason codes

### ✅ Mayor can upload/compute decision with three-gate validation
- [ ] POST `/api/runs/:run_id/compute_decision` endpoint
- [ ] MayorDecisionPanel component (role-gated)
- [ ] Three-gate validation: schema, allowlist, purity
- [ ] GatesDisplay component showing pass/fail per gate

### ✅ Publish emits public page
- [ ] POST `/api/runs/:run_id/publish` endpoint
- [ ] PublicPage component (`/public/:claim_id`)
- [ ] Read-only artifact snapshot
- [ ] Hash pointers + timestamp (labeled non-deterministic)

---

## Next Increment: Run Diff View

**Route:** `/runs/compare?a=:run_id_a&b=:run_id_b`

**Purpose:** Compare two runs with same claim_id, highlight pin changes vs receipt changes

**Implementation:**
```typescript
const RunDiffView = ({ run_a, run_b }) => {
  const pinDiffs = computePinDiffs(run_a.eq_pins, run_b.eq_pins)
  const receiptDiffs = computeReceiptDiffs(
    run_a.summary.receipt_gap,
    run_b.summary.receipt_gap
  )

  return (
    <Layout>
      <Section title="Pin Differences">
        {pinDiffs.length === 0 ? (
          <Badge color="green">Replay-equivalent</Badge>
        ) : (
          <DiffList items={pinDiffs} />
        )}
      </Section>

      <Section title="Receipt Gap Changes">
        <Metric>
          {run_a.summary.receipt_gap} → {run_b.summary.receipt_gap}
        </Metric>
        {receiptDiffs.map(diff => (
          <DiffCard key={diff.obligation}>
            <Obligation>{diff.obligation}</Obligation>
            <Change>{diff.change}</Change>
          </DiffCard>
        ))}
      </Section>
    </Layout>
  )
}
```

This prevents "stealth changes" by making pin drifts vs genuine progress immediately visible.

---

**END OF UI_INTEGRATION_SPEC.md**
