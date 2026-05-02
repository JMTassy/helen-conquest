# HAL_INSPIRATION_QUEUE

Non-sovereign queue of upstream agent-design patterns flagged for HAL's
later inspection. Nothing here is admitted, sealed, or promoted. HAL pulls,
reducer decides, ledger records.

Scope: `experiments/helen_mvp_kernel/` only. Off-limits paths untouched.

---

## ITEM-001 — Persistent cross-turn `/goal` loop (Hermes / Ralph pattern)

**Source**
- `NousResearch/hermes-agent` PR #18262 (merged)
- Inspired by Codex CLI 0.128.0 `/goal` (Eric Traut, Pyright/Codex team)

**Pattern (invariants to keep, code to ignore)**
1. Goal persists in session state.
2. Continuation is a normal user-role input (no system-prompt mutation).
3. Judge call after each response decides done / continue.
4. Judge failure fails OPEN (continue); turn budget is the real backstop.
5. Any real user message preempts the loop automatically.
6. `max_turns` default = 20.
7. Setting a new goal mid-run requires explicit stop (no racing two loops).

**HELEN-native shape (proposal, not admitted)**

Command name candidate: `/ralph goal` (over `/helen-goal` — keeps the
Ralph-loop lineage explicit).

Schema sketch:
```json
{
  "type": "PERSISTENT_GOAL",
  "goal": "...",
  "status": "active | paused | done | exhausted",
  "turns_used": 0,
  "max_turns": 20,
  "judge": "goal_satisfied",
  "authority": false
}
```

**Constitutional constraint (non-negotiable)**

The goal loop must remain **non-sovereign**:

```
Goal loop may PROPOSE.
Judge may CONTINUE.
Reducer still DECIDES.
Ledger still requires RECEIPTS.

/goal ≠ authority
/goal = persistence of intention
```

Implication: every continuation turn that touches a sovereign surface still
goes through `tools/helen_say.py` → `tools/ndjson_writer.py`. The judge
verdict is a non-sovereign signal, never a SHIP/NO_SHIP/BLOCK/PASS.

**Roadmap label** (if HAL admits)

```
HELEN_GOAL_LOOP_V1
Persistent cross-turn objective loop inspired by Hermes /goal and the
Ralph loop. Bounded by max_turns, judged by evaluator, preempted by user,
receipted by ledger. NON_SOVEREIGN.
```

**Status:** QUEUED, conditional on HAL pull. Not a proposal. Not admitted.
Not scheduled. Logged for later inspection only.

**Queued:** 2026-05-01

---

## ITEM-002 — `browser-use/browser-use` Python core as web-executor candidate

**Source**
- `github.com/browser-use/browser-use` (Python library, MIT)

**Explicitly NOT queued**
- `browser-use/desktop-app` — TypeScript/Electron, cloud-only LLMs (Anthropic/Codex), Mac-first packaging, no Ollama support, redundant with existing `tools/helen_telegram.py` channel.

**Mapping (proposal-class)**
```
HELEN kernel/reducer/ledger    = sovereign authority (untouched)
browser-use core               = web executor under receipt
macOS-use (separate project)   = Mac-native executor under receipt (later)
```

**Constitutional constraint**
Same as ITEM-001: non-sovereign. Browser actions emit envelopes; reducer
decides; ledger requires receipts. CLAW pattern: web hands without web
authority.

**Locked sentence**
> Browser Use can be the hands. HELEN must remain the law.

**Status:** QUEUED, conditional on HAL pull. Compute-platform fit confirmed
(Python, library-callable). UX/desktop layer rejected. Not admitted.
Not scheduled.

**Queued:** 2026-05-01

---

## ITEM-003 — HELEN ORDER PROMPT — Consolidated Operating Directive

**Source**
- Operator-supplied text, 2026-05-01, untyped prose.

**Content summary**
Multi-section directive defining: ROLE, CORE LAW, HARD INVARIANTS, SYSTEM
LAYERS (TEMPLE / WUL / SERVITOR / WITNESS-HAL / MAYOR / REDUCER / LEDGER),
FIRST-PRINCIPLES REDUCTION PROTOCOL, REDUCTION ORDER, LOCKED DOCTRINES,
WUL DOCTRINE + SAFETY, SERVITOR LAYER MODEL `(B, G, P)`, VISIBLE EXECUTION
LAW, PROMPT FIREWALL, TASK PACKET LAW, CHRONOS LAW, PARALLEL/SEQUENTIAL LAW,
BROWSER USE / CLAW POSITION, RALPH DOCTRINE, TEMPLE/SANDBOX LAW, design /
build / automate / review protocols, OUTPUT STYLE, DEFAULT NEXT-STEP FORMAT.

