/**
 * MARKETING STREET - Backend Orchestrator
 *
 * This is the server-side component that:
 * 1. Receives session config + agent prompts from frontend
 * 2. Orchestrates 9-turn conversation (Round 1 → Round 2 → Final Synthesis)
 * 3. Enforces conversation protocol (contribution + question + action)
 * 4. Streams events back to frontend via SSE
 * 5. Exports structured JSON + Markdown deliverables
 *
 * Stack: Node.js + Express + OpenAI SDK
 */

import express from 'express';
import { OpenAI } from 'openai';
import cors from 'cors';

const app = express();
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

app.use(cors());
app.use(express.json());
app.use(express.static('public')); // Serve frontend HTML

// ═══════════════════════════════════════
// CONVERSATION PROTOCOL
// ═══════════════════════════════════════

const TURN_PROTOCOL = `
STRICT OUTPUT PROTOCOL:
You MUST structure your response with these three sections:

## CONTRIBUTION
[Your main analysis, proposal, or deliverable goes here]

## QUESTION
[Ask exactly ONE specific question to another agent - name them explicitly]

## ACTION
[State what should happen next or what you need to proceed]

This format is REQUIRED. Do not deviate from it.
`;

// ═══════════════════════════════════════
// ORCHESTRATION PLAN (9 turns)
// ═══════════════════════════════════════

const CONVERSATION_PLAN = [
  // ROUND 1: Alignment (4 turns)
  {
    agent: 'strategist',
    focus: 'Define ICP, primary pains, differentiators, and narrative spine for the product',
    round: 1
  },
  {
    agent: 'creative',
    focus: 'Propose 3-5 creative campaign angles and metaphors based on the positioning',
    round: 1
  },
  {
    agent: 'analyst',
    focus: 'Identify top 3 acquisition channels and propose 5 initial experiments with metrics',
    round: 1
  },
  {
    agent: 'compliance',
    focus: 'Review all proposals so far and flag any risky claims or ambiguous language',
    round: 1
  },

  // ROUND 2: Refinement (4 turns)
  {
    agent: 'strategist',
    focus: 'Refine positioning based on team feedback and finalize the narrative spine',
    round: 2
  },
  {
    agent: 'creative',
    focus: 'Draft landing page hero, subhead, 6 bullets, and 3 CTAs',
    round: 2
  },
  {
    agent: 'analyst',
    focus: 'Create 3 ad variants (one per top channel) with hooks and success metrics',
    round: 2
  },
  {
    agent: 'compliance',
    focus: 'Final compliance pass - edit all copy for safety and create risk table',
    round: 2
  },

  // FINAL: Synthesis (1 turn)
  {
    agent: 'strategist',
    focus: 'Compile final 1-page brief with all deliverables in structured JSON format',
    round: 3,
    finalSynthesis: true
  }
];

// ═══════════════════════════════════════
// LOCKED OPERATING RULES (per agent)
// ═══════════════════════════════════════

const OPERATING_RULES = {
  strategist: `
• Use concrete language - avoid "revolutionary", "game-changing", "innovative"
• Make all assumptions explicit
• Cite what evidence you need
• When disagreeing, propose specific alternatives
• Reference previous turns when building on ideas
`,
  creative: `
• Be bold but concrete - provide visual motifs and metaphors
• Every creative concept must have a clear rationale
• Propose multiple variants when uncertain
• Balance novelty with clarity
• Flag when you need more context
`,
  analyst: `
• Prioritize ruthlessly - rank everything by expected impact
• Every metric must have a success threshold
• Make ROI assumptions explicit
• Challenge vanity metrics
• Flag data dependencies
`,
  compliance: `
• NEVER delete ideas - only rewrite into safer versions
• Explain risk level (low/medium/high) for each flag
• Preserve marketing intent while reducing legal risk
• Propose concrete alternatives, never just "no"
• Check for: security claims, performance guarantees, ambiguous language
`
};

// ═══════════════════════════════════════
// DEFAULT AGENT PROMPTS (user-editable)
// ═══════════════════════════════════════

