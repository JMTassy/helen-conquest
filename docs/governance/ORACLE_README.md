# ORACLE BOT - CLI Emulation

Multi-Agent Cognitive Architecture with Epistemic Tier Discipline

## Architecture

```
DECOMPOSER → EXPLORER → CRITIC → BUILDER → INTEGRATOR
    🔍          🧭         ⚔️        🔨         🎯
```

### The 5 Agents

1. **DECOMPOSER** - Transforms fuzzy requests into precise task graphs
2. **EXPLORER** - Generates diverse, meaningfully different solution candidates
3. **CRITIC** - Adversarial verification engine (WILLIAM protocol)
4. **BUILDER** - Constructs artifacts from surviving candidates
5. **INTEGRATOR** - Merges, finalizes, and decides STOP/CONTINUE

### Epistemic Tiers

- **Tier I**: Proven/tested only (full derivation discharged)
- **Tier II**: Falsifiable conjectures (explicit falsification protocol)
- **Tier III**: Heuristics only (labeled, cannot justify other claims)

## Installation

```bash
# No installation needed - just Python 3.7+
python3 oracle_cli.py --help
```

Optional dependencies for real LLM:
```bash
pip install requests
```

## Usage

### 1. Interactive Mode (Mock LLM)

```bash
python3 oracle_cli.py
```

This starts an interactive session with mock responses (no API key needed).

```
ORACLE> How do I implement caching?
[System runs all 5 agents sequentially with mock responses]

ORACLE> save
[Saves session to JSON file]

ORACLE> quit
```

### 2. Interactive Mode (Real LLM)

```bash
# Set API key first
export ANTHROPIC_API_KEY="your_key_here"
# or
export OPENAI_API_KEY="your_key_here"

# Run with real LLM
python3 oracle_cli.py --real
```

### 3. Direct Query Mode (Mock)

```bash
python3 oracle_cli.py --query "How do I optimize database queries?"
```

### 4. Direct Query Mode (Real LLM)

```bash
export ANTHROPIC_API_KEY="your_key_here"
python3 oracle_cli.py --query "How do I optimize database queries?" --real
```

### 5. Save Output to File

```bash
python3 oracle_cli.py --query "..." --save output.json
```

## Command Line Options

```
--query, -q    Direct query (non-interactive mode)
--real, -r     Use real LLM instead of mock responses
--save, -s     Save output to JSON file
--help, -h     Show help message
```

## Examples

### Example 1: Quick Test (Mock)

```bash
python3 oracle_cli.py --query "Should I use REST or GraphQL?"
```

### Example 2: Real Analysis

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python3 oracle_cli.py --query "Design a distributed caching system" --real --save cache_analysis.json
```

### Example 3: Interactive Session

```bash
python3 oracle_cli.py --real

ORACLE> How can I reduce latency in microservices?
[Waits for full 5-agent analysis]

ORACLE> What are trade-offs between monolith and microservices?
[New analysis]

ORACLE> save
✓ Session saved to oracle_session_20260110_143022.json

ORACLE> quit
```

## Output Structure

Each agent produces YAML-formatted output:

```yaml
DECOMPOSITION:      # DECOMPOSER
  core_question: "..."
  subtasks: [...]
  blocking_unknowns: [...]

EXPLORATION:        # EXPLORER
  candidates:
    - id: C1
      approach_type: "CONVENTIONAL"
      viability_estimate: 0.7

CRITIQUE:           # CRITIC (WILLIAM Protocol)
  candidate_evaluations:
    - candidate_id: C1
      verdict: "ROBUST|FLAWED_REPAIRABLE|INVALID_DANGEROUS"
      verdict_symbol: "✅|⚠️|❌"

BUILD:              # BUILDER
  artifact:
    type: "code|proof|plan|analysis"
    content: |
      [THE ACTUAL DELIVERABLE]

INTEGRATION:        # INTEGRATOR
  final_answer:
    content: |
      [USER-FACING RESPONSE]
  confidence:
    overall: 0.75
  decision:
    verdict: "STOP|CONTINUE"
