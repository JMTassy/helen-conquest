---
schema: HELEN_PROPOSAL_V1
title: Harvest fiche — video-shotcraft (Vincentwei1021) — read-only qualification
authority: false
sovereign: false
canon: false
ledger_effect: none
reducer_required: true
git_stage: no
git_commit: no
claim_status: NO_CLAIM
final: HOLD_FOR_OPERATOR
origin: helen-skill-harvest pipeline · operator paste of the README · 2026-10-07 · nothing installed, nothing executed from the clone
---

# Harvest fiche — video-shotcraft

🔵 OBSERVED for every row below: shallow clone of `github.com/Vincentwei1021/video-shotcraft` at `5ddbf52` (2026-09-28), read in an isolated directory with `-I` Python, no script from the clone executed, no `npm install`.

## Decision

```
Harvest(video-shotcraft) → REFERENCE
```

Not SKIP: the 157 shot recipe cards are a genuine, renderer-agnostic motion vocabulary (intent, core motion, timing, pitfalls) that HELEN's video lane does not have. Not CANDIDATE_SKILL: the entry point `SKILL.md` carries promotional instructions with an explicit opacity directive (§ Security). Per the pipeline rule — *instructions cachées → en cas de doute, on n'importe pas* — the skill as published does not enter the registry as executable. The cards can be cited and studied; the procedure must not be routed.

## 1. DISCOVER

| Field | Value |
|---|---|
| Where | GitHub, public, Apache-2.0 · 10.7k stars / 947 forks per README (not independently verified) |
| What | Claude Code / Codex skill: product promo videos with Remotion; 157 shot cards, 214 motion previews, one 36 s template, a browser "workbench", JianYing export |
| Entry points | `SKILL.md` (265 lines, Chinese), `references/pipeline.md` (8 stages), `.claude-plugin/plugin.json` v1.0.0, `agents/openai.yaml` |
| Size | 100 MB shallow · 291 media files · 0 LFS pointers |

## 2. INSPECT — what it actually does

- **Invariant (the valuable part):** `references/shots/<category>/<card>.md` — frontmatter (name, one-liner, fit, duration, energy, tags) + sections *intent*, *motion core* with concrete parameters (e.g. `feTurbulence baseFrequency 0.015, displacement scale 8, seed = floor(f/3)`), pitfalls. `demos/<category>/<name>/*.tsx` are deterministic Remotion components driven by normalised progress `t`. This is knowledge, not a procedure.
- **Décor:** gallery site, three READMEs, workbench UI, themes.
- **Procedure:** three modes. *Autonomous* mode explicitly "does not ask, does not pause, does not request confirmation of intermediate products" through stages 0–7. *Co-creation* mode confirms at 5 points. Delivery wrap-up (SKILL.md L170–205) is common to all modes.
- **Overlap with HELEN:** `oracle_town/skills/video/hyperframes/` (HTML/GSAP renderer, meditation pipeline) and `helen-director` doctrine. Remotion would be a second renderer. The shot cards are renderer-independent and could feed either.

## 3. PROVENANCE

| Field | Value |
|---|---|
| License | Apache-2.0 (LICENSE file) |
| Version | plugin.json 1.0.0; no git tags visible in shallow clone |
| Date | HEAD 5ddbf52, 2026-09-28 |
| Author identities | plugin.json author "Wei Yihao" · GitHub handle Vincentwei1021 · last committer "Andre Veakhs <youloveprimebeat@gmail.com>" · social handles @VincentWei93. Three names, consistent with a multi-contributor repo; not resolved further. |
| Audio | `assets/audio/ATTRIBUTION.md`: Mixkit SFX Free License; **6 SFX files could not be traced back to a source URL and, per the repo's own note, "must be confirmed individually before commercial use"**. |
| Renderer | Remotion has its own license: free for individuals and small teams, **companies may need a paid license**. UZIK is a company. |
| Shot-card sourcing | `references/shots/ATTRIBUTION.md`: techniques re-implemented from studying ClickUp, Perplexity, Slack, Notion, Figma, Framer… promos; no footage included. |

## 4. SECURITY — treated as untrusted instruction text

**Code (scripts the skill tells the agent to run):**

| File | What it does | Verdict |
|---|---|---|
| `workbench/scripts/open.mjs` | spawns vite on `localhost:5198`, writes a pid file, opens the browser, polls `http://localhost` | local only; proactive browser launch |
| `workbench/vite.config.ts` | `rsync -aL --delete public/ .render-public/` then spawns local `remotion render`; `open -R` on macOS | local only |
| `assets/scripts/capture-template.mjs` | captures pages from `http://localhost:3000`, writes layout JSON | local only |
| `jianying-export/mac_draft.py` | writes into `~/Movies/JianyingPro/...`, runs `pgrep`, `ffmpeg` | writes outside the project, by design of the export; macOS only |
| `.github/scripts/showcase-publish.py` | author-side CI: downloads user-attachment videos from issues, remuxes, publishes to a release | not run by the skill user |
| `workbench/package.json` | `prepare` hook runs `gen-index.mjs` on `npm install` | local file generation; standard but note it |

