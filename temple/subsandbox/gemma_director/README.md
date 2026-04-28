# TEMPLE_GEMMA_DIRECTOR_SANDBOX — NON_SOVEREIGN

Cheap local imagination, gated by HAL+MAYOR, before any cloud render spend.

## Status

- Authority: `NON_SOVEREIGN_SANDBOX`
- Layer: TEMPLE (Layer 5 per HELEN OS architecture)
- Promotable: **NO**. Outputs here are exploration sidecars, never canon, never ledger entries.
- Default model: `aura-gemma4:latest` via local Ollama (`http://localhost:11434`)
- Alternative: pull `huihui_ai/gemma-4-abliterated:e2b` if you prefer the upstream community variant — `--model huihui_ai/gemma-4-abliterated:e2b` after `ollama pull`

## One-line architecture

> Cheap local imagination first. Expensive cloud generation only after HAL/MAYOR filtering.

## Pipeline

```
INTENT (operator string)
    │
    ▼
HER (Gemma)        propose N concepts as JSON list
    │
    ▼
TEMPLE LABEL       every concept stamped NON_SOVEREIGN_SANDBOX
    │
    ▼
HAL                reject:
                     - forbidden patterns (sovereign paths, destructive ops)
                     - incoherent (length 20-600 chars)
                     - off-brand (HELEN concepts must mention identity marker)
    │
    ▼
MAYOR              rank by deterministic score, package top K as
                   MAYOR_PACKET_V1 with status: READY_FOR_REDUCER
    │
    ▼
batch receipt      GEMMA_DIRECTOR_BATCH_V1 sidecar in runs/
                   authority_status: NON_SOVEREIGN_SANDBOX
```

The REDUCER (sovereign) is **not called** from this sandbox. MAYOR prepares the case; REDUCER decides the verdict — and that decision is owned by the operator + HELEN's actual kernel/governance gates, not by this script.

## Running

```bash
# Default: 10 concepts, top 3 packetized
python3 temple/subsandbox/gemma_director/temple_gemma_director.py "INTENT: HELEN portrait, copper hair, blue-grey eyes, cyberpunk era, locked tripod, 35mm"

# More variants, fewer survivors
python3 temple/subsandbox/gemma_director/temple_gemma_director.py --n 20 --top 5 "INTENT: ..."

# Read intent from file
python3 temple/subsandbox/gemma_director/temple_gemma_director.py --intent-file intent.txt

# Swap to upstream abliterated variant
ollama pull huihui_ai/gemma-4-abliterated:e2b
python3 temple/subsandbox/gemma_director/temple_gemma_director.py --model huihui_ai/gemma-4-abliterated:e2b "INTENT: ..."
```

Each run produces a JSON receipt at `runs/{ts}__{intent_hash12}.json` containing:
- the intent + sha256
- all generated concepts
- HAL verdicts per concept
- top K SHIP_CANDIDATE packets (MAYOR_PACKET_V1 shape)
- rejections with reasons

## What this is for

- prompt variants
- shot ideas
- failure-class diagnosis brainstorm
- caption drafts
- seed-pool descriptions
- cheap "what could this become?" exploration

## What this is NOT for

- canon
- memory mutation
- ledger writes
- final quality judgment
- safety validation (HAL here is a sandbox-grade reject filter, not the sovereign K-tau or K8 gate)

## Workflow with the rest of HELEN

```
GEMMA_DIRECTOR (this)
   │
   ▼ produces SHIP_CANDIDATEs
   │
   ▼ operator picks ONE candidate
   │
   ▼ spend Higgsfield/Seedance credits on a single pilot render
   │
   ▼ render produces NON_SOVEREIGN_RENDER_RECEIPT (schema v3+)
   │   with operator_decision/pipeline_score/output_score
   │
   ▼ if KEEP + ratings high → propose for promotion via standard
     proposal → peer-review → MAYOR → REDUCER chain
```

The credit spend collapses from "render 10 ideas to find one good" to "render 1 already-filtered idea." That's the cost-discipline win.
