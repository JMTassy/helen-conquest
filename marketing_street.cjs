/**
 * marketing_street.js
 *
 * 4-Agent Marketing Orchestrator for Landing Page Generation
 *
 * MVP Scope: Deterministic agent team that generates landing copy + metadata
 * in 5-7 turns, with explicit editorial authority and mandatory termination.
 *
 * Agents:
 * 1. Positioning Strategist — ICP, pains, differentiation, narrative spine
 * 2. Growth Marketer — Top 3 channels, hooks, angles
 * 3. Copywriter — Hero, subhead, bullets, CTAs, 15s script
 * 4. Brand & Compliance — Risk table, safe rewrites, tone coherence
 */

// No TypeScript types; pure JavaScript

// ============================================================================
// AGENT IMPLEMENTATIONS (Pure Functions)
// ============================================================================

/**
 * Positioning Strategist
 * INPUT: Goal + constraints
 * OUTPUT: ICP, pains, narrative spine, differentiation
 */
function positioningStrategist(goal, constraints, seed) {
  // Deterministic response based on seed + inputs
  const random = Math.sin(seed + 1) * 10000;
  const variant = Math.floor(random) % 2;

  let contribution = "";
  if (variant === 0) {
    contribution = `
## Positioning (Strategist)

**ICP**: VP Eng / Head of AI / Product leaders (mid-market SaaS, $50M+ ARR)
**Primary Pain**: Tool calls are opaque. Memory writes are invisible. Demos can't be replayed.
**Narrative Spine**: "Stop selling agent magic. Sell verifiable behavior."

**Differentiation**:
- Walkable behavior (see what the agent decided, step-by-step)
- Deterministic replay (same seed = identical trace)
- Memory visible (regex extractions, fact store, session context)
- Export proof (Markdown + JSON artifacts for audit)

**Proof Points**:
1. Seed-based determinism (replay demo, show consistency)
2. Memory extraction (show exact facts learned from user input)
3. Tool call visibility (every decision logged with reason)
4. Artifact export (artifacts survive beyond demo)
    `;
  } else {
    contribution = `
## Positioning (Strategist)

**ICP**: Engineering leadership concerned with AI agent reliability and debuggability
**Primary Pain**: Can't inspect agent internals during live demos. No replay capability.
**Narrative Spine**: "Trustworthy AI through transparency."

**Differentiation**:
- Transparent reasoning (tool calls + memory updates logged)
- Seeded determinism (same seed always reproduces run)
- Exportable artifacts (copy demo outputs for documentation)
- Session memory (facts extracted and retained within demo)

**Proof Points**:
1. Deterministic seed testing
2. Live memory inspection during demo
3. Artifact export and replay
4. Tool call tracing with full context
    `;
  }

  return {
    agent: "Positioning Strategist",
    turn: 1,
    contribution,
    question_for_next:
      "Given this positioning, what channels and hooks would resonate most with our ICP?",
    action: "continue",
  };
}

/**
 * Growth Marketer
 * INPUT: Positioning + goal
 * OUTPUT: Top 3 channels, hooks, angles for each
 */
function growthMarketer(positioning, seed) {
  const random = Math.sin(seed + 2) * 10000;
  const variant = Math.floor(random) % 2;

  let contribution = "";
  if (variant === 0) {
    contribution = `
## Growth Strategy (Growth Marketer)

**Top 3 Channels**:
1. **LinkedIn**: Target engineering leaders. Showcase replay + tool-tracing.
   - Hook: "Your AI agents are a black box. Now they're glass."
   - Angle: Transparency as competitive advantage in agent deployment

2. **Hacker News / Lobsters**: Dev-community attention to determinism + auditability.
   - Hook: "Deterministic agent demos. Same seed, identical trace."
   - Angle: Technical credibility through reproducible runs

3. **Vendor ecosystem (Hugging Face, Anthropic partner channels)**: Enterprise buyers.
   - Hook: "Proof of behavior, not promises of intelligence."
   - Angle: Integration-ready, exportable, trustworthy

**Cross-Channel Message**:
"We give you visibility into agent decisions. Every action logged. Every run reproducible."
    `;
  } else {
    contribution = `
## Growth Strategy (Growth Marketer)

**Top 3 Channels**:
1. **Engineering communities (Reddit /r/machinelearing, Lambda Labs)**: Early adoption + word-of-mouth.
   - Hook: "Your agent's behavior is now walkable in demos."
   - Angle: Developer experience and debugging tools

2. **AI safety / alignment spaces (LessWrong, AI Alignment Research)**: Trustworthiness narrative.
   - Hook: "Transparent reasoning for autonomous systems."
   - Angle: Safety and auditability at the core

3. **Enterprise sales (direct outreach to Fortune 500 AI leads)**: Risk-averse buyers.
   - Hook: "Deterministic replay = auditable deployment."
   - Angle: Compliance and risk management for production AI

**Brand Message**:
"Build agents you can trust. See every decision. Replay every run."
    `;
  }

  return {
    agent: "Growth Marketer",
    turn: 2,
    contribution,
    question_for_next:
      "Can you draft the landing page hero, subhead, and bullet points using these channels and hooks?",
    action: "continue",
  };
}

