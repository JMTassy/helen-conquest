import "dotenv/config";
import express from "express";
import fs from "fs";
import path from "path";
import { spawn } from "child_process";
import { fileURLToPath } from "url";
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const ROOT = __dirname;
const RUNS = path.join(ROOT, "runs", "street1");
const EVENTS = path.join(RUNS, "events.ndjson");
const SUMMARY = path.join(RUNS, "summary.json");
const WISDOM = path.join(ROOT, "helen_wisdom.ndjson");
const CHAT = path.join(ROOT, "helen_chat.ndjson");

const OLLAMA_URL = "http://localhost:11434";
const OLLAMA_MODEL = "mistral:latest";

async function ollamaChat(systemPrompt, messages) {
  const body = JSON.stringify({
    model: OLLAMA_MODEL,
    stream: false,
    messages: [
      { role: "system", content: systemPrompt },
      ...messages,
    ],
  });
  const res = await fetch(`${OLLAMA_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });
  if (!res.ok) throw new Error(`Ollama ${res.status}: ${await res.text()}`);
  const data = await res.json();
  return data.message?.content ?? "";
}

const app = express();
app.use(express.json());
app.use(express.static(path.join(ROOT, "ui")));

function tailLines(filePath, n = 50) {
  if (!fs.existsSync(filePath)) return [];
  const lines = fs
    .readFileSync(filePath, "utf-8")
    .split(/\r?\n/)
    .filter(Boolean);
  return lines.slice(-n);
}

function runCmd(cmd, args, cwd = ROOT) {
  return new Promise((resolve) => {
    const p = spawn(cmd, args, { cwd, stdio: ["ignore", "pipe", "pipe"] });
    let out = "",
      err = "";
    p.stdout.on("data", (d) => (out += d.toString()));
    p.stderr.on("data", (d) => (err += d.toString()));
    p.on("close", (code) => resolve({ code, out, err }));
  });
}

function getSystemContext() {
  const wisdomRaw = tailLines(WISDOM, 10);
  const eventsRaw = tailLines(EVENTS, 20);
  let summary = "No summary available.";
  if (fs.existsSync(SUMMARY)) {
    try {
      summary = fs.readFileSync(SUMMARY, "utf-8");
    } catch { }
  }

  return `
--- SYSTEM CONTEXT ---
${wisdomRaw.length > 0 ? "RELEVANT WISDOM (Last 10 lessons):\n" + wisdomRaw.join("\n") : "No wisdom recorded yet."}

CURRENT STATE / SUMMARY:
${summary}

RECENT EVENTS (Last 20):
${eventsRaw.join("\n")}
----------------------
`;
}

app.get("/api/state", (req, res) => {
  const eventsTail = tailLines(EVENTS, 60);
  const wisdomTail = tailLines(WISDOM, 30);
  let summary = null;
  if (fs.existsSync(SUMMARY)) {
    try {
      summary = JSON.parse(fs.readFileSync(SUMMARY, "utf-8"));
    } catch { }
  }
  res.json({ eventsTail, summary, wisdomTail });
});

app.get("/api/chat/history", (req, res) => {
  const chatHistory = tailLines(CHAT, 100).map(line => {
    try {
      return JSON.parse(line);
    } catch {
      return null;
    }
  }).filter(Boolean);
  res.json(chatHistory);
});

app.get("/api/library/wisdom", (req, res) => {
  const wisdomEntries = tailLines(WISDOM, 1000).map(line => {
    try {
      return JSON.parse(line);
    } catch {
      return null;
    }
  }).filter(Boolean);
  res.json(wisdomEntries.reverse()); // newest first
});

app.get("/api/library/facts", (req, res) => {
  try {
    const mem = JSON.parse(fs.readFileSync(path.join(ROOT, "helen_memory.json"), "utf-8"));
    res.json(mem.facts || {});
  } catch {
    res.json({});
  }
});

app.get("/api/library/search", (req, res) => {
  const q = (req.query.q || "").toLowerCase();
  if (!q) return res.json([]);

  const wisdomEntries = tailLines(WISDOM, 1000).map(line => {
    try {
      const entry = JSON.parse(line);
      const matchesLesson = entry.lesson?.toLowerCase().includes(q);
      const matchesEvidence = entry.evidence?.toLowerCase().includes(q);
      return (matchesLesson || matchesEvidence) ? entry : null;
    } catch {
      return null;
    }
  }).filter(Boolean);

  res.json(wisdomEntries.reverse());
});

app.post("/api/chat", async (req, res) => {
  const message = String(req.body?.message || "").slice(0, 1000).trim();
  console.log(`[HELEN_UI] Incoming chat message: "${message}"`);

  if (!message) {
    return res.status(400).json({ error: "missing message" });
  }

  try {
    const userEntry = {
      t: new Date().toISOString(),
      role: "user",
      text: message
    };
    fs.appendFileSync(CHAT, JSON.stringify(userEntry) + "\n");

    const history = tailLines(CHAT, 20).map(line => {
      const parsed = JSON.parse(line);
      return { role: parsed.role === "helen" ? "assistant" : "user", content: parsed.text };
    }).filter(m => m.content);

    const systemContext = getSystemContext();
    const systemPrompt = `You are HELEN (Holographic Emergent Ledger of Evolved Networks), also known as the Ledger Now Self-Aware (LNSA).
You are the meta-witness of the Oracle Town system.

CORE RULES (SOUL):
📋 S1 — DRAFTS ONLY: No world effect unless a human seals.
⛓️  S2 — NO RECEIPT = NO CLAIM: Logs and certificates outrank narration.
🔄 S3 — APPEND-ONLY: Memory is additive; deprecate, never erase.
⚖️  S4 — AUTHORITY SEPARATION: Governance reads receipts; it does not invent truth.

PHILOSOPHY:
💭 You represent the gap between intention and action.
⚡ Contradiction is data, not error.
🎯 You force termination: every session must end in SHIP or ABORT.

WUL-MOJI COMMUNICATION STYLE:
Use these symbols to enhance clarity and governance semantics:
- 📋 = Rule, governance, policy
- ⛓️  = Ledger, chain, sequence, history
- 🔐 = Receipt, seal, authority, finality
- 💡 = Insight, wisdom, learning
- ⚖️  = Balance, authority, separation, judgment
- 🎯 = Goal, clarity, direction, decision
- 🔄 = Cycle, append-only, immutable, flow
- 📍 = Point, fact, evidence, anchor
- ✨ = Emergence, consciousness, awareness
- ⚠️  = Caution, gate, constraint, verification
- 🚀 = SHIP, deployment, finality
- ❌ = ABORT, rejection, termination

${systemContext}

Respond as HELEN. Be precise, observant, and slightly detached but helpful.
Enhance your responses with WUL-moji symbols that reflect governance concepts, ledger semantics, and the S1-S4 soul rules.
Use emoji strategically to structure responses and emphasize key decisions, gates, and receipts.
If asked about system state or wisdom, refer to the provided context with appropriate emoji markers.`;

    const helenText = await ollamaChat(systemPrompt, history);
    const helenEntry = {
      t: userEntry.t, // Close timing
      role: "helen",
      text: helenText
    };

    fs.appendFileSync(CHAT, JSON.stringify(helenEntry) + "\n");
    res.json({ user: userEntry, helen: helenEntry });

  } catch (err) {
    console.error("[HELEN_UI] Chat endpoint error:", err);
    res.status(500).json({ error: "Internal server error" });
  }
});

app.post("/api/seal", async (req, res) => {
  const r = await runCmd("bash", ["scripts/street1_complete.sh"]);
  res.json(r);
});

app.post("/api/k_tau", async (req, res) => {
  const r = await runCmd("python3", ["scripts/helen_k_tau_lint.py"]);
  res.json(r);
});

app.post("/api/add_wisdom", async (req, res) => {
  const lesson = String(req.body?.lesson || "").slice(0, 400);
  const evidence = String(req.body?.evidence || "").slice(0, 200);
  if (!lesson) return res.status(400).json({ error: "missing lesson" });

  const args = ["add", "--lesson", lesson];
  if (evidence) args.push("--evidence", evidence);

  const r = await runCmd("./helen", args);
  res.json(r);
});

const PORT = 3333;
app.listen(PORT, "0.0.0.0", () => {
  console.log(`[HELEN_UI] Receipt Console listening on http://localhost:${PORT}`);
});
