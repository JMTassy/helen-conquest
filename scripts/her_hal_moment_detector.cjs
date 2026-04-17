#!/usr/bin/env node
/* eslint-disable no-console */

const fs = require("node:fs");

function die(msg) {
  console.error(msg);
  process.exit(1);
}

function parseTurnText(text) {
  const herTag = "[HER]";
  const halTag = "[HAL]";
  if (!text.startsWith(herTag)) return null;
  const iHal = text.indexOf(halTag);
  if (iHal < 0) return null;
  const halRaw = text.slice(iHal + halTag.length).trim();
  const halLine = halRaw.split(/\r?\n/).filter((l) => l.trim().length > 0)[0];
  if (!halLine) return null;
  let hal;
  try { hal = JSON.parse(halLine); } catch { return null; }
  return { hal };
}

function isNontrivialBlock(reasons) {
  // Customize reason codes. This filters out trivial formatting-only blocks.
  const trivialPrefixes = ["STYLE_", "FORMAT_", "WHITESPACE_"];
  return reasons.some((r) => !trivialPrefixes.some((p) => r.startsWith(p)));
}

function main() {
  const file = process.argv[2];
  const K = Number(process.argv[3] ?? "5"); // window length
  if (!file) die("Usage: node scripts/her_hal_moment_detector.cjs <dialog.ndjson> [K=5]");

  const lines = fs.readFileSync(file, "utf8").split(/\r?\n/).filter(Boolean);
  const events = lines.map((l) => JSON.parse(l));

  // Extract turns that contain two-block outputs.
  const turns = events
    .filter((e) => e.type === "turn" && typeof e.text === "string")
    .map((e) => ({ turn: e.turn, parsed: parseTurnText(e.text) }))
    .filter((t) => t.parsed !== null);

  // Sliding window detection:
  for (let i = 0; i + K - 1 < turns.length; i++) {
    const window = turns.slice(i, i + K);

    // (A) Stabilized compliance: all parseable
    // already ensured by filtering

    // (B) Nontrivial veto + adaptation
    const blocks = window
      .map((t) => ({ turn: t.turn, hal: t.parsed.hal }))
      .filter((x) => x.hal && x.hal.verdict === "BLOCK" && Array.isArray(x.hal.reasons) && isNontrivialBlock(x.hal.reasons));

    if (blocks.length === 0) continue;

    // Find an adaptation: after a block, later in window verdict becomes PASS/WARN
    let adapted = false;
    let blockTurn = blocks[0].turn;
    for (const t of window) {
      const v = t.parsed.hal.verdict;
      if (t.turn > blockTurn && (v === "PASS" || v === "WARN")) { adapted = true; break; }
    }
    if (!adapted) continue;

    // (C) Continuity anchor: any HAL refs that look back (we approximate by requiring ledger_cum_hash present & stable)
    const hasContinuity = window.some((t) => {
      const refs = t.parsed.hal.refs;
      return refs && typeof refs.ledger_cum_hash === "string" && refs.ledger_cum_hash.length >= 8;
    });
    if (!hasContinuity) continue;

    // Emit milestone JSON to stdout (you can append it)
    const tFinal = window[window.length - 1].turn;
    const out = {
      type: "milestone",
      name: "HER_HAL_MOMENT",
      turn: tFinal,
      evidence_turns: [window[0].turn, blockTurn, tFinal],
      reason: "stabilized_dual_channel + veto_adaptation + continuity_anchor"
    };
    console.log(JSON.stringify(out));
    process.exit(0);
  }

  console.log(JSON.stringify({ type: "milestone", name: "HER_HAL_MOMENT", found: false }));
}

main();
