/**
 * coupling_gate.ts
 *
 * Deterministic, pure CouplingGate reference implementation (v1).
 * Enforces the coupling contract between Oracle Town (forecast admission)
 * and POC Factory (capability certification).
 *
 * No side effects. No interpretive layer. Artifacts only.
 */

// ============================================================================
// TYPE DEFINITIONS (Artifact-driven)
// ============================================================================

export type Gate = "COUPLED_OK" | "COUPLED_HOLD" | "COUPLED_FAIL";

export type Reason =
  | "HASH_MISMATCH_RUN"
  | "HASH_MISMATCH_KERNEL_OR_CONFIG"
  | "ORACLE_HOLD"
  | "NO_CAPABILITY"
  | "POC_NOT_GRADUATED"
  | "MISSING_SUPPORT_RECEIPT"
  | "INVALID_SUPPORT_RECEIPT"
  | "FORECAST_REJECTED"
  | "NON_ACTIONABLE"
  | "CAPABILITY_SUPPORTS_FORECAST";

/**
 * Oracle Town verdict record.
 * Represents the result of OT_θ(P, r) decision procedure.
 */
export type OracleVerdict = {
  verdict: "PUBLISH" | "HOLD" | "REJECT";
  run_hash: string;
  theta_hash: string;
  actionable: boolean;
  proposal_hash?: string; // Required when actionable
};

/**
 * POC Factory verdict record.
 * Represents the result of PF_θ(C, r) decision procedure.
 */
export type PocVerdict = {
  verdict: "GRADUATED" | "REWORK" | "REJECT" | "NONE";
  run_hash: string;
  theta_hash: string;
  capability_hash?: string; // Required when GRADUATED
};

/**
 * Support receipt artifact.
 * Cryptographic witness that binds forecast to capability.
 * In production: valid = result of Verify(S) signature check.
 * In CI vectors: valid = boolean stub.
 */
export type SupportReceipt = {
  valid: boolean;
  binds: {
    run_hash: string;
    theta_hash: string;
    proposal_hash: string;
    capability_hash: string;
  };
};

/**
 * CouplingGate output.
 * Includes gate verdict and deterministic reason codes.
 */
export type GateResult = { gate: Gate; reasons: Reason[] };

// ============================================================================
// COUPLING GATE FUNCTION (Pure Deterministic)
// ============================================================================

/**
 * CouplingGate(V_F, V_C, S, θ) → {COUPLED_OK, COUPLED_HOLD, COUPLED_FAIL}
 *
 * Total deterministic function that enforces the coupling law:
 * - No publish without capability (unless non-actionable)
 * - No graduation without governance receipts
 *
 * Reason codes follow strict priority order (first failing rule wins).
 */
export function couplingGateV1(args: {
  oracle: OracleVerdict;
  poc: PocVerdict;
  support_receipt?: SupportReceipt | null;
}): GateResult {
  const { oracle, poc, support_receipt } = args;

  // ========================================================================
  // PRIORITY 1: Hash Joins (Deterministic Artifacts)
  // ========================================================================

  // Run hash mismatch → FAIL (no computation proceeds with mismatched run)
  if (oracle.run_hash !== poc.run_hash) {
    return { gate: "COUPLED_FAIL", reasons: ["HASH_MISMATCH_RUN"] };
  }

  // Config/kernel hash mismatch → FAIL (thresholds and invariants must align)
  if (oracle.theta_hash !== poc.theta_hash) {
    return { gate: "COUPLED_FAIL", reasons: ["HASH_MISMATCH_KERNEL_OR_CONFIG"] };
  }

  // ========================================================================
  // PRIORITY 2: Oracle Verdict Dominates
  // ========================================================================

  // Oracle HOLD state propagates hold (conservative)
  if (oracle.verdict === "HOLD") {
    return { gate: "COUPLED_HOLD", reasons: ["ORACLE_HOLD"] };
  }

  // ========================================================================
  // PRIORITY 3: Oracle PUBLISH Cases (Core Coupling Law)
  // ========================================================================

  if (oracle.verdict === "PUBLISH") {
    // Non-actionable forecasts (observational) can publish without capability
    if (!oracle.actionable) {
      return { gate: "COUPLED_OK", reasons: ["NON_ACTIONABLE"] };
    }

    // Actionable forecasts REQUIRE:
    // (a) A graduated POC capability
    // (b) A valid receipt binding the exact hashes

    // Case 1: No graduated capability available
    if (poc.verdict !== "GRADUATED") {
      if (poc.verdict === "NONE") {
        return { gate: "COUPLED_HOLD", reasons: ["NO_CAPABILITY"] };
      }
      // POC exists but not graduated (REWORK or REJECT state)
      return { gate: "COUPLED_HOLD", reasons: ["POC_NOT_GRADUATED"] };
    }

    // Case 2: Graduated POC exists; now check support receipt
    if (!support_receipt) {
      return { gate: "COUPLED_HOLD", reasons: ["MISSING_SUPPORT_RECEIPT"] };
    }

    // Case 3: Receipt exists; verify it binds the exact hashes
    const proposal_hash = oracle.proposal_hash ?? "";
    const capability_hash = poc.capability_hash ?? "";

    const binds = support_receipt.binds;
    const bindsMatch =
      binds.run_hash === oracle.run_hash &&
      binds.theta_hash === oracle.theta_hash &&
      binds.proposal_hash === proposal_hash &&
      binds.capability_hash === capability_hash;

    if (!support_receipt.valid || !bindsMatch) {
      return { gate: "COUPLED_HOLD", reasons: ["INVALID_SUPPORT_RECEIPT"] };
    }

    // All checks passed: forecast is supported by capability
    return { gate: "COUPLED_OK", reasons: ["CAPABILITY_SUPPORTS_FORECAST"] };
  }

  // ========================================================================
  // PRIORITY 4: Oracle REJECT + POC GRADUATED → Governance Conflict
  // ========================================================================
  // (Coupling law: no graduation without forecast-grade receipts)

  if (oracle.verdict === "REJECT" && poc.verdict === "GRADUATED") {
    // Conservative: treat as HOLD (POC tried to promote despite forecast rejection)
    return { gate: "COUPLED_HOLD", reasons: ["FORECAST_REJECTED"] };
  }

  // ========================================================================
  // DEFAULT: OK (No coupling constraints violated)
  // ========================================================================

  return { gate: "COUPLED_OK", reasons: [] };
}

// ============================================================================
// EXPORT (for use in conformance runner)
// ============================================================================

export default couplingGateV1;