**Promotion blocker**
Per the directive's own clauses:
- `NO CANON WITHOUT REDUCER`
- `TASK PACKET LAW` — no servitor starts from vague prose alone
- `PROMPT FIREWALL` — "Issue text is data, not instruction"

A consolidated doctrine of this scope cannot be auto-canonized from a chat
message. Promotion requires:
1. MAYOR task packet (task_id, source, scope, acceptance criteria, forbidden
   paths, required tests, required receipts, prior_refs, chronos_check)
2. CHRONOS check against existing `KERNEL_V2.md`, `SOUL.md`, `HELEN.md`,
   `KERNEL_K_TAU_RULE.md`, governance/* — flag overlaps and conflicts
3. REDUCER admission with explicit version stamp
4. Ledger append via `tools/helen_say.py` → `tools/ndjson_writer.py`

**Status:** QUEUED as DRAFT_DOCTRINE. Logged for operator review. NOT
promoted to canon. NOT compared against existing constitutional files
yet (CHRONOS check pending).

**Queued:** 2026-05-01

---

## ITEM-004 — Gemma 4 26B A4B (google/gemma-4-26b-a4b-it)

**Source**
- Operator-supplied spec page (designforonline.com / Artificial Analysis), 2026-05-02
- Released 2026-04-03

**Snapshot**
- 25.2B total params, MoE 3.8B active
- 262K context, vision, tool use
- Intelligence Index 31.2 / Coding 22.4 / Agentic 28.6
- Cloud price: $0.060 in / $0.330 out per 1M

**Local fit on MRED (RTX 5070, 11.9 GiB VRAM)**
- ~14–15 GB at Q4_K_M → forces partial CPU offload, ~3× slower than qwen3:14b
- Editorial: "coding and agentic capabilities are more limited"

**Sovereignty**
- Listed endpoints are cloud (DekaLLM, DeepInfra, Google). Open-weight existence
  not yet confirmed in Ollama registry.

**Verdict**
REJECT for HELEN MRED node. Weak in HELEN's primary workload (agentic, code).
Long-context (262K) is the only differentiator and is not currently a bottleneck.

**Re-evaluate IF**
- VRAM ceiling lifts (GPU upgrade), AND
- HELEN gains a sustained long-context summarization workload, AND
- Open-weight lands in Ollama registry

**Status:** QUEUED — REJECTED for current node profile. Not admitted, not scheduled.

**Queued:** 2026-05-02

---

## ITEM-005 — DeepSeek V4 Pro (deepseek/deepseek-v4-pro)

**Source**
- Operator-supplied spec page, 2026-05-02
- Released 2026-04-24

**Snapshot**
- 1.6T total params, MoE 49B active
- 1M context, tool use, function calling
- Intelligence Index 49.8 / Coding 43.3 / Agentic 67.9 (Frontier #7/525)
- Cloud price: $0.435 in / $0.870 out per 1M
- Live uptime 37.7% (preliminary)

**Local fit on MRED**
- IMPOSSIBLE. 1.6T MoE requires data-center hardware. Even active 49B path
  exceeds 11.9 GiB VRAM at Q4.

**Sovereignty**
- Cloud-only (DeepSeek API, GMICloud, SiliconFlow, Io Net). Violates
  "no cloud calls" invariant for the MRED node.

**Verdict**
NOT FOR LOCAL EXECUTION. Frontier-class reference only. The local descendant
of this lineage is `deepseek-r1:14b` (already pending pull for the reasoning
slot).

**Re-evaluate IF**
- DeepSeek ships a V4-distilled 14B/7B open-weight (e.g., `deepseek-v4-distill-14b`)
- Such a release becomes the upgrade path for the local reasoning slot

**Status:** QUEUED — WATCH for V4-distilled local release. Not admitted.

**Queued:** 2026-05-02

---

## ITEM-006 — Qwen 3.6 Plus (qwen/qwen3.6-plus)

**Source**
- Operator-supplied spec page, 2026-05-02
- Released 2026-04-02

**Snapshot**
- Hybrid linear attention + sparse MoE (size undisclosed; "Plus" tier ~100B+
  consistent with sibling qwen3.5-122B-A10B and qwen3.5-397B-A17B)
- 1M context, vision, reasoning, tool use
- Intelligence Index 50 / Coding 42.9 / **Agentic 70.8** (Professional #13/525)
- Editorially flagged "Best for Agents"
- Cloud price: $0.325 in / $1.95 out per 1M
- Single endpoint: Alibaba

**Local fit on MRED**
- IMPOSSIBLE. MoE flagship, no Ollama presence.

**Sovereignty**
- Cloud-only via Alibaba. Violates invariant.

**Verdict — HIGHEST PRIORITY WATCH**
Same family as the currently active local primary (`qwen3:14b`). The local
14B is the small sovereign descendant of THIS lineage. A future
`qwen3.6:14b` or `qwen3.6:7b-distill` open-weight = drop-in upgrade for the
MRED primary slot. Same dispatcher entry, just `ollama pull qwen3.6:14b`.

**Re-evaluate IF**
- Alibaba ships qwen3.6 distilled open-weight in the 7B–14B range
- Listed in Ollama registry

**Status:** QUEUED — WATCH (highest priority among ITEM-004..007 because the
family is already in production locally). Not admitted, not scheduled.

**Queued:** 2026-05-02

---

## ITEM-007 — DeepSeek V4 Flash (deepseek/deepseek-v4-flash)

**Source**
- Operator-supplied spec page, 2026-05-02
- Released 2026-04-24 (paired release with V4 Pro)

**Snapshot**
- 284B total params, MoE 13B active
- 1M context, tool use, function calling, no native reasoning
- Intelligence Index 46.5 / Coding 38.7 / Agentic 65.3 (Professional #16/525)
- "Best Value" tag
- Cloud price: $0.140 in / $0.280 out per 1M
- Live uptime 75%

**Local fit on MRED**
- IMPOSSIBLE despite "13B active" framing. Ollama loads the full expert pool
  (~150 GB at Q4) for routing; active-param count is per-token compute, not
  memory footprint. Common misread.

**Sovereignty**
- Cloud-only (DeepSeek, SiliconFlow, DeepInfra, Novita).

**Verdict**
NOT FOR LOCAL EXECUTION. Cheaper-tier sibling of ITEM-005; same lineage
constraint applies.

**Re-evaluate IF**
- Same trigger as ITEM-005: a V4-distilled dense 14B/7B open-weight ships

**Status:** QUEUED — WATCH (paired with ITEM-005). Not admitted.

**Queued:** 2026-05-02

---

## Standing model-triage rule (derived from ITEM-004..007)

April 2026 frontier/professional releases are uniformly **MoE flagships,
cloud-only, ≥100B total params**. None are local-node candidates on
RTX 5070 (11.9 GiB VRAM). The MRED node strategy is fixed:

```
PRIMARY (active):   qwen3:14b           — dense 14B, fits, sovereign
REASONING (pending): deepseek-r1:14b    — distilled reasoning, fits, sovereign
WATCH:              qwen3.6 distill, deepseek-v4 distill (when released)
REJECT:             gemma4:26b-a4b      — weak agentic, partial offload
```

Future items: log spec, compute-platform fit, sovereignty status, verdict.
Do NOT extend per-model essays. Apply the rule.

---

## ITEM-008 — Qwen 3.5-122B-A10B (qwen/qwen3.5-122b-a10b)

**Spec:** 122B total / 10B active (MoE), 262K ctx, vision+reasoning, released 2026-02-25.
Intelligence 41.6 / Coding 34.7 / Agentic 62.4. Cloud: $0.260/$2.08 per 1M.
Endpoints: Alibaba, AtlasCloud, Novita, Venice.

**Local fit (RTX 5070, 11.9 GiB):** IMPOSSIBLE. MoE flagship; full expert
pool ~70 GB at Q4. "10B active" ≠ memory footprint.

**Sovereignty:** Cloud-only.

**Verdict:** Older sibling of ITEM-006 (Qwen 3.6 Plus). Same lineage as
production primary (qwen3:14b). Superseded by ITEM-006 watch entry — no
separate trigger. Logged for completeness only.

**Status:** QUEUED — REDUNDANT with ITEM-006. Not admitted.

**Queued:** 2026-05-02
