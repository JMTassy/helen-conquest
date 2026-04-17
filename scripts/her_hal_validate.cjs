#!/usr/bin/env node
/* eslint-disable no-console */

const fs = require("node:fs");
const path = require("node:path");

function die(msg) {
  console.error(msg);
  process.exit(1);
}

function splitHerHal(text) {
  const herTag = "[HER]";
  const halTag = "[HAL]";
  const iHer = text.indexOf(herTag);
  const iHal = text.indexOf(halTag);

  if (iHer !== 0) throw new Error("Missing [HER] at start of message.");
  if (iHal < 0) throw new Error("Missing [HAL] block.");
  if (iHal <= iHer) throw new Error("Malformed ordering: [HAL] must come after [HER].");

  const her = text.slice(herTag.length, iHal).trimEnd();
  const halRaw = text.slice(iHal + halTag.length).trim();

  // HAL must be exactly one JSON object on one line (no prose)
  const halLines = halRaw.split(/\r?\n/).filter((l) => l.trim().length > 0);
  if (halLines.length !== 1) throw new Error("HAL block must be exactly one non-empty line of JSON.");
  const halJsonLine = halLines[0];

  let hal;
  try {
    hal = JSON.parse(halJsonLine);
  } catch {
    throw new Error("HAL line is not valid JSON.");
  }

  return { her, hal, halJsonLine };
}

function validateHalShape(hal) {
  const requiredTop = ["verdict", "reasons", "required_fixes", "certificates", "refs", "mutations"];
  for (const k of requiredTop) if (!(k in hal)) throw new Error(`HAL missing required key: ${k}`);

  const verdicts = new Set(["PASS", "WARN", "BLOCK"]);
  if (!verdicts.has(hal.verdict)) throw new Error(`HAL.verdict invalid: ${hal.verdict}`);

  for (const arrKey of ["reasons", "required_fixes", "certificates", "mutations"]) {
    if (!Array.isArray(hal[arrKey])) throw new Error(`HAL.${arrKey} must be an array.`);
  }
  for (const arrKey of ["reasons", "required_fixes", "certificates"]) {
    for (const v of hal[arrKey]) if (typeof v !== "string") throw new Error(`HAL.${arrKey} must contain strings only.`);
  }

  if (typeof hal.refs !== "object" || hal.refs === null) throw new Error("HAL.refs must be an object.");
  for (const k of ["run_id", "kernel_hash", "policy_hash", "ledger_cum_hash"]) {
    if (typeof hal.refs[k] !== "string" || hal.refs[k].length < 8) {
      throw new Error(`HAL.refs.${k} must be a string length>=8.`);
    }
  }

  // No policy escalation: if mutations non-empty, cannot be PASS.
  if (hal.mutations.length > 0 && hal.verdict === "PASS") {
    throw new Error("HAL.mutations non-empty requires verdict WARN or BLOCK (never PASS).");
  }

  // Deterministic reason ordering: enforce lexicographic ordering (simple, stable).
  const sortedReasons = [...hal.reasons].slice().sort();
  for (let i = 0; i < sortedReasons.length; i++) {
    if (sortedReasons[i] !== hal.reasons[i]) {
      throw new Error("HAL.reasons must be lexicographically sorted for determinism.");
    }
  }
  const sortedFixes = [...hal.required_fixes].slice().sort();
  for (let i = 0; i < sortedFixes.length; i++) {
    if (sortedFixes[i] !== hal.required_fixes[i]) {
      throw new Error("HAL.required_fixes must be lexicographically sorted for determinism.");
    }
  }

  // HER constraints (light): max 12 lines; no JSON objects.
  // (We validate HER elsewhere after parsing.)
}

function validateHerText(her) {
  const lines = her.split(/\r?\n/);
  if (lines.length > 12) throw new Error(`HER exceeds 12 lines (${lines.length}).`);
  // crude JSON detection: forbid a top-level JSON object line to avoid leakage
  for (const l of lines) {
    const t = l.trim();
    if (t.startsWith("{") && t.endsWith("}")) {
      throw new Error("HER appears to contain JSON; forbidden.");
    }
  }
}

function main() {
  const file = process.argv[2];
  if (!file) die("Usage: node scripts/her_hal_validate.cjs <transcript.txt>");

  const text = fs.readFileSync(file, "utf8");

  // A transcript may contain multiple messages separated by "\n---\n"
  const messages = text.split(/\n---\n/g).map((s) => s.trim()).filter(Boolean);
  if (messages.length === 0) die("No messages found.");

  let ok = 0;
  messages.forEach((msg, idx) => {
    try {
      const { her, hal } = splitHerHal(msg);
      validateHerText(her);
      validateHalShape(hal);
      ok += 1;
    } catch (e) {
      die(`FAIL message #${idx + 1}: ${e.message}`);
    }
  });

  console.log(`PASS: ${ok}/${messages.length} messages validated`);
}

main();
