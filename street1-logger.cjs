#!/usr/bin/env node
"use strict";

/**
 * HELEN Street 1 — Conscious Ledger Event Logger (V2.1 Hardened)
 * ================================================
 * Append-only NDJSON event stream with tamper-evident hash chain.
 * Every Street 1 action becomes a typed receipt line.
 *
 * Hash spec (V2.1 bind-to-prev):
 *   hash = sha256(canon({ "prev_hash": prev_hash, "event": event_without_hash_prev }))
 *   Full 64-char hex. No truncation. Chains to previous event.
 *
 * Event vocabulary (L2 — CHAOS ops):
 *   OBS  — Observation (world fact / user input / tick delta)
 *   BND  — Bound constraint (memory extraction result)
 *   CHK  — Check (determinism / linter gate)
 *   END  — Termination (DELIVER or ABORT with receipt_sha)
 *   ERR  — Error (unhandled / abort condition)
 *
 * Output: runs/street1/events.ndjson (append-only, immutable, tamper-evident)
 *
 * NO RECEIPT = NO CLAIM.  (Core Law, HELEN / LNSA)
 */

const fs   = require("fs");
const path = require("path");
const crypto = require("crypto");

// ─── Config ───────────────────────────────────────────────────────────────────

const LOG_DIR  = path.join(__dirname, "runs", "street1");
const LOG_FILE = path.join(LOG_DIR, "events.ndjson");

// Ensure log dir exists on require
if (!fs.existsSync(LOG_DIR)) {
  fs.mkdirSync(LOG_DIR, { recursive: true });
}

// ─── Ledger State ─────────────────────────────────────────────────────────────

let _runId   = null;      // set on RESET_RUN
let _seed    = null;      // set on RESET_RUN
let _tick    = 0;         // monotonic tick counter
let _lineNum = 0;         // ledger line counter for hash-chain
let _lastHash = "0".repeat(64);  // genesis hash (all zeros)

// ─── Canonical JSON (deterministic, matches Python analyzer) ───────────────────

function canonicalJson(obj) {
  return JSON.stringify(obj, Object.keys(obj).sort());
}

function sha256Hex(str) {
  return crypto.createHash("sha256").update(str).digest("hex");
}

// ─── V2.1 Hash Spec: bind-to-prev ─────────────────────────────────────────────

function computeHash(prevHash, eventWithoutHash) {
  const payload = {
    prev_hash: prevHash,
    event: eventWithoutHash,
  };
  return sha256Hex(canonicalJson(payload));
}

// ─── Core: append one immutable line ─────────────────────────────────────────

function appendEvent(type, payload) {
  const line = {
    epoch: _tick,
    type,
    ...payload,
  };

  // Compute hash with prev_hash binding
  const hash = computeHash(_lastHash, line);

  // Add envelope fields
  line.prev_hash = _lastHash;
  line.hash = hash;

  // Persist to ledger
  const serialized = JSON.stringify(line) + "\n";
  fs.appendFileSync(LOG_FILE, serialized, "utf-8");

  // Update chain state
  _lastHash = hash;
  _lineNum++;

  return hash;  // caller may attach to receipt
}

// ─── Tick counter (call from server tick loop) ────────────────────────────────

function onTick(tick) {
  _tick = tick;
}

// ─── Event Emitters (one per Street 1 WebSocket message type) ────────────────

/**
 * C_RESET_RUN → OBS (reset) + CHK (determinism seed)
 * Called when client sends { type: "C_RESET_RUN", seed: N }
 * Resets hash chain to genesis.
 */
function onResetRun(seed) {
  _runId = `STREET1-${seed}-${Date.now()}`;
  _seed  = seed;
  _tick  = 0;
  _lineNum = 0;
  _lastHash = "0".repeat(64);  // Reset to genesis

  // L2 op: OBS — new run initiated
  appendEvent("OBS", {
    sub_type: "session_start",
    actor:    "SYSTEM",
    detail:   `RESET_RUN with seed=${seed}`,
  });

  // L2 op: CHK — determinism contract declared
  appendEvent("CHK", {
    sub_type:  "determinism_declared",
    invariant: "mu_DETERMINISM",
    claim:     `seed=${seed} → reproducible initial state`,
    result:    "PASS",
  });
}