```

## Session Files

Sessions are saved as JSON with:

```json
{
  "query": "Original user query",
  "results": [
    {
      "agent": "DECOMPOSER",
      "output": "...",
      "timestamp": "2026-01-10T14:30:22.123456"
    },
    ...
  ],
  "context": {
    "DECOMPOSER": "...",
    "EXPLORER": "...",
    ...
  },
  "timestamp": "2026-01-10T14:30:22.123456"
}
```

## WILLIAM Protocol (CRITIC Agent)

The CRITIC agent uses the WILLIAM doctrine:

1. **Reality Scan** - What does this ACTUALLY claim?
2. **Anti-Bullshit Protocol** - Where is uncertainty hidden?
3. **Auto-Demolition** - If dead wrong, what breaks?
4. **Tier Gate Check** - Any epistemic tier violations?
5. **Falsification Hook** - What minimal test settles this?

## Key Features

### Adversarial Verification
- CRITIC challenges all assumptions
- No "politeness bias" - brutal honesty required
- Kill-switches for fatal flaws

### Epistemic Rigor
- All claims labeled with tier (I/II/III)
- Tier III cannot justify other claims
- Progress scored by tier discharge

### Emergent Synthesis
- Disagreement is information
- Pattern analysis across agents
- Detects shared blind spots

## Mock vs Real LLM

**Mock Mode (default)**:
- No API key required
- Instant responses
- Generic but structurally correct output
- Perfect for testing the flow

**Real Mode (--real)**:
- Requires API key (Anthropic or OpenAI)
- Actual analysis of your query
- Much slower (30-60 seconds per agent)
- Production-quality insights

## Troubleshooting

### "No API key found"
```bash
export ANTHROPIC_API_KEY="your_key"
# or
export OPENAI_API_KEY="your_key"
```

### "Module 'requests' not found"
```bash
pip install requests
```

### Colors not showing
Some terminals don't support ANSI colors. Output will still be functional, just not colored.

## Advanced Usage

### Custom Configuration

Edit `oracle_cli.py` to customize:

```python
CONFIG = {
    "llm_backend": "mock",  # or "anthropic", "openai"
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 4096,
    "temperature": 0.7,
}
```

### Custom Prompts

Modify the `AGENT_PROMPTS` dictionary in `oracle_cli.py` to adjust agent behavior.

### Custom Mock Responses

Edit the `MOCK_RESPONSES` dictionary to provide domain-specific examples.

## Architecture Principles

1. **Progress = Stability Under Attack** (not agreement)
2. **Every claim carries epistemic tier** (I/II/III)
3. **Failure is explicit** (no hallucinated closure)
4. **Disagreement contains information** (pattern analysis)
5. **Only INTEGRATOR can STOP** (closure authority)

## Comparison to Other Systems

| Feature | ORACLE | ChatGPT | Traditional |
|---------|--------|---------|-------------|
| Adversarial testing | ✅ Built-in | ❌ No | ❌ No |
| Epistemic tiers | ✅ I/II/III | ❌ No | ❌ No |
| Multiple hypotheses | ✅ Always | ⚠️ Sometimes | ❌ Rare |
| Brutal honesty | ✅ WILLIAM | ❌ Polite | ⚠️ Varies |
| Kill-switches | ✅ Yes | ❌ No | ❌ No |

## Future Enhancements

The full ORACLE BOT system (not included in this CLI) has:

- Flask web interface
- Consensus voting mechanism
- Tier I validator with computational certificates
- Session persistence
- Parallel agent execution
- Multi-backend support (Ollama, LMStudio)

To implement the full system, you would need the additional files:
- `app.py` (Flask backend)
- `consensus.py` (voting algorithm)
- `validator.py` (Tier I validation)
- `prompts_v3.py` (full prompt system)
- Templates and static files

## License

This is a demonstration/educational implementation.

## Credits

- WILLIAM Protocol: Reality-based adversarial verification
- Epistemic Tiers: Formal verification principles
- Multi-Agent: Inspired by cognitive architectures and swarm intelligence
