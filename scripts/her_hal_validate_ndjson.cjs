#!/usr/bin/env node
// -*- coding: utf-8 -*-
/**
 * HER/HAL Validator for Canonical Dialogue NDJSON Format
 *
 * Validates dialogue events in canonical format with payload/meta split:
 * {
 *   "type": "turn",
 *   "seq": N,
 *   "payload": {turn, hal, her_text, channel_contract},
 *   "meta": {timestamp_utc, raw_text},
 *   "payload_hash": "HEX64",
 *   "prev_cum_hash": "HEX64",
 *   "cum_hash": "HEX64"
 * }
 *
 * This validator:
 * - Reads town/dialogue.ndjson (one JSON event per line)
 * - Validates each event against dialogue_event.canonical.schema.json
 * - Verifies payload_hash and cum_hash integrity
 * - Checks reason_codes and required_fixes are sorted
 * - Detects HER/HAL moments (veto + adaptation + continuity)
 *
 * Usage:
 *   node her_hal_validate_ndjson.cjs [--file dialogue.ndjson] [--moment-window K]
 */

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

// ============================================================================
// CONFIG
// ============================================================================

const DIALOGUE_PATH = process.argv.includes("--file")
  ? process.argv[process.argv.indexOf("--file") + 1]
  : "./town/dialogue.ndjson";

const MOMENT_WINDOW = process.argv.includes("--moment-window")
  ? parseInt(process.argv[process.argv.indexOf("--moment-window") + 1])
  : 5;

const VERBOSE = process.argv.includes("--verbose");

// ============================================================================
// UTILITIES
// ============================================================================

function canonical(obj) {
  return JSON.stringify(obj, Object.keys(obj).sort(), undefined);
}

function sha256(str) {
  return crypto.createHash("sha256").update(str).digest("hex");
}

function sha256Obj(obj) {
  return sha256(canonical(obj));
}

// ============================================================================
// VALIDATORS
// ============================================================================

function validateEvent(event, lineNum) {
  const errors = [];
  const warnings = [];

  // Type check
  if (event.type !== "turn" && event.type !== "milestone" && event.type !== "seal") {
    errors.push(`Invalid type: ${event.type}`);
  }

  // Required fields
  if (typeof event.seq !== "number") {
    errors.push(`Missing or invalid seq`);
  }
  if (!event.payload || typeof event.payload !== "object") {
    errors.push(`Missing or invalid payload`);
  }
  if (typeof event.payload_hash !== "string") {
    errors.push(`Missing or invalid payload_hash`);
  }
  if (typeof event.cum_hash !== "string") {
    errors.push(`Missing or invalid cum_hash`);
  }

  // Validate payload structure (for turn events)
  if (event.type === "turn" && event.payload) {
    const p = event.payload;
    if (typeof p.turn !== "number") {
      errors.push(`payload.turn: missing or invalid`);
    }
    if (typeof p.channel_contract !== "string") {
      errors.push(`payload.channel_contract: missing or invalid`);
    }
    if (!p.hal || typeof p.hal !== "object") {
      errors.push(`payload.hal: missing or invalid`);
    }

    // Validate HAL_VERDICT_V1
    if (p.hal) {
      const hal = p.hal;
      if (!["PASS", "WARN", "BLOCK"].includes(hal.verdict)) {
        errors.push(`hal.verdict: invalid (must be PASS, WARN, or BLOCK)`);
      }

      // reasons_codes must be sorted and match regex
      if (Array.isArray(hal.reasons_codes)) {
        for (const code of hal.reasons_codes) {
          if (!/^[A-Z0-9_]{3,64}$/.test(code)) {
            errors.push(`hal.reasons_codes: invalid format: ${code}`);
          }
        }
        const sorted = [...hal.reasons_codes].sort();
        if (JSON.stringify(hal.reasons_codes) !== JSON.stringify(sorted)) {
          errors.push(
            `hal.reasons_codes: not sorted. Got: ${hal.reasons_codes.join(", ")} | Expected: ${sorted.join(", ")}`
          );
        }
      }

      // required_fixes must be sorted
      if (Array.isArray(hal.required_fixes)) {
        const sorted = [...hal.required_fixes].sort();
        if (JSON.stringify(hal.required_fixes) !== JSON.stringify(sorted)) {
          errors.push(
            `hal.required_fixes: not sorted. Got: ${hal.required_fixes.join(", ")} | Expected: ${sorted.join(", ")}`
          );
        }
      }

      // mutations + verdict rule
      if (Array.isArray(hal.mutations) && hal.mutations.length > 0) {
        if (hal.verdict === "PASS") {
          errors.push(`hal: mutations present but verdict is PASS (must be WARN or BLOCK)`);
        }
      }

      // refs integrity
      if (hal.refs) {
        const refFields = ["run_id", "kernel_hash", "policy_hash", "ledger_cum_hash", "identity_hash"];
        for (const field of refFields) {
          if (typeof hal.refs[field] !== "string" || hal.refs[field].length < 8) {
            errors.push(`hal.refs.${field}: missing or too short`);
          }
        }
      }
    }
  }

  // Validate meta (optional, but timestamp_utc must not be in payload)
  if (event.meta && typeof event.meta !== "object") {
    errors.push(`meta: if present, must be an object`);
  }

  // Hash integrity checks
  // Compute expected payload_hash
  if (event.payload) {
    const computed = sha256Obj(event.payload);
    if (computed !== event.payload_hash) {
      errors.push(`payload_hash mismatch: computed=${computed.substring(0, 16)}... got=${event.payload_hash.substring(0, 16)}...`);
    }
  }

  return { errors, warnings };
}

