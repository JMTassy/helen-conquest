#!/usr/bin/env node
/* eslint-disable no-console */

const fs = require("node:fs");

function die(msg) {
  console.error(msg);
  process.exit(1);
}

function get(obj, path) {
  // Simple dot-path getter: "a.b.c"
  if (!path) return undefined;
  return path.split(".").reduce((acc, k) => (acc && acc[k] !== undefined ? acc[k] : undefined), obj);
}

function parseHerHalFromText(text) {
  const herTag = "[HER]";
  const halTag = "[HAL]";
  if (typeof text !== "string" || !text.startsWith(herTag)) return null;
  const iHal = text.indexOf(halTag);
  if (iHal < 0) return null;

  const halRaw = text.slice(iHal + halTag.length).trim();
  const halLine = halRaw.split(/\r?\n/).filter((l) => l.trim().length > 0)[0];
  if (!halLine) return null;

  let hal;
  try { hal = JSON.parse(halLine); } catch { return null; }
  return { hal };
}

function isNontrivialBlock(reasons, trivialPrefixes) {
  if (!Array.isArray(reasons)) return false;
  return reasons.some((r) => typeof r === "string" && !trivialPrefixes.some((p) => r.startsWith(p)));
}

function main() {
  const file = process.argv[2];
  const configPath = process.argv[3];
  const K = Number(process.argv[4] ?? "5");

  if (!file || !configPath) {
    die("Usage: node scripts/her_hal_moment_detector_v2.cjs <dialog.ndjson> <config.json> [K=5]");
  }

  const cfg = JSON.parse(fs.readFileSync(configPath, "utf8"));
  const lines = fs.readFileSync(file, "utf8").split(/\r?\n/).filter(Boolean);
  const events = lines.map((l) => JSON.parse(l));

  const trivialPrefixes = cfg.trivial_reason_prefixes ?? ["STYLE_", "FORMAT_", "WHITESPACE_"];

  // Extract turns
  const turns = [];
  for (const e of events) {
    // identify a turn event
    const typeVal = cfg.turn_event_key ? get(e, cfg.turn_event_key) : e.type;
    if (typeVal !== cfg.turn_event_value) continue;

    const turn = Number(get(e, cfg.turn_field));
    if (!Number.isFinite(turn)) continue;

    let hal = null;

    // Option A: HAL object exists directly
    if (cfg.hal_object_field) {
      const obj = get(e, cfg.hal_object_field);
      if (obj && typeof obj === "object") hal = obj;
    }

    // Option B: parse from combined text
    if (!hal && cfg.text_field) {
      const txt = get(e, cfg.text_field);
      const parsed = parseHerHalFromText(txt);
      if (parsed) hal = parsed.hal;
    }

    if (!hal) continue;
    turns.push({ turn, hal });
  }

  // Sliding window
  for (let i = 0; i + K - 1 < turns.length; i++) {
    const window = turns.slice(i, i + K);

    // (B) Nontrivial veto + adaptation
    const blocks = window.filter(
      (x) => x.hal.verdict === "BLOCK" && isNontrivialBlock(x.hal.reasons, trivialPrefixes)
    );
    if (blocks.length === 0) continue;

    const blockTurn = blocks[0].turn;
    const adapted = window.some((x) => x.turn > blockTurn && (x.hal.verdict === "PASS" || x.hal.verdict === "WARN"));
    if (!adapted) continue;

    // (C) Continuity anchor: presence of ledger_cum_hash in refs
    const hasContinuity = window.some((x) => {
      const refs = x.hal.refs;
      return refs && typeof refs.ledger_cum_hash === "string" && refs.ledger_cum_hash.length >= 8;
    });
    if (!hasContinuity) continue;

    const tFinal = window[window.length - 1].turn;
    console.log(JSON.stringify({
      type: "milestone",
      name: "HER_HAL_MOMENT",
      turn: tFinal,
      evidence_turns: [window[0].turn, blockTurn, tFinal],
      reason: "stabilized_dual_channel + veto_adaptation + continuity_anchor"
    }));
    process.exit(0);
  }

  console.log(JSON.stringify({ type: "milestone", name: "HER_HAL_MOMENT", found: false }));
}

main();