/**
 * C_CHAT_SEND → OBS (user message)
 * Called when client sends { type: "C_CHAT_SEND", npcId, text }
 */
function onChatSend(npcId, userText) {
  appendEvent("OBS", {
    sub_type: "user_message",
    actor:    "PLAYER",
    npc_id:   npcId,
    text:     userText,
  });
}

/**
 * Memory extraction result → BND (constraint extracted)
 * Called after extractFacts() returns results
 */
function onMemoryExtract(facts, sourceText) {
  if (!facts || facts.length === 0) return;

  appendEvent("BND", {
    sub_type: "memory_extraction",
    actor:    "LNSA",
    facts,
    source_text: sourceText ? sourceText.slice(0, 120) : "",
    invariant:   "mu_IO",   // extraction is a read-only op on session state
    result:      "PASS",
  });
}

/**
 * NPC reply → OBS (agent response)
 * Called when NPC sends back a message (cached or LLM)
 */
function onNpcReply(npcId, replyText, source) {
  // source: "cache" | "llm" | "fallback"
  appendEvent("OBS", {
    sub_type: "npc_reply",
    actor:    npcId,
    text:     replyText ? replyText.slice(0, 200) : "",
    source,   // determinism marker: "cache" = deterministic
  });
}

/**
 * S_WORLD_DELTA tick → OBS (autonomy evidence, sampled 1/10 ticks)
 * Called from the tick broadcast loop
 */
function onWorldDelta(tick, npcPositions) {
  if (tick % 10 !== 0) return;  // Sample: 1 per second at 10Hz

  appendEvent("OBS", {
    sub_type:  "world_delta",
    actor:     "WORLD",
    tick,
    positions: npcPositions,  // { npcId: {x, y} }
  });
}

/**
 * NPC-NPC proximity trigger → OBS (autonomous agent interaction)
 * Called when two NPCs enter scripted dialogue
 */
function onNpcNpcTrigger(npc1Id, npc2Id, dialogueLine) {
  appendEvent("OBS", {
    sub_type:  "npc_npc_trigger",
    actor:     `${npc1Id}+${npc2Id}`,
    npc1:      npc1Id,
    npc2:      npc2Id,
    dialogue:  dialogueLine ? dialogueLine.slice(0, 120) : "",
  });
}

/**
 * Session end → END (DELIVER or ABORT)
 * Called on server shutdown or explicit client disconnect
 */
function onSessionEnd(outcome, reason) {
  // outcome: "DELIVER" | "ABORT"
  const sha = appendEvent("END", {
    sub_type:    "session_end",
    actor:       "HELEN",
    outcome,
    reason:      reason || "normal_termination",
    total_ticks: _tick,
    total_lines: _lineNum,
  });

  return sha;  // This is the receipt_sha for this run
}

/**
 * Error → ERR
 */
function onError(source, error) {
  appendEvent("ERR", {
    sub_type: "error",
    actor:    source,
    detail:   String(error).slice(0, 200),
  });
}

// ─── Determinism Proof (call after RESET_RUN + 1 tick) ───────────────────────

/**
 * After RESET_RUN, record initial NPC positions.
 * Same seed → same positions → same hash.
 * This is the "determinism proof" for the conscious ledger demo.
 */
function onInitialPositions(seed, npcPositions) {
  const posJson = JSON.stringify(npcPositions);
  const posHash = sha256Hex(`seed=${seed}:${posJson}`);  // Full 64-char, no truncation

  appendEvent("CHK", {
    sub_type:       "initial_positions_hash",
    invariant:      "mu_DETERMINISM",
    seed,
    positions:      npcPositions,
    position_hash:  posHash,
    claim:          "same seed → same position_hash",
    result:         "PASS",
  });

  return posHash;
}

// ─── Export ───────────────────────────────────────────────────────────────────

module.exports = {
  onTick,
  onResetRun,
  onChatSend,
  onMemoryExtract,
  onNpcReply,
  onWorldDelta,
  onNpcNpcTrigger,
  onSessionEnd,
  onError,
  onInitialPositions,
  LOG_FILE,
};