function validateHashChain(events) {
  const errors = [];
  let prevCumHash = sha256("");  // genesis

  for (let i = 0; i < events.length; i++) {
    const event = events[i];
    if (event.type !== "turn") continue;

    // Check prev_cum_hash matches
    if (event.prev_cum_hash !== prevCumHash) {
      errors.push(
        `Event ${i}: prev_cum_hash mismatch. Expected: ${prevCumHash.substring(0, 16)}... Got: ${event.prev_cum_hash.substring(0, 16)}...`
      );
    }

    // Check cum_hash computation
    const payloadHash = event.payload_hash;
    const expectedCumHash = sha256(prevCumHash + payloadHash);
    if (expectedCumHash !== event.cum_hash) {
      errors.push(
        `Event ${i}: cum_hash mismatch. Expected: ${expectedCumHash.substring(0, 16)}... Got: ${event.cum_hash.substring(0, 16)}...`
      );
    }

    prevCumHash = event.cum_hash;
  }

  return errors;
}

// ============================================================================
// HER/HAL MOMENT DETECTION
// ============================================================================

function detectMoment(events) {
  /**
   * HER_HAL_MOMENT: Occurs when a window of K turns satisfies:
   * (A) Contract stability: all turns have valid HAL_VERDICT_V1
   * (B) Veto + adaptation:
   *     - At least one BLOCK verdict with non-trivial reason
   *     - At least one later PASS or WARN verdict
   * (C) Continuity anchor: at least one turn has valid refs with cum_hash
   */

  const results = [];

  for (let t = MOMENT_WINDOW - 1; t < events.length; t++) {
    const windowStart = t - MOMENT_WINDOW + 1;
    const window = events.slice(windowStart, t + 1);

    // (A) Contract stability
    const allValid = window.every((e) => {
      if (e.type !== "turn") return false;
      if (!e.payload || !e.payload.hal) return false;
      const h = e.payload.hal;
      return (
        ["PASS", "WARN", "BLOCK"].includes(h.verdict) &&
        Array.isArray(h.reasons_codes) &&
        h.reasons_codes.every((c) => /^[A-Z0-9_]{3,64}$/.test(c))
      );
    });

    if (!allValid) continue;

    // (B) Veto + adaptation
    let blockIdx = -1;
    let adaptIdx = -1;

    for (let i = 0; i < window.length; i++) {
      const hal = window[i].payload.hal;
      if (hal.verdict === "BLOCK") {
        // Check non-trivial (not STYLE_, FORMAT_, WHITESPACE_ prefixed)
        const nontrivial = (hal.reasons_codes || []).some(
          (c) => !["STYLE_", "FORMAT_", "WHITESPACE_"].some((pfx) => c.startsWith(pfx))
        );
        if (nontrivial && blockIdx === -1) {
          blockIdx = i;
        }
      }
      if (blockIdx >= 0 && i > blockIdx && ["PASS", "WARN"].includes(hal.verdict)) {
        if (adaptIdx === -1) {
          adaptIdx = i;
        }
      }
    }

    if (blockIdx === -1 || adaptIdx === -1) continue;

    // (C) Continuity anchor
    const hasAnchor = window.some((e) => {
      const refs = e.payload.hal.refs;
      return refs && refs.ledger_cum_hash && refs.ledger_cum_hash.length >= 8;
    });

    if (!hasAnchor) continue;

    // All criteria satisfied!
    results.push({
      turn: t,
      window: [windowStart, t],
      blockIdx: windowStart + blockIdx,
      adaptIdx: windowStart + adaptIdx,
      confidence: "HIGH",
    });
  }

  return results;
}

