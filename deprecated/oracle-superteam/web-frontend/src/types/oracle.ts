// web-frontend/src/types/oracle.ts
/**
 * ORACLE SUPERTEAM — TypeScript Type Definitions
 *
 * Frontend type definitions for the ORACLE SUPERTEAM governance framework.
 */

export type VerdictState = 'SHIP' | 'NO_SHIP';
export type InternalState = 'ACCEPT' | 'QUARANTINE' | 'KILL';
export type ClaimTier = 'Tier I' | 'Tier II' | 'Tier III';
export type SignalType = 'OBLIGATION_OPEN' | 'RISK_FLAG' | 'EVIDENCE_WEAK' | 'KILL_REQUEST';
export type ObligationType =
  | 'METRICS_INSUFFICIENT'
  | 'LEGAL_COMPLIANCE'
  | 'SECURITY_THREAT'
  | 'EVIDENCE_MISSING'
  | 'CONTRADICTION_DETECTED';

export enum TeamType {
  LEGAL = 'Legal Office',
  SECURITY = 'Security Sector',
  ENGINEERING = 'Engineering Wing',
  DATA_VALIDATION = 'Data Validation Office',
  COO = 'COO HQ',
  UX_IMPACT = 'UX/Impact Bureau',
  STRATEGY = 'Strategy HQ'
}

export interface Claim {
  id: string;
  assertion: string;
  tier: ClaimTier;
  domain: string[];
  owner_team: string;
  requires_receipts: boolean;
  timestamp?: string;
}

export interface Evidence {
  id: string;
  type: string;
  tags: string[];
  hash?: string;
  issuer?: string;
  content?: string;
}

export interface Signal {
  team: TeamType;
  signal_type: SignalType;
  obligation_type?: ObligationType;
  rationale: string;
  timestamp?: string;
}

export interface Obligation {
  type: ObligationType;
  owner_team: string;
  closure_criteria: string;
  status: 'OPEN' | 'RESOLVED' | 'INVALIDATED';
  opened_by?: string;
  verifiable_credential?: VerifiableCredential;
}

export interface Contradiction {
  rule_id: string;
  triggered_on: string[];
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface QIResult {
  A_c: {
    re: number;
    im: number;
  };
  S_c: number;
}

export interface Verdict {
  final: VerdictState;
  ship_permitted: boolean;
  reason_codes: string[];
  internal_state?: InternalState;
}

export interface RunManifest {
  run_id: string;
  timestamp_start: string;
  timestamp_end: string;
  code_version: string;
  claim: Claim;
  evidence: Evidence[];
  signals: Signal[];
  derived: {
    kill_switch_triggered: boolean;
    rule_kill_triggered: boolean;
    kill_switch_by: string[];
    contradictions: Contradiction[];
    obligations_open: Obligation[];
    obligations_closed: Obligation[];
    qi_int: QIResult;
  };
  decision: Verdict;
  event_log: Array<{
    event: string;
    value?: any;
  }>;
  hashes: {
    inputs_hash: string;
    outputs_hash: string;
  };
}

// Verifiable Credentials for Obligations
export interface VerifiableCredential {
  '@context': string[];
  type: string[];
  issuer: string;
  issuanceDate: string;
  credentialSubject: {
    id: string;
    obligationType: ObligationType;
    claimId: string;
    satisfactionProof: string;
    evidence: {
      type: string;
      hash: string;
      timestamp: string;
    }[];
  };
  proof: {
    type: string;
    created: string;
    proofPurpose: string;
    verificationMethod: string;
    jws: string;
  };
}

// API Key Management
export interface ApiKeyConfig {
  key: string;
  provider: 'gemini' | 'openai' | 'anthropic';
  encrypted: boolean;
  created_at: string;
  last_used?: string;
}

// Filtering Options
export interface ClaimFilter {
  decision?: VerdictState;
  dateRange?: {
    start: string;
    end: string;
  };
  searchQuery?: string;
  tier?: ClaimTier;
  domain?: string[];
  team?: TeamType;
}

export interface SortOption {
  field: 'timestamp' | 'tier' | 'decision' | 'score';
  direction: 'asc' | 'desc';
}

// Domain Inference
export interface DomainKeywords {
  domain: string;
  keywords: string[];
  weight: number;
}

export interface InferredDomain {
  domain: string;
  confidence: number;
  matched_keywords: string[];
}