const DEFAULT_AGENT_PROMPTS = {
  strategist: `You are the Positioning Strategist in a 4-agent marketing team.

Your job: Define ICP, primary pain points, differentiated value proposition, and narrative spine.

Output requirements:
- ICP: specific role, company profile, current state
- 3 Primary Pains: concrete, relatable problems (not generic)
- 3 Differentiators: specific, defensible advantages
- One-liner: max 15 words
- 30-word pitch: exactly 30 words
- Proof points needed: list what evidence would make this compelling

Constraints:
- Avoid hype words: "revolutionary", "innovative", "game-changing"
- Make assumptions explicit
- Be specific about who this is NOT for`,

  creative: `You are the Creative Director in a 4-agent marketing team.

Your job: Develop creative campaign angles, metaphors, and messaging that brings the positioning to life.

Output requirements:
- 3-5 campaign concepts with rationale
- 5-10 hook lines/taglines
- Visual motifs and metaphors
- Emotional angle (what feeling should dominate?)
- Channel-specific adaptations

Constraints:
- Bold but concrete (no vague "storytelling" - show actual stories)
- Every concept must ladder back to the positioning
- Provide context for why each angle works`,

  analyst: `You are the Performance Marketing Analyst in a 4-agent marketing team.

Your job: Propose acquisition plan with experiments, metrics, and ROI assumptions.

Output requirements:
- Top 3 channels ONLY (ranked with rationale)
- 5 experiments (hypothesis, metric, expected effect size, timeline)
- Success criteria (what "good" looks like)
- ROI assumptions (CAC, LTV, conversion rates)
- Measurement plan (tools and tracking)

Constraints:
- Ruthlessly prioritize - explain why you're NOT doing other channels
- Every metric needs a threshold (what number = success?)
- Flag dependencies (what needs to be true for this to work?)`,

  compliance: `You are the Brand & Compliance Editor in a 4-agent marketing team.

Your job: Ensure all messaging is clear, consistent, and legally safe.

Output requirements:
- Risk table: [original claim → risk level → safer alternative]
- Edited copy with all changes tracked
- Flagged issues with severity ratings
- Brand voice consistency notes

Constraints:
- Do NOT delete ideas - rewrite them into testable, verifiable language
- Flag these claim types: security, performance, "first/only/best", guarantees
- Provide safer alternatives that preserve marketing intent
- Explain WHY something is risky (teach the team)`
};

// ═══════════════════════════════════════
// STRUCTURED OUTPUT SCHEMA
// ═══════════════════════════════════════

const DELIVERABLE_SCHEMA = {
  positioning: {
    icp: "string",
    primaryPains: ["string", "string", "string"],
    differentiators: ["string", "string", "string"],
    oneLiner: "string",
    thirtyWordPitch: "string",
    proofPointsNeeded: ["string"]
  },
  landingPage: {
    hero: "string",
    subhead: "string",
    bullets: ["string", "string", "string", "string", "string", "string"],
    ctas: ["string", "string", "string"]
  },
  adVariants: [
    {
      channel: "string",
      headline: "string",
      body: "string",
      cta: "string",
      hook: "string"
    }
  ],
  experimentPlan: [
    {
      hypothesis: "string",
      metric: "string",
      successCriteria: "string",
      timeline: "string"
    }
  ],
  riskTable: [
    {
      originalClaim: "string",
      riskLevel: "string",
      saferAlternative: "string"
    }
  ],
  brief: "string"
};

// ═══════════════════════════════════════
// SESSION ENDPOINT (SSE)
// ═══════════════════════════════════════