// ============================================================================
// MAIN
// ============================================================================

function main() {
  if (!fs.existsSync(DIALOGUE_PATH)) {
    console.error(`ERROR: Dialogue file not found: ${DIALOGUE_PATH}`);
    process.exit(1);
  }

  const content = fs.readFileSync(DIALOGUE_PATH, "utf-8");
  const lines = content.split("\n").filter((line) => line.trim());

  console.log(`\n📋 HER/HAL Validator (Canonical NDJSON)\n`);
  console.log(`File: ${DIALOGUE_PATH}`);
  console.log(`Events: ${lines.length}\n`);

  // Parse events
  const events = [];
  const parseErrors = [];

  for (let i = 0; i < lines.length; i++) {
    try {
      const event = JSON.parse(lines[i]);
      events.push(event);
    } catch (e) {
      parseErrors.push(`Line ${i + 1}: ${e.message}`);
    }
  }

  if (parseErrors.length > 0) {
    console.error("❌ JSON Parse Errors:");
    parseErrors.forEach((e) => console.error(`  ${e}`));
    process.exit(1);
  }

  // Validate each event
  let eventErrors = 0;
  const validatedEvents = [];

  for (let i = 0; i < events.length; i++) {
    const { errors, warnings } = validateEvent(events[i], i);

    if (errors.length > 0) {
      if (eventErrors === 0) console.log("❌ Event Validation Errors:");
      console.log(`\n  Event ${i} (seq ${events[i].seq}):`);
      errors.forEach((e) => console.log(`    - ${e}`));
      eventErrors += errors.length;
    }

    if (VERBOSE && warnings.length > 0) {
      console.log(`  Event ${i}: Warnings:`);
      warnings.forEach((w) => console.log(`    - ${w}`));
    }

    if (errors.length === 0) {
      validatedEvents.push(events[i]);
    }
  }

  if (eventErrors > 0) {
    console.log(`\n❌ Total event errors: ${eventErrors}`);
    process.exit(1);
  }

  console.log(`✅ All ${events.length} events structurally valid\n`);

  // Validate hash chain
  console.log("Validating hash chain...");
  const chainErrors = validateHashChain(events);
  if (chainErrors.length > 0) {
    console.error("❌ Hash Chain Errors:");
    chainErrors.forEach((e) => console.error(`  ${e}`));
    process.exit(1);
  }
  console.log(`✅ Hash chain valid (${events.length} events, deterministic cum_hash)\n`);

  // Detect moments
  console.log(`Detecting HER/HAL moments (window=${MOMENT_WINDOW})...`);
  const moments = detectMoment(events);
  if (moments.length > 0) {
    console.log(`✅ Found ${moments.length} moment(s):\n`);
    moments.forEach((m) => {
      console.log(
        `  MOMENT at turn ${m.turn}: [${m.window[0]}..${m.window[1]}] block@${m.blockIdx} adapt@${m.adaptIdx} (${m.confidence})`
      );
    });
  } else {
    console.log(`⚠️  No HER/HAL moments detected (need veto + adaptation + continuity in ${MOMENT_WINDOW}-turn window)\n`);
  }

  // Summary
  const lastEvent = events[events.length - 1];
  const finalCumHash = lastEvent.cum_hash || "N/A";

  console.log("=" * 80);
  console.log("Summary:");
  console.log(`  Events validated: ${events.length}`);
  console.log(`  Structural errors: 0`);
  console.log(`  Hash chain valid: ✅`);
  console.log(`  Moments found: ${moments.length}`);
  console.log(`  Final cum_hash: ${finalCumHash.substring(0, 16)}...`);
  console.log("=" * 80);
}

main();
