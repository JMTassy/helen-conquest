#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const http = require("http");
const express = require("express");
const WebSocket = require("ws");
const logger = require("./street1-logger.cjs");

// ─────────────────────────────────────────────────────────────────────────────
// CONFIG
// ─────────────────────────────────────────────────────────────────────────────

const PORT = process.env.PORT ? Number(process.env.PORT) : 3001;
const CONTENT_DIR = path.join(__dirname, "content");
const HTML_PATH = path.join(__dirname, "street1.html");

const TICK_HZ = 10;               // Deterministic tick rate
const TICK_MS = 1000 / TICK_HZ;
const NPC_THINK_MS = 900;         // Simulated thinking latency
const CHAT_HARD_TIMEOUT_MS = 2500;

// ─────────────────────────────────────────────────────────────────────────────
// DETERMINISTIC RNG (Mulberry32)
// ─────────────────────────────────────────────────────────────────────────────

function mulberry32(seed) {
  let t = seed >>> 0;
  return function () {
    t += 0x6D2B79F5;
    let x = Math.imul(t ^ (t >>> 15), 1 | t);
    x ^= x + Math.imul(x ^ (x >>> 7), 61 | x);
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// CONTENT LOADING
// ─────────────────────────────────────────────────────────────────────────────

function readJSON(filename) {
  const p = path.join(CONTENT_DIR, filename);
  if (!fs.existsSync(p)) {
    throw new Error(`Missing content file: ${filename}`);
  }
  return JSON.parse(fs.readFileSync(p, "utf-8"));
}

function loadContent() {
  const tilemap = readJSON("street1.tilemap.json");
  const personas = readJSON("street1.personas.json");
  const lines = readJSON("street1.lines.json");
  const demo = readJSON("street1.demoScript.json");
  return { tilemap, personas, lines, demo };
}

// ─────────────────────────────────────────────────────────────────────────────
// WORLD STATE
// ─────────────────────────────────────────────────────────────────────────────

function makeWorld(seed, content) {
  const rng = mulberry32(seed);
  const grid = content.tilemap.grid || { width: 24, height: 14 };
  const walkable_mask = content.tilemap.walkable_mask || [];
  const buildings = content.tilemap.buildings || [];

  // NPCs: load spawn points + waypoints from tilemap
  const npcs = (content.tilemap.npcs || []).map((nDef) => ({
    id: nDef.id,
    x: nDef.spawn?.x ?? 0,
    y: nDef.spawn?.y ?? 0,
    targetX: nDef.spawn?.x ?? 0,
    targetY: nDef.spawn?.y ?? 0,
    waypoints: nDef.waypoints || [],
    waypointIdx: 0,
    waypointTimer: 0,
    mode: "IDLE", // IDLE | WALKING | TALKING | THINKING
    thought: "",
    thoughtTimer: 0,
    npcNpcCooldown: 0,
  }));

  const player = { x: 12.5, y: 7.5 };

  return {
    seed,
    tick: 0,
    rng,
    grid,
    walkable_mask,
    buildings,
    npcs,
    player,
    sessionMemory: {
      facts: [],
      history: [],
    },
    activeLLM: {},
    _pairCooldown: {}, // NPC-NPC trigger cooldown
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// WALKABLE CHECK
// ─────────────────────────────────────────────────────────────────────────────

function isWalkable(world, tx, ty) {
  const col = Math.floor(tx);
  const row = Math.floor(ty);
  if (col < 0 || col >= world.grid.width || row < 0 || row >= world.grid.height) {
    return false;
  }
  const idx = row * world.grid.width + col;
  if (idx >= world.walkable_mask.length) return true; // Safe default
  return world.walkable_mask[idx] === true;
}

// ─────────────────────────────────────────────────────────────────────────────
// NPC AUTONOMOUS MOVEMENT
// ─────────────────────────────────────────────────────────────────────────────

const NPC_SPEED = 2.5; // tiles per second

function tickNPC(world, npc, dtSec) {
  // Frozen while interacting with player
  if (npc.mode === "TALKING" || npc.mode === "THINKING") {
    return;
  }

  // Move toward target
  const dx = npc.targetX - npc.x;
  const dy = npc.targetY - npc.y;
  const dist = Math.sqrt(dx * dx + dy * dy);

  if (dist > 0.05) {
    npc.mode = "WALKING";
    const step = Math.min(NPC_SPEED * dtSec, dist);
    const nx = npc.x + (dx / dist) * step;
    const ny = npc.y + (dy / dist) * step;

    if (isWalkable(world, nx, ny)) {
      npc.x = nx;
      npc.y = ny;
    } else if (isWalkable(world, nx, npc.y)) {
      npc.x = nx;
    } else if (isWalkable(world, npc.x, ny)) {
      npc.y = ny;
    }
  } else {
    // Reached target — pick next waypoint
    npc.mode = "IDLE";
    npc.waypointTimer -= dtSec;

    if (npc.waypointTimer <= 0) {
      const wps = npc.waypoints;
      if (wps.length === 0) {
        npc.thought = "";
        return;
      }

      npc.waypointIdx = (npc.waypointIdx + 1) % wps.length;
      const wp = wps[npc.waypointIdx];

      // Small jitter via seeded RNG
      npc.targetX = wp.x + 0.5 + (world.rng() - 0.5) * 0.4;
      npc.targetY = wp.y + 0.5 + (world.rng() - 0.5) * 0.4;
      npc.waypointTimer = (wp.pause_sec || 3) + world.rng() * 2;
    }
  }

  // Thought bubble rotation (deterministic)
  npc.thoughtTimer -= dtSec;
  if (npc.thoughtTimer <= 0) {
    const persona = content.personas[npc.id];
    const thoughts = persona?.thought_bubbles || [];
    if (thoughts.length > 0) {
      npc.thought = thoughts[Math.floor(world.rng() * thoughts.length)];
    }
    npc.thoughtTimer = 8 + world.rng() * 6;
  }

  // NPC-NPC cooldown decay
  if (npc.npcNpcCooldown > 0) npc.npcNpcCooldown -= dtSec * 1000;
}

// ─────────────────────────────────────────────────────────────────────────────
// MEMORY EXTRACTION (deterministic regex)
// ─────────────────────────────────────────────────────────────────────────────

function extractFacts(text) {
  const facts = [];
  const lower = text.toLowerCase();

  // Detect "N weeks"
  const weeksMatch = lower.match(/\b(\d+)\s*weeks?\b/);
  if (weeksMatch) {
    facts.push(`Timeline: ${weeksMatch[1]} weeks`);
  } else if (lower.includes("two weeks")) {
    facts.push("Timeline: 2 weeks");
  }

  // Detect name: "my name is X" or "I am X"
  const nameMatch = text.match(/(?:my name is|I am)\s+([A-Z][a-zA-Z]{1,20})/i);
  if (nameMatch) {
    facts.push(`Player name: ${nameMatch[1]}`);
  }

  return facts;
}

// ─────────────────────────────────────────────────────────────────────────────
// NPC-NPC TRIGGERS
// ─────────────────────────────────────────────────────────────────────────────

function checkNPCNPCTriggers(world, content, broadcast) {
  const npcs = world.npcs;

  // Map NPC IDs to roles
  const npcRoles = {};
  for (const npcId of ["emma", "olivia", "alex"]) {
    const persona = content.personas[npcId];
    npcRoles[npcId] = persona?.role?.toLowerCase() || npcId;
  }

  // Role-based pair mappings (from content/street1.lines.json)
  const roleKeyMap = {
    "research__orchestrator": ["emma", "olivia"],
    "orchestrator__social": ["olivia", "alex"],
    "social__research": ["alex", "emma"],
  };

  for (const [roleKey, [aId, bId]] of Object.entries(roleKeyMap)) {
    const a = npcs.find((n) => n.id === aId);
    const b = npcs.find((n) => n.id === bId);
    if (!a || !b) continue;

    // Check mode (don't interrupt)
    if (a.mode !== "IDLE" && a.mode !== "WALKING") continue;
    if (b.mode !== "IDLE" && b.mode !== "WALKING") continue;

    // Check cooldown
    if (a.npcNpcCooldown > 0 || b.npcNpcCooldown > 0) continue;

    // Check distance
    const dx = a.x - b.x;
    const dy = a.y - b.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist > 1.5) continue;

    // Trigger exchange
    const script = content.lines?.npc_npc_dialogue?.[roleKey];
    if (!script || !script.lines) continue;

    a.npcNpcCooldown = 60000;
    b.npcNpcCooldown = 60000;

    // Emit each line with delay
    let delay = 0;
    for (const line of script.lines) {
      setTimeout(() => {
        // ── HELEN: log NPC-NPC autonomous trigger ────────────────────────────
        logger.onNpcNpcTrigger(aId, bId, line.text);
        // ─────────────────────────────────────────────────────────────────────
        broadcast({
          type: "S_NPC_NPC_DIALOGUE",
          speaker: line.speaker,
          text: line.text,
          timestamp: Date.now(),
        });
      }, delay);
      delay += 1800;
    }
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// MEMORY CONTEXT BUILDING
// ─────────────────────────────────────────────────────────────────────────────

function buildMemoryContext(world, content, npcId, userMessage) {
  const mem = world.sessionMemory;
  const persona = content.personas[npcId] || {};
  const parts = [];

  parts.push(`You are ${npcId}.`);
  parts.push(persona.persona || "");
  if (persona.voiceRules && Array.isArray(persona.voiceRules)) {
    parts.push(`Voice rules: ${persona.voiceRules.join("; ")}`);
  }

  if (mem.facts.length > 0) {
    parts.push(`\nKnown facts:\n${mem.facts.join("\n")}`);
  }

  if (mem.history && mem.history.length > 0) {
    const recent = mem.history.slice(-2);
    parts.push(
      `\nRecent:\n${recent
        .map((h) => `Player: ${h.user}\n${npcId}: ${h.reply}`)
        .join("\n")}`
    );
  }

  parts.push(`\nPlayer: ${userMessage}`);
  parts.push(`\nReply in character, concise.`);

  return parts.join("\n");
}

// ─────────────────────────────────────────────────────────────────────────────
// LLM DIALOGUE (deterministic fallback when no API key)
// ─────────────────────────────────────────────────────────────────────────────

async function getLLMReply(world, content, npcId, userMessage) {
  const OPENAI_KEY = process.env.OPENAI_API_KEY;

  // Fallback: deterministic response (when no OpenAI key)
  if (!OPENAI_KEY || OPENAI_KEY === "sk-your-api-key-here") {
    const persona = content.personas[npcId] || {};
    const mem = world.sessionMemory;

    // Check for extracted facts first
    let reply = null;
    if (mem.facts.length > 0) {
      const timelineFact = mem.facts.find((f) => f.includes("Timeline"));
      const nameFact = mem.facts.find((f) => f.includes("name"));

      if (npcId === "olivia" && timelineFact) {
        reply = `I see you mentioned ${timelineFact.toLowerCase()}. I will scope the plan accordingly.`;
      } else if (npcId === "emma" && timelineFact) {
        reply = `${timelineFact} is locked. What are the acceptance criteria?`;
      } else if (npcId === "alex" && nameFact) {
        reply = `Understood. I will remember you.`;
      }
    }

    // If no memory-based reply, use a generic response
    if (!reply) {
      const lines =
        content.lines?.npc_dialogue_banks?.[npcId]?.player_initiated || [];
      reply = lines.length > 0 ? lines[0] : persona.cachedGreeting || "Hello.";
    }

    return { ok: true, text: reply, fallback: true };
  }

  // Real LLM call (with timeout)
  const prompt = buildMemoryContext(world, content, npcId, userMessage);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), CHAT_HARD_TIMEOUT_MS);

  try {
    const resp = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${OPENAI_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: process.env.OPENAI_MODEL || "gpt-4o-mini",
        messages: [{ role: "user", content: prompt }],
        max_tokens: 120,
        temperature: 0.7,
      }),
      signal: controller.signal,
    });
    clearTimeout(timeout);

    if (!resp.ok) {
      const err = await resp.text();
      console.error("[LLM] API error:", err);
      throw new Error("API error");
    }

    const data = await resp.json();
    const text = data.choices?.[0]?.message?.content?.trim();
    return {
      ok: true,
      text: text || "I need a moment to think.",
      fallback: false,
    };
  } catch (err) {
    clearTimeout(timeout);
    const persona = content.personas[npcId] || {};
    const fallbackLines =
      content.lines?.npc_dialogue_banks?.[npcId]?.player_initiated || [];
    const fb =
      fallbackLines[0] ||
      content.lines?.default_fallbacks?.timeout_reply ||
      "Sorry, I lost my train of thought.";
    return {
      ok: false,
      text: fb,
      fallback: true,
      reason: err.name === "AbortError" ? "timeout" : "error",
    };
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// EXPRESS + WS SERVER
// ─────────────────────────────────────────────────────────────────────────────

const app = express();

app.get("/", (_req, res) => {
  res.sendFile(HTML_PATH);
});

app.use("/content", express.static(CONTENT_DIR));

const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

let content = loadContent();
let world = makeWorld(42, content);
let clients = new Set();

console.log("[Street1] Content loaded:");
console.log(`  - Grid: ${world.grid.width}×${world.grid.height}`);
console.log(`  - NPCs: ${world.npcs.map((n) => n.id).join(", ")}`);
console.log(`  - Buildings: ${world.buildings.length}`);

// ─────────────────────────────────────────────────────────────────────────────
// SNAPSHOT & DELTA
// ─────────────────────────────────────────────────────────────────────────────

function snapshot() {
  return {
    type: "S_WORLD_SNAPSHOT",
    seed: world.seed,
    tick: world.tick,
    grid: world.grid,
    buildings: world.buildings,
    player: world.player,
    npcs: world.npcs.map((n) => ({
      id: n.id,
      x: n.x,
      y: n.y,
      mode: n.mode,
      thought: n.thought,
    })),
  };
}

function delta() {
  return {
    type: "S_WORLD_DELTA",
    tick: world.tick,
    npcs: world.npcs.map((n) => ({
      id: n.id,
      x: n.x,
      y: n.y,
      mode: n.mode,
      thought: n.thought,
    })),
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// WS HANDLERS
// ─────────────────────────────────────────────────────────────────────────────

wss.on("connection", (ws) => {
  clients.add(ws);
  console.log(`[WS] Client connected (total: ${clients.size})`);

  // Send full snapshot on connect
  ws.send(JSON.stringify(snapshot()));

  ws.on("message", async (raw) => {
    let msg;
    try {
      msg = JSON.parse(raw.toString("utf-8"));
    } catch {
      ws.send(JSON.stringify({ type: "S_ERROR", message: "Invalid JSON" }));
      return;
    }

    switch (msg.type) {
      case "C_HELLO":
        ws.send(JSON.stringify(snapshot()));
        break;

      case "C_RESET_RUN": {
        const seed = msg.seed ?? 42;
        content = loadContent();
        world = makeWorld(seed, content);
        // ── HELEN: conscious ledger ───────────────────────────────────────────
        logger.onResetRun(seed);
        // Capture initial NPC positions for determinism proof (same seed → same hash)
        const initPositions = {};
        for (const npc of world.npcs) initPositions[npc.id] = { x: npc.x, y: npc.y };
        logger.onInitialPositions(seed, initPositions);
        // ─────────────────────────────────────────────────────────────────────
        broadcast(snapshot());
        console.log(`[Sim] Reset to seed=${seed}`);
        break;
      }

      case "C_NPC_CLICK": {
        const npc = world.npcs.find((n) => n.id === msg.npcId);
        if (!npc) break;

        npc.mode = "TALKING";
        npc.thought = "Listening...";
        broadcast({
          type: "S_NPC_MODE",
          npcId: npc.id,
          mode: "TALKING",
          thought: "Listening...",
        });

        // Send cached first line instantly
        const persona = content.personas[npc.id] || {};
        const cachedLine = persona.cachedGreeting || "Hello.";
        setTimeout(() => {
          broadcast({
            type: "S_NPC_DIALOGUE",
            npcId: npc.id,
            text: cachedLine,
            cached: true,
          });
        }, 80);

        break;
      }

      case "C_CHAT_SEND": {
        const npc = world.npcs.find((n) => n.id === msg.npcId);
        if (!npc) break;
        if (world.activeLLM[msg.npcId]) break; // de-dup

        const userText = (msg.text || "").trim().slice(0, 200);
        if (!userText) break;

        // ── HELEN: log incoming user message ─────────────────────────────────
        logger.onChatSend(msg.npcId, userText);
        // ─────────────────────────────────────────────────────────────────────

        // Extract facts into session memory
        const newFacts = extractFacts(userText);
        world.sessionMemory.facts.push(...newFacts);

        // ── HELEN: log memory extraction ──────────────────────────────────────
        logger.onMemoryExtract(newFacts, userText);
        // ─────────────────────────────────────────────────────────────────────

        // Set THINKING mode immediately
        npc.mode = "THINKING";
        npc.thought = "Thinking...";
        broadcast({
          type: "S_NPC_MODE",
          npcId: npc.id,
          mode: "THINKING",
          thought: "Thinking...",
        });

        // Fire LLM async — never blocks tick
        world.activeLLM[msg.npcId] = true;
        console.log(`[Chat] ${msg.npcId} received: "${userText}"`);
        console.log(`[Chat] Facts before LLM: ${JSON.stringify(world.sessionMemory.facts)}`);

        getLLMReply(world, content, msg.npcId, userText)
          .then((result) => {
            world.activeLLM[msg.npcId] = false;
            console.log(`[Chat] ${msg.npcId} reply: "${result.text}" (fallback=${result.fallback})`);

            // Store in history
            if (!world.sessionMemory.history) world.sessionMemory.history = [];
            world.sessionMemory.history.push({
              user: userText,
              reply: result.text,
            });
            if (world.sessionMemory.history.length > 20)
              world.sessionMemory.history.shift();

            // Return to IDLE
            npc.mode = "IDLE";
            npc.thought = "";

            // ── HELEN: log NPC reply ──────────────────────────────────────────
            const replySource = result.fallback ? "fallback" : "llm";
            logger.onNpcReply(msg.npcId, result.text, replySource);
            // ─────────────────────────────────────────────────────────────────

            broadcast({
              type: "S_NPC_DIALOGUE",
              npcId: msg.npcId,
              text: result.text,
              cached: false,
              fallback: result.fallback || false,
            });
          })
          .catch((err) => {
            world.activeLLM[msg.npcId] = false;
            npc.mode = "IDLE";
            console.error(`[Chat] ${msg.npcId} error:`, err.message);
          });

        break;
      }

      default:
        ws.send(
          JSON.stringify({
            type: "S_ERROR",
            message: `Unknown msg type: ${msg.type}`,
          })
        );
    }
  });

  ws.on("close", () => {
    clients.delete(ws);
    console.log(`[WS] Client disconnected (total: ${clients.size})`);
    // If no more clients, seal the ledger
    if (clients.size === 0) {
      try {
        const receipt = logger.onSessionEnd("DELIVER", "client_disconnect");
        console.log(`[HELEN] Session sealed on client disconnect. receipt_sha=${receipt}`);
      } catch (e) {
        console.error(`[HELEN] Seal error:`, e.message);
      }
    }
  });

  ws.on("error", (err) => {
    console.error("[WS] Error:", err.message);
    clients.delete(ws);
  });
});

function broadcast(obj) {
  const json = JSON.stringify(obj);
  for (const client of clients) {
    if (client.readyState === WebSocket.OPEN) {
      client.send(json);
    }
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// TICK LOOP
// ─────────────────────────────────────────────────────────────────────────────

let lastTickTime = Date.now();
let prevState = { npcs: world.npcs.map((n) => ({ ...n })) };

setInterval(() => {
  const now = Date.now();
  const dtSec = (now - lastTickTime) / 1000;
  lastTickTime = now;

  // Tick each NPC
  for (const npc of world.npcs) {
    tickNPC(world, npc, dtSec);
  }

  // Check NPC-NPC triggers
  checkNPCNPCTriggers(world, content, broadcast);

  world.tick++;

  // ── HELEN: update tick counter + sample world positions ──────────────────
  logger.onTick(world.tick);
  const npcPositions = {};
  for (const npc of world.npcs) npcPositions[npc.id] = { x: +npc.x.toFixed(2), y: +npc.y.toFixed(2) };
  logger.onWorldDelta(world.tick, npcPositions);
  // ─────────────────────────────────────────────────────────────────────────

  // Emit delta
  const d = delta();
  if (clients.size > 0) {
    broadcast(d);
  }
}, TICK_MS);

// ─────────────────────────────────────────────────────────────────────────────
// BOOT
// ─────────────────────────────────────────────────────────────────────────────

server.listen(PORT, () => {
  console.log(`[Street1] Running at http://localhost:${PORT}`);
  console.log(`[Street1] Open in browser now`);
  console.log(
    `[Street1] OPENAI_API_KEY: ${
      process.env.OPENAI_API_KEY
        ? "SET ✓"
        : "NOT SET (using deterministic fallback)"
    }`
  );
  console.log(`[HELEN] Ledger: ${logger.LOG_FILE}`);
});

// ── HELEN: emit session_end on clean shutdown ─────────────────────────────────
process.on("SIGINT", () => {
  try {
    const receipt = logger.onSessionEnd("DELIVER", "SIGINT_shutdown");
    console.log(`\n[HELEN] Session sealed. receipt_sha=${receipt}`);
  } catch {}
  process.exit(0);
});
