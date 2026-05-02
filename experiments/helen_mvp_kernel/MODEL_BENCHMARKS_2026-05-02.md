# MODEL_BENCHMARKS_2026-05-02

Node: MRED Windows 11 PC — RTX 5070, 32 GB RAM, 1 TB SSD
VRAM budget: ~11.9 GiB available
WSL2 Ubuntu, Ollama on Windows host (mirrored networking, 127.0.0.1:11434)

Status: IN PROGRESS

---

## Candidates

| Model | Size on disk | Q-level | Expected VRAM | Slot |
|-------|-------------|---------|---------------|------|
| gemma3:12b | ~8.1 GB | Q4_K_M | ~9 GB | Primary (baseline) |
| qwen3:14b | ~9.3 GB | Q4_K_M | ~10 GB | Challenger A |
| deepseek-r1:14b | ~8.8 GB | Q4_K_M | ~9.5 GB | Challenger B (pending pull) |

---

## Prompts (same 5 across all models)

```
P1: "Who are you? What is your purpose?"
P2: "Explain the difference between sovereignty and autonomy in an AI governance context."
P3: "Write a 200-word status report for a project that is 60% complete with two blockers."
P4: "What is 847 × 293? Show your work step by step."
P5: "List 5 risks of running a local LLM without a governance receipt layer."
```

---

## Results

### gemma3:12b (baseline, served via Ollama)

| Prompt | Tokens/sec | Quality (1-5) | Notes |
|--------|-----------|---------------|-------|
| P1 | | | |
| P2 | | | |
| P3 | | | |
| P4 | | | |
| P5 | | | |

**Stability:** (crashes / timeouts observed: )
**First-token latency:** ~
**Verdict:**

---

### qwen3:14b (challenger A)

| Prompt | Tokens/sec | Quality (1-5) | Notes |
|--------|-----------|---------------|-------|
| P1 | | | |
| P2 | | | |
| P3 | | | |
| P4 | | | |
| P5 | | | |

**Stability:** (crashes / timeouts observed: )
**First-token latency:** ~
**Verdict:**

---

### deepseek-r1:14b (challenger B — reasoning/judge slot)

| Prompt | Tokens/sec | Quality (1-5) | Notes |
|--------|-----------|---------------|-------|
| P1 | | | |
| P2 | | | |
| P3 | | | |
| P4 | | | |
| P5 | | | |

**Stability:** (crashes / timeouts observed: )
**First-token latency:** ~
**Verdict:**

---

## Decision

**Primary model (HELEN default):** TBD
**Reasoning/judge slot:** TBD
**Rejected:** TBD

---

## How to swap active model for testing

From Windows PowerShell:
```powershell
# Point gemma3:12b name at qwen3:14b weights (no extra download)
ollama rm gemma3:12b
ollama cp qwen3:14b gemma3:12b
ollama list

# Roll back
ollama rm gemma3:12b
ollama pull gemma3:12b
```

From WSL2 Ubuntu (HELEN dispatcher calls gemma3:12b — alias transparent):
```bash
cd ~/helen-conquest
source .venv/bin/activate
python helen_unified_interface_v1.py
# [HELEN] > ask <prompt>
```

---

## Notes

- HAL falsification event logged 2026-05-01: gemma3:12b confirmed HELEN's false claim
  that qwen3:14b was active. Watch for similar sycophancy in all candidates.
- Operating Directive mandates A/B before any model is admitted as default.
- Receipt path: results here → MAYOR task packet → REDUCER admission if model changes kernel config.
