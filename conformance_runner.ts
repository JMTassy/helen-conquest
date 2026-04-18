/**
 * conformance_runner.ts
 *
 * CI test harness for CouplingGate conformance vectors.
 * Reads vectors.json, runs each test case, reports failures.
 *
 * Usage:
 *   npx tsx conformance_runner.ts vectors.json
 *
 * Exit code 0 = all pass, 1 = any fail.
 */

import { readFileSync } from "node:fs";
import { couplingGateV1, type GateResult } from "./coupling_gate";

// ============================================================================
// TYPE DEFINITIONS (Conformance Vector Format)
// ============================================================================

/**
 * A conformance test vector.
 * Tests both single-POC and multi-POC resolution policies.
 */
type Vector = {
  name: string;
  oracle: any;
  poc?: any; // Single POC (most tests)
  pocs?: any[]; // Multiple POCs (multi-POC selection tests)
  support_receipt?: any | null;
  support_receipts?: any[]; // Multiple receipts for multi-POC
  expected: GateResult;
};

// ============================================================================
// UTILITIES
// ============================================================================

/**
 * Deep equality check (JSON stringify comparison).
 * Sufficient for flat verdict records.
 */
function assertEqual(actual: unknown, expected: unknown, msg: string): void {
  const a = JSON.stringify(actual);
  const e = JSON.stringify(expected);
  if (a !== e) {
    throw new Error(`${msg}\nEXPECTED: ${e}\nACTUAL:   ${a}`);
  }
}

/**
 * Multi-POC resolution policy.
 * POLICY: first_satisfying_support_receipt
 *
 * If vector has multiple POCs:
 *   1. Find the first GRADUATED POC
 *   2. That has a matching valid receipt binding its hashes
 *   3. Use that (poc, receipt) pair
 *
 * If no satisfying pair found:
 *   - Fall back to first POC, no receipt
 */
function resolveMulti(vector: Vector): { poc: any; receipt: any | null } {
  if (!vector.pocs) {
    // Single-POC case (most tests)
    return { poc: vector.poc, receipt: vector.support_receipt ?? null };
  }

  const oracle = vector.oracle;
  const pocs = vector.pocs;
  const receipts = vector.support_receipts ?? [];

  // Scan for a satisfying (poc, receipt) pair
  for (const p of pocs) {
    if (p.verdict !== "GRADUATED") continue; // Skip non-graduated

    for (const r of receipts) {
      if (!r?.valid) continue; // Skip invalid receipts

      const binds = r.binds;
      // Check if receipt binds the oracle's proposal and this POC's capability
      if (
        binds.run_hash === oracle.run_hash &&
        binds.theta_hash === oracle.theta_hash &&
        binds.proposal_hash === oracle.proposal_hash &&
        binds.capability_hash === p.capability_hash
      ) {
        // Found a satisfying pair
        return { poc: p, receipt: r };
      }
    }
  }

  // No satisfying pair found; fall back to first POC, no receipt
  return { poc: pocs[0], receipt: null };
}

// ============================================================================
// MAIN TEST RUNNER
// ============================================================================

function main(): void {
  // Get vectors file from command-line args
  const path = process.argv[2];
  if (!path) {
    console.error("Usage: npx tsx conformance_runner.ts <vectors.json>");
    process.exit(2);
  }

  // Load vectors
  let vectors: Vector[];
  try {
    const raw = readFileSync(path, "utf8");
    vectors = JSON.parse(raw);
  } catch (e: any) {
    console.error(`Failed to load vectors: ${e.message}`);
    process.exit(2);
  }

  if (!Array.isArray(vectors)) {
    console.error("Vectors file must contain a JSON array");
    process.exit(2);
  }

  console.log(
    `\nRunning ${vectors.length} conformance test vector${vectors.length === 1 ? "" : "s"}...\n`
  );

  let passed = 0;
  let failed = 0;

  for (const v of vectors) {
    try {
      // Resolve multi-POC case if needed
      const { poc, receipt } = resolveMulti(v);

      // Run CouplingGate
      const actual = couplingGateV1({
        oracle: v.oracle,
        poc,
        support_receipt: receipt,
      });

      // Check against expected
      assertEqual(actual, v.expected, `FAIL: ${v.name}`);

      console.log(`✅ PASS: ${v.name}`);
      passed++;
    } catch (e: any) {
      console.error(`❌ FAIL: ${e.message}\n`);
      failed++;
    }
  }

  // Summary
  console.log(
    `\n${"=".repeat(70)}`
  );
  console.log(`Tests: ${passed} passed, ${failed} failed out of ${vectors.length} total`);
  console.log(`${"=".repeat(70)}\n`);

  // Exit code
  process.exit(failed > 0 ? 1 : 0);
}

// Run
main();