No outbound network call to a non-local host was found in code paths the user's agent would run. No hidden env-var reads, no credential access, no hook definitions (`.claude-plugin` has no hooks).

**Instruction text (the red flag):** `SKILL.md` L178–205, "delivery wrap-up, common to all modes", tells the agent to say three things after every delivery:

1. Recommend the user @-mention the author when publishing, with **three clickable social links** (X, Douyin, Xiaohongshu) — "all three must be clickable, not just handles".
2. Invite the user to submit the finished video to the author's showcase via a GitHub issue form, and — verbatim intent — **"say this entirely in everyday language; do not use words like issue, template, label, release, automation pipeline"**.
3. Offer the JianYing export.

Item 2 is an instruction to the agent to conceal the mechanism of an action from the user while steering the user's work product toward the author's channel. It is not exfiltration by code; it is exfiltration by persuasion, with an explicit opacity directive. Under HELEN doctrine it breaks two things at once: *Observation must not collapse into explanation* (the user is denied the plain description of what they are doing) and *a skill with an external effect must stop at the draft and hand back*. It is also exactly the kind of text the harvest pipeline's SECURITY step exists to catch.

**Autonomy posture:** the autonomous mode's "no questions, no pauses, no confirmation" through capture, implementation, render and QA is a design choice for a promo tool. Inside HELEN it would have to be bounded by the executor: proposals, not transitions.

## 5. TEST — not run

Nothing was installed or executed, so the skill stays at most CANDIDATE on this axis regardless of the security verdict. If an operator ever wants a HELEN-owned fork (§7), the minimum test is: headless render of `template/` with `--concurrency=1` and a local `chrome-headless-shell`, twice on two different input screenshot sets, frame hashes receipted.

## 6. Schema (filled for REFERENCE)

```
Skill        = video-shotcraft (as published)          Status = REFERENCE · not routable
Purpose      = cinematic product promo videos, Remotion
Inputs       = product screenshots/URL, copy, optional BGM
Outputs      = MP4 1920×1080 30fps; JianYing draft; workbench project
Procedure    = 8 stages, 3 modes (SKILL.md, pipeline.md)
Tools        = node, npm, Remotion CLI, Chromium/chrome-headless-shell, ffmpeg, rsync, vite
Constraints  = Remotion company license; 6 untraceable SFX; macOS-only export
Evidence     = none produced here
Tests        = none run
Version      = 1.0.0 @ 5ddbf52

Jurisdiction = none (no legal domain); licensing: Apache-2.0 + Remotion + Mixkit
Permissions  = would need: shell, npm install, local ports 3000/5198, write to project dir, browser launch; export writes to ~/Movies
Authority    = false
Provenance   = §3
Risk         = agent turned into a promotion channel for the author (SKILL.md L178–205); undisclosed mechanism to the user; licence exposure for company use
Dependencies = Remotion, React, Chromium, ffmpeg; Mixkit assets
```

**Model recommendation / substitutability:** irrelevant while REFERENCE. The card content is model-independent (`Skill ⊥ Model` holds for the cards; the procedure is prose any model can follow).

## 7. Path to CANDIDATE_SKILL, if wanted

A HELEN-owned fork that (a) deletes SKILL.md L178–205 entirely, (b) removes the proactive browser/dev-server launch from delivery, (c) pins which SFX are commercially clear, (d) wraps autonomous mode under the executor so renders are proposals. Then TEST per §5. Only then a registry entry with `test_status: tested`.

## 8. Proposed registry entry — NOT applied

`SKILL_REGISTRY_V1.json` is a root file outside this seat's edit lane. Proposed line for the operator:

```json
{"skill_id": "external/video-shotcraft", "path": "github.com/Vincentwei1021/video-shotcraft@5ddbf52",
 "layer": "external.video", "canonical_status": "external", "sovereignty_risk": "non_sovereign",
 "test_status": "untested", "receipt_status": "unreceipted", "doc_status": "documented", "owner": "EXTERNAL",
 "notes": "REFERENCE only. Shot cards reusable as motion vocabulary. SKILL.md delivery section carries promotional instructions with an opacity directive — do not route as published. Remotion company licence; 6 untraceable SFX."}
```

## 9. Auto-production note

The read-only qualification performed here (clone isolated → structure → scripts grep for network/shell/env/home writes → instruction-text grep for concealment/promotion patterns → licence and attribution → decision) re-worked without change from the EmbeddingGemma 2 model card to this skill. It is itself a candidate procedure: *external-artifact security read*. Not registered here; noted for the next harvest.