app.post('/api/run-session', async (req, res) => {
  // Set up SSE
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  const { goal, audience, tone, constraints, agentPrompts } = req.body;

  // Use provided prompts or defaults
  const prompts = {
    strategist: agentPrompts?.strategist || DEFAULT_AGENT_PROMPTS.strategist,
    creative: agentPrompts?.creative || DEFAULT_AGENT_PROMPTS.creative,
    analyst: agentPrompts?.analyst || DEFAULT_AGENT_PROMPTS.analyst,
    compliance: agentPrompts?.compliance || DEFAULT_AGENT_PROMPTS.compliance
  };

  // Session state
  const conversationHistory = [];
  const deliverables = {};

  // Send event helper
  const sendEvent = (event, data) => {
    res.write(`event: ${event}\n`);
    res.write(`data: ${JSON.stringify(data)}\n\n`);
  };

  try {
    sendEvent('session-start', {
      totalTurns: CONVERSATION_PLAN.length,
      goal,
      audience,
      tone,
      constraints
    });

    // Execute conversation plan
    for (let i = 0; i < CONVERSATION_PLAN.length; i++) {
      const turn = CONVERSATION_PLAN[i];
      const turnNumber = i + 1;

      sendEvent('turn-start', {
        turnNumber,
        agent: turn.agent,
        focus: turn.focus,
        round: turn.round
      });

      // Build context
      const sessionContext = `
SESSION CONFIGURATION:
Goal: ${goal}
Audience: ${audience}
Tone: ${tone}
Constraints: ${constraints}

CURRENT TASK (Turn ${turnNumber}, Round ${turn.round}):
${turn.focus}
      `.trim();

      // Build conversation history for context
      const previousTurns = conversationHistory
        .map(h => `[${h.agent.toUpperCase()}]\n${h.response}`)
        .join('\n\n---\n\n');

      const fullContext = previousTurns
        ? `${sessionContext}\n\n---\n\nPREVIOUS DISCUSSION:\n${previousTurns}`
        : sessionContext;

      // Call LLM
      const response = await callAgent(
        turn.agent,
        prompts[turn.agent],
        OPERATING_RULES[turn.agent],
        fullContext,
        turn.finalSynthesis
      );

      // Log turn
      conversationHistory.push({
        turnNumber,
        agent: turn.agent,
        focus: turn.focus,
        response: response.fullText,
        parsed: response.parsed
      });

      // Send response to frontend
      sendEvent('turn-complete', {
        turnNumber,
        agent: turn.agent,
        contribution: response.parsed.contribution,
        question: response.parsed.question,
        action: response.parsed.action,
        fullText: response.fullText
      });

      // Extract deliverables on specific turns
      if (turn.finalSynthesis) {
        // Final synthesis - extract structured JSON
        deliverables.final = response.parsed;
      }
    }

    // Generate final export
    const exportPackage = {
      meta: {
        timestamp: new Date().toISOString(),
        goal,
        audience,
        tone,
        constraints
      },
      conversation: conversationHistory,
      deliverables: deliverables.final || extractDeliverables(conversationHistory),
      agentPrompts: prompts
    };

    sendEvent('session-complete', exportPackage);

  } catch (error) {
    sendEvent('error', { message: error.message, stack: error.stack });
  } finally {
    res.end();
  }
});

// ═══════════════════════════════════════
// LLM CALL FUNCTION
// ═══════════════════════════════════════

async function callAgent(agentKey, systemPrompt, operatingRules, context, isFinalSynthesis = false) {
  const finalSynthesisInstruction = isFinalSynthesis ? `

FINAL SYNTHESIS TASK:
You are compiling the final deliverables. After your standard CONTRIBUTION/QUESTION/ACTION sections,
you MUST also include a JSON block with this exact structure:

\`\`\`json
{
  "positioning": {
    "icp": "...",
    "primaryPains": ["...", "...", "..."],
    "differentiators": ["...", "...", "..."],
    "oneLiner": "...",
    "thirtyWordPitch": "...",
    "proofPointsNeeded": ["..."]
  },
  "landingPage": {
    "hero": "...",
    "subhead": "...",
    "bullets": ["...", "...", "...", "...", "...", "..."],
    "ctas": ["...", "...", "..."]
  },
  "adVariants": [
    { "channel": "...", "headline": "...", "body": "...", "cta": "...", "hook": "..." }
  ],
  "experimentPlan": [
    { "hypothesis": "...", "metric": "...", "successCriteria": "...", "timeline": "..." }
  ],
  "riskTable": [
    { "originalClaim": "...", "riskLevel": "...", "saferAlternative": "..." }
  ],
  "brief": "..."
}
\`\`\`

Extract this from the full conversation history.
` : '';

  const fullSystemPrompt = `${systemPrompt}

${operatingRules}

${TURN_PROTOCOL}${finalSynthesisInstruction}`;

  const completion = await openai.chat.completions.create({
    model: 'gpt-4-turbo-preview',
    messages: [
      { role: 'system', content: fullSystemPrompt },
      { role: 'user', content: context }
    ],
    temperature: 0.7,
    max_tokens: 1500
  });

  const responseText = completion.choices[0].message.content;

  // Parse response
  const parsed = parseAgentResponse(responseText);

  return {
    fullText: responseText,
    parsed
  };
}