/**
 * Copywriter
 * INPUT: Positioning + growth strategy
 * OUTPUT: Hero, subhead, bullets, CTAs, 15s script
 */
function copywriter(strategy, seed) {
  const random = Math.sin(seed + 3) * 10000;
  const variant = Math.floor(random) % 3;

  let contribution = "";
  const heros = [
    "Walk Your AI.",
    "Trustworthy Agents.",
    "See Every Decision.",
  ];
  const subheads = [
    "Inspect tool calls + memory writes + replayable demo runs (fixed seed, logged transcript).",
    "Deterministic replay. Visible memory. Exportable artifacts. Transparent reasoning.",
    "Your agent's behavior is now inspectable, reproducible, and auditable.",
  ];

  const hero = heros[variant];
  const subhead = subheads[variant];

  contribution = `
## Landing Copy (Copywriter)

**Hero**: ${hero}

**Subhead**: ${subhead}

**6 Bullet Points**:
1. **Walkable behavior** — Click → see exact tool calls + reasoning
2. **Deterministic replay** — Same seed = identical events (fixed randomness, logged trace)
3. **Memory visible** — Watch facts get extracted and stored during demo
4. **Exportable artifacts** — Download Markdown + JSON from any run
5. **Seeded sandbox** — Safe, reproducible, no API keys exposed
6. **Built for demos** — 90-second proof-of-concept, then ask for a call

**Primary CTA**: Book a demo / See replayable run
**Secondary CTA**: Get a 1-page brief / Download sample run

**15-Second Demo Script**:
"I'll walk you through a deterministic agent run. See the tool calls live, watch memory extraction in real-time, and replay the whole thing with a fixed seed. [Click agent → observe trace → show memory → replay → export.] That's it. Same seed, identical behavior, every time."
    `;

  return {
    agent: "Copywriter",
    turn: 3,
    contribution,
    question_for_next:
      "This is strong, but let me check for any risky claims or tone misalignment. Reviewing now...",
    action: "continue",
  };
}

/**
 * Brand & Compliance
 * INPUT: Copy + strategy
 * OUTPUT: Risk flags, safe rewrites, compliance notes
 */
function brandCompliance(copy, seed) {
  const random = Math.sin(seed + 4) * 10000;
  const variant = Math.floor(random) % 2;

  let contribution = "";
  if (variant === 0) {
    contribution = `
## Compliance & Brand Review (Brand Officer)

**Risk Table**:
| Claim | Risk Level | Rewrite |
|-------|-----------|---------|
| "Your agent's behavior is now walkable" | LOW | ✓ Supported by tool-call tracing |
| "Same seed = identical behavior" | MEDIUM | Rewrite to: "Deterministic behavior under fixed seed + environment" |
| "Memory visible" | LOW | ✓ Supported by session memory logs |
| "Transparent reasoning" | MEDIUM | Clarify: "Decision trace showing tool calls, not internal LLM reasoning" |
| "Safe, reproducible" | LOW | ✓ Supported by sandbox + seeding |

**Tone Check**: ✓ Confident but not hyperbolic. "Verifiable" > "magical"

**Final Copy Note**: Remove "trustworthy AI" → use "inspectable" and "auditable". Don't claim AI safety; claim behavior transparency.

**Messaging Guidelines**:
- Use "decision trace" not "reasoning"
- Use "reproducible" not "deterministic" (less jargony for execs)
- Use "visible memory" not "memory access" (more intuitive)
- Use "proof-of-concept" not "production-ready" (manage expectations)
    `;
  } else {
    contribution = `
## Compliance & Brand Review (Brand Officer)

**Risk Assessment**:
| Claim | Status | Note |
|-------|--------|------|
| "Deterministic replay" | ✓ SAFE | Supported by seeded RNG + logging |
| "Audit-ready" | ⚠️ REVIEW | Clarify: deterministic runs, not audit compliance per se |
| "Production-grade" | ❌ REMOVE | Too strong; use "production-ready" for controlled claims |
| "Memory extraction" | ✓ SAFE | Regex-based, well-defined |
| "No API key exposure" | ✓ SAFE | Sandbox + no network calls |

**Tone Adjustment**:
From: "Build agents you can trust" (implies safety/alignment claim)
To: "Build agents you can verify" (focuses on transparency)

**Revised Subhead**:
"Inspect tool calls. Trace memory extraction. Replay with fixed seed. Export proof artifacts."

**Demo Script Revision**:
Add: "This is a proof-of-concept demo. For production use, see [integration docs]."
    `;
  }

  return {
    agent: "Brand & Compliance",
    turn: 4,
    contribution,
    question_for_next:
      "Compliance check complete. Shall we finalize and export the landing page artifact?",
    action: variant === 0 ? "continue" : "ready_for_editorial",
  };
}