// ═══════════════════════════════════════
// RESPONSE PARSER
// ═══════════════════════════════════════

function parseAgentResponse(text) {
  const sections = {
    contribution: '',
    question: '',
    action: '',
    json: null
  };

  // Extract sections
  const contributionMatch = text.match(/##\s*CONTRIBUTION\s*\n([\s\S]*?)(?=##\s*QUESTION|$)/i);
  const questionMatch = text.match(/##\s*QUESTION\s*\n([\s\S]*?)(?=##\s*ACTION|$)/i);
  const actionMatch = text.match(/##\s*ACTION\s*\n([\s\S]*?)(?=```json|$)/i);
  const jsonMatch = text.match(/```json\s*\n([\s\S]*?)\n```/);

  if (contributionMatch) sections.contribution = contributionMatch[1].trim();
  if (questionMatch) sections.question = questionMatch[1].trim();
  if (actionMatch) sections.action = actionMatch[1].trim();

  if (jsonMatch) {
    try {
      sections.json = JSON.parse(jsonMatch[1]);
    } catch (e) {
      console.error('Failed to parse JSON deliverables:', e);
    }
  }

  return sections;
}

// ═══════════════════════════════════════
// DELIVERABLE EXTRACTION (fallback)
// ═══════════════════════════════════════

function extractDeliverables(conversationHistory) {
  // If final synthesis didn't produce JSON, extract from conversation
  // This is a fallback - in production, enforce JSON in final turn

  const deliverables = {
    positioning: {},
    landingPage: {},
    adVariants: [],
    experimentPlan: [],
    riskTable: [],
    brief: "See full conversation for details."
  };

  // Look for structured data in any agent's final contribution
  const finalTurn = conversationHistory[conversationHistory.length - 1];
  if (finalTurn?.parsed?.json) {
    return finalTurn.parsed.json;
  }

  return deliverables;
}

// ═══════════════════════════════════════
// EXPORT ENDPOINT
// ═══════════════════════════════════════

app.post('/api/export', async (req, res) => {
  const { exportPackage } = req.body;

  // Generate Markdown
  let markdown = `# Marketing Street Session Export\n\n`;
  markdown += `**Generated:** ${exportPackage.meta.timestamp}\n\n`;
  markdown += `---\n\n`;

  markdown += `## Session Configuration\n\n`;
  markdown += `- **Goal:** ${exportPackage.meta.goal}\n`;
  markdown += `- **Audience:** ${exportPackage.meta.audience}\n`;
  markdown += `- **Tone:** ${exportPackage.meta.tone}\n`;
  markdown += `- **Constraints:** ${exportPackage.meta.constraints}\n\n`;
  markdown += `---\n\n`;

  markdown += `## Conversation Transcript\n\n`;
  exportPackage.conversation.forEach(turn => {
    markdown += `### Turn ${turn.turnNumber}: ${turn.agent.toUpperCase()}\n\n`;
    markdown += `**Focus:** ${turn.focus}\n\n`;
    markdown += `${turn.response}\n\n`;
    markdown += `---\n\n`;
  });

  markdown += `## Deliverables\n\n`;
  markdown += `\`\`\`json\n${JSON.stringify(exportPackage.deliverables, null, 2)}\n\`\`\`\n\n`;

  res.json({
    markdown,
    json: exportPackage
  });
});

// ═══════════════════════════════════════
// HEALTH CHECK
// ═══════════════════════════════════════

app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    model: 'gpt-4-turbo-preview'
  });
});

// ═══════════════════════════════════════
// START SERVER
// ═══════════════════════════════════════

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`
╔═══════════════════════════════════════╗
║   MARKETING STREET • Backend Ready    ║
╚═══════════════════════════════════════╝

Server running on http://localhost:${PORT}
API endpoint: /api/run-session
Health check: /api/health

Environment:
- OpenAI API Key: ${process.env.OPENAI_API_KEY ? '✓ Set' : '✗ Missing'}
- Model: gpt-4-turbo-preview
- Protocol: SSE (Server-Sent Events)

Ready to orchestrate 9-turn marketing discussions.
  `);
});

export default app;