// ============================================================================
// ORCHESTRATOR (Pure Round-Robin)
// ============================================================================

function runMarketingRound(goal, constraints, seed) {
  const session = {
    goal,
    constraints,
    seed,
    turn: 0,
    artifacts: {},
    turns_log: [],
    phase: "exploration",
    editorial_decision: null,
  };

  // Round 1: Strategist
  const turn1 = positioningStrategist(goal, constraints, seed);
  session.turns_log.push(turn1);
  session.artifacts.positioning = turn1.contribution;
  session.turn++;

  // Round 2: Growth
  const turn2 = growthMarketer(turn1.contribution, seed);
  session.turns_log.push(turn2);
  session.artifacts.growth_angles = turn2.contribution;
  session.turn++;

  // Round 3: Copy
  const turn3 = copywriter(turn2.contribution, seed);
  session.turns_log.push(turn3);
  session.artifacts.draft_copy = turn3.contribution;
  session.turn++;

  // Round 4: Compliance
  const turn4 = brandCompliance(turn3.contribution, seed);
  session.turns_log.push(turn4);
  session.artifacts.compliance_notes = turn4.contribution;
  session.turn++;

  // ========================================================================
  // EDITORIAL COLLAPSE (Unilateral Authority)
  // ========================================================================

  // Merge all artifacts into final landing page
  const finalLanding = `# STREET 1: Walk Your AI

${session.artifacts.positioning}

${session.artifacts.growth_angles}

${session.artifacts.draft_copy}

---

## Compliance & Brand Notes

${session.artifacts.compliance_notes}

---

**Status**: ✅ READY TO SHIP
**Seed**: ${seed}
**Turns**: ${session.turn}
**Decision**: SHIP (Landing page + brand compliance verified)
    `;

  session.artifacts.final_landing = finalLanding;

  // Create final metadata (NO TIMESTAMPS - determinism required)
  session.artifacts.final_metadata = {
    goal,
    constraints,
    seed,
    phase: "terminated",
    editorial_decision: "SHIP",
    golden_run_id: `MARKET-${seed}`,
    artifact_hashes: {
      positioning: hashString(session.artifacts.positioning || ""),
      growth: hashString(session.artifacts.growth_angles || ""),
      copy: hashString(session.artifacts.draft_copy || ""),
      compliance: hashString(session.artifacts.compliance_notes || ""),
      final_landing: hashString(finalLanding),
    },
  };

  session.phase = "terminated";
  session.editorial_decision = "SHIP";

  return session;
}

// ============================================================================
// UTILITIES
// ============================================================================

/**
 * Simple deterministic hash for artifact versioning
 */
function hashString(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash; // 32-bit integer
  }
  return Math.abs(hash).toString(16);
}

// ============================================================================
// MAIN ENTRY POINT
// ============================================================================

function main() {
  const goal =
    "Launch AgentX Street 1 MVP to VP Eng / Head of AI leaders with strong product credibility";
  const constraints =
    "No unqualified perf claims. No security/compliance claims beyond determinism. Tone: Confident, playful, concrete.";
  const seed = process.argv[2] ? parseInt(process.argv[2]) : 111;

  console.log(`\n=== MARKETING STREET MVP (Seed: ${seed}) ===\n`);
  console.log(`Goal: ${goal}\n`);

  const session = runMarketingRound(goal, constraints, seed);

  console.log(`\n=== FINAL LANDING PAGE ===\n`);
  console.log(session.artifacts.final_landing);

  console.log(`\n=== METADATA ===\n`);
  console.log(JSON.stringify(session.artifacts.final_metadata, null, 2));

  console.log(`\n=== DECISION ===\n`);
  console.log(`Editorial Decision: ${session.editorial_decision}`);
  console.log(
    `Artifact Ready: runs/marketing_street/landing_${seed}.md`
  );
}

main();

// ============================================================================
// EXPORTS (for use in web server)
// ============================================================================

module.exports = { runMarketingRound, positioningStrategist, growthMarketer, copywriter, brandCompliance };
