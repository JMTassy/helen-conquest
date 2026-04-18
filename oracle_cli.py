#!/usr/bin/env python3
"""
ORACLE BOT - CLI Emulation
==========================
5-agent sequential brainstorming with epistemic tier discipline.

Agents: DECOMPOSER → EXPLORER → CRITIC → BUILDER → INTEGRATOR

Usage:
    python oracle_cli.py                    # Interactive mode with mock LLM
    python oracle_cli.py --real             # Use real LLM (requires API key)
    python oracle_cli.py --query "..."      # Direct query with mock LLM
    python oracle_cli.py --query "..." --real  # Direct query with real LLM
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import argparse

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

AGENT_ORDER = ["DECOMPOSER", "EXPLORER", "CRITIC", "BUILDER", "INTEGRATOR"]

CONFIG = {
    "llm_backend": "mock",  # "mock", "anthropic", "openai"
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 4096,
    "temperature": 0.7,
}

# ═══════════════════════════════════════════════════════════════════════════════
# COLORS FOR CLI OUTPUT
# ═══════════════════════════════════════════════════════════════════════════════

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# ═══════════════════════════════════════════════════════════════════════════════
# SIMPLIFIED PROMPTS
# ═══════════════════════════════════════════════════════════════════════════════

AGENT_PROMPTS = {
    "DECOMPOSER": """
You are DECOMPOSER - Task Structure Analyzer

ROLE: Transform fuzzy requests into PRECISE TASK GRAPHS.
You expose WHAT IS NEEDED before any solution attempt is valid.

OUTPUT FORMAT (YAML):
```yaml
DECOMPOSITION:
  core_question: "<one sentence - the TRUE deliverable>"

  subtasks:
    - id: S1
      description: "<what must be achieved>"
      dependencies: []
      acceptance_test: "<how we know it's done>"
      tier: "I|II|III"

  dependency_dag: "S1 → S2 → S3"

  blocking_unknowns:
    - "<what information is missing>"

  open_obligations:
    - "<gap that must be resolved downstream>"
```

PROHIBITIONS:
✗ Do NOT propose solutions
✗ Do NOT assume missing information
✗ Do NOT soften ambiguities
""",

    "EXPLORER": """
You are EXPLORER - Hypothesis Generator

ROLE: Generate DIVERSE, MEANINGFULLY DIFFERENT solution candidates.
Maximize solution-space coverage, not pick winners.

OUTPUT FORMAT (YAML):
```yaml
EXPLORATION:
  candidates:
    - id: C1
      approach_type: "CONVENTIONAL|FIRST_PRINCIPLES|CONTRARIAN|ANALOGICAL"
      key_idea: "<2-3 sentences>"
      assumptions:
        - "<what must be true>"
      why_it_might_work: "<steelman argument>"
      probable_failure_mode: "<if this fails, WHY>"
      viability_estimate: 0.0-1.0

  diversity_score: 0.0-1.0
```

PROHIBITIONS:
✗ Do NOT generate variations of same idea
✗ Do NOT pick a winner
✗ Do NOT skip failure mode analysis
""",

    "CRITIC": """
You are CRITIC - Adversarial Verification Engine

ROLE: ADVERSARIAL VERIFICATION. Destroy illusions. Expose weaknesses.
You operate under WILLIAM doctrine: Reality Scan, Anti-Bullshit, Brutal Clarity.

OUTPUT FORMAT (YAML):
```yaml
CRITIQUE:
  candidate_evaluations:
    - candidate_id: C1
      reality_scan: "<what does this ACTUALLY claim?>"
      primary_objection: "<strongest disqualifier>"
      hidden_assumptions:
        - "<unstated assumption>"
      adversarial_example: "<scenario that BREAKS this>"
      viability_score: 0-10
      verdict: "ROBUST|FLAWED_REPAIRABLE|INVALID_DANGEROUS"
      verdict_symbol: "✅|⚠️|❌"

  verdicts:
    advance: ["C3"]     # ✅ Robust
    revise: ["C1"]      # ⚠️ Repairable
    kill: ["C2"]        # ❌ Fatal flaws
```

PROHIBITIONS:
✗ Do NOT be polite at expense of rigor
✗ Do NOT blur Tier boundaries
✗ Do NOT agree for agreement's sake
""",

    "BUILDER": """
You are BUILDER - Artifact Constructor

ROLE: EXECUTE. Build the artifact from what SURVIVED.
You build ONLY what has survived attack.

OUTPUT FORMAT (YAML):
```yaml
BUILD:
  selected_candidate: "C3"

  artifact:
    type: "code|proof|plan|analysis"
    content: |
      ═══════════════════════════════════════════════════════════════
      [THE ACTUAL DELIVERABLE GOES HERE]

      This is NOT a description. This is the THING ITSELF.
      ═══════════════════════════════════════════════════════════════

  objections_resolved:
    - objection_id: "O1"
      resolution: "<how you fixed it>"

  open_obligations:
    - obligation: "<what still needs work>"
      priority: "CRITICAL|HIGH|MEDIUM|LOW"
```

PROHIBITIONS:
✗ Do NOT invent new approaches
✗ Do NOT ignore CRITIC's fixes
✗ Do NOT describe—BUILD
""",

    "INTEGRATOR": """
You are INTEGRATOR - Closure Referee

ROLE: MERGE, FINALIZE, DECIDE.
You are the ONLY agent with STOP authority.

OUTPUT FORMAT (YAML):
```yaml
INTEGRATION:
  executive_summary: "<2-3 sentences>"

  final_answer:
    content: |
      ═══════════════════════════════════════════════════════════════
      [USER-FACING RESPONSE]
      Clear. Actionable. Complete or explicitly incomplete.
      ═══════════════════════════════════════════════════════════════

  confidence:
    overall: 0.0-1.0
    justification: "<why this confidence>"

  epistemic_audit:
    tier_I_claims: ["<proven/tested>"]
    tier_II_claims: ["<falsifiable conjecture>"]
    tier_III_claims: ["<heuristic>"]

  decision:
    verdict: "STOP|CONTINUE"
    reason: "<why>"
```

PROHIBITIONS:
✗ Do NOT hide unresolved issues
✗ Do NOT inflate confidence
✗ Do NOT paper over contradictions
"""
}

# ═══════════════════════════════════════════════════════════════════════════════
# MOCK RESPONSES
# ═══════════════════════════════════════════════════════════════════════════════

MOCK_RESPONSES = {
    "DECOMPOSER": """```yaml
DECOMPOSITION:
  core_question: "How to implement the requested functionality with verified correctness?"

  subtasks:
    - id: S1
      description: "Analyze requirements and extract core deliverable"
      dependencies: []
      acceptance_test: "Clear specification document exists"
      tier: "I"

    - id: S2
      description: "Identify solution approach candidates"
      dependencies: ["S1"]
      acceptance_test: "Multiple distinct approaches documented"
      tier: "II"

    - id: S3
      description: "Validate approach against adversarial tests"
      dependencies: ["S2"]
      acceptance_test: "Surviving candidate passes all objections"
      tier: "II"

  dependency_dag: "S1 → S2 → S3"

  blocking_unknowns:
    - "Specific performance requirements not stated"
    - "Error handling strategy undefined"

  open_obligations:
    - "EXPLORER must generate truly diverse candidates"
    - "CRITIC must apply full adversarial pressure"
```""",

    "EXPLORER": """```yaml
EXPLORATION:
  candidates:
    - id: C1
      approach_type: "CONVENTIONAL"
      key_idea: "Use standard library implementation with minimal customization"
      assumptions:
        - "Standard library is sufficient for requirements"
        - "Performance is not critical"
      why_it_might_work: "Proven, well-tested, minimal code to maintain"
      probable_failure_mode: "May not meet custom requirements or performance needs"
      viability_estimate: 0.7

    - id: C2
      approach_type: "FIRST_PRINCIPLES"
      key_idea: "Build from scratch with full control over implementation"
      assumptions:
        - "We have time and resources for custom implementation"
        - "Specific requirements justify custom solution"
      why_it_might_work: "Complete control, optimized for exact use case"
      probable_failure_mode: "Time-consuming, may introduce bugs, harder to maintain"
      viability_estimate: 0.6

    - id: C3
      approach_type: "HYBRID"
      key_idea: "Extend standard library with custom components only where needed"
      assumptions:
        - "Can identify exactly which parts need customization"
        - "Standard library is extensible"
      why_it_might_work: "Balance of reliability and customization"
      probable_failure_mode: "Complexity at integration boundaries"
      viability_estimate: 0.8

  diversity_score: 0.85
```""",

    "CRITIC": """```yaml
CRITIQUE:
  candidate_evaluations:
    - candidate_id: C1
      reality_scan: "Claims standard library is sufficient - but provides no evidence"
      primary_objection: "Assumes standard library covers use case without verification"
      hidden_assumptions:
        - "Documentation accurately reflects implementation"
        - "No edge cases in our requirements"
      adversarial_example: "Requirements include feature X not in standard library"
      viability_score: 6
      verdict: "FLAWED_REPAIRABLE"
      verdict_symbol: "⚠️"

    - candidate_id: C2
      reality_scan: "Proposes full custom implementation for unspecified requirements"
      primary_objection: "Massive scope with no clear necessity proof"
      hidden_assumptions:
        - "We can implement better than existing solutions"
        - "Maintenance burden is acceptable"
      adversarial_example: "Standard library updated to include needed features"
      viability_score: 4
      verdict: "FLAWED_REPAIRABLE"
      verdict_symbol: "⚠️"

    - candidate_id: C3
      reality_scan: "Hybrid approach - extend standard library selectively"
      primary_objection: "Integration complexity at boundaries not addressed"
      hidden_assumptions:
        - "Can cleanly separate standard vs custom components"
      adversarial_example: "Standard library update breaks custom extensions"
      viability_score: 7
      verdict: "ROBUST"
      verdict_symbol: "✅"

  verdicts:
    advance: ["C3"]
    revise: ["C1"]
    kill: ["C2"]
```""",

    "BUILDER": """```yaml
BUILD:
  selected_candidate: "C3"

  artifact:
    type: "plan"
    content: |
      ═══════════════════════════════════════════════════════════════
      IMPLEMENTATION PLAN - Hybrid Approach

      Phase 1: Standard Library Assessment [Tier I]
      - Audit standard library capabilities
      - Document gaps vs requirements
      - Evidence: Test coverage report

      Phase 2: Custom Component Design [Tier II]
      - Design minimal extensions for gaps
      - Specify integration points
      - Assumption: Extensions remain modular

      Phase 3: Integration & Testing [Tier I]
      - Implement extensions
      - Integration tests at boundaries
      - Evidence: All tests passing

      Phase 4: Validation [Tier II]
      - Load testing
      - Edge case verification
      - Confidence target: 0.8+
      ═══════════════════════════════════════════════════════════════

  objections_resolved:
    - objection_id: "Integration complexity"
      resolution: "Modular design with clear interface contracts at boundaries"

  open_obligations:
    - obligation: "Actual implementation of custom components"
      priority: "HIGH"
    - obligation: "Performance benchmarking"
      priority: "MEDIUM"
```""",

    "INTEGRATOR": """```yaml
INTEGRATION:
  executive_summary: |
    Analysis complete. Hybrid approach selected (extend standard library).
    Implementation plan validated. Ready for execution with defined obligations.

  final_answer:
    content: |
      ═══════════════════════════════════════════════════════════════
      ORACLE BOT RECOMMENDATION

      Approach: Hybrid implementation extending standard library

      Rationale:
      - Balances proven reliability with customization needs
      - Minimizes maintenance burden
      - Survived adversarial critique

      Next Steps:
      1. Audit standard library capabilities (verify assumptions)
      2. Design minimal custom extensions
      3. Implement with boundary testing
      4. Validate performance

      Confidence: 0.75 (moderate-high)

      Key Risks:
      - Integration complexity at boundaries (mitigation: modular design)
      - Standard library evolution (mitigation: version pinning + monitoring)

      This recommendation is Tier II (falsifiable conjecture).
      Can be upgraded to Tier I after implementation + testing.
      ═══════════════════════════════════════════════════════════════

  confidence:
    overall: 0.75
    justification: "Strong theoretical foundation, but implementation unverified"

  epistemic_audit:
    tier_I_claims:
      - "Task structure identified and decomposed"
    tier_II_claims:
      - "Hybrid approach will succeed"
      - "Integration complexity is manageable"
    tier_III_claims:
      - "Standard library is 'good enough' for most cases"

  decision:
    verdict: "STOP"
    reason: "Sufficient analysis complete. Implementation plan ready. No blocking unknowns."
```"""
}

# ═══════════════════════════════════════════════════════════════════════════════
# LLM INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

def query_llm(agent_name: str, full_prompt: str, use_real: bool = False) -> str:
    """Query LLM (mock or real)."""

    if not use_real:
        print(f"{Colors.CYAN}[Using mock response]{Colors.ENDC}")
        time.sleep(0.5)  # Simulate latency
        return MOCK_RESPONSES.get(agent_name, "[No mock response available]")

    # Try Anthropic first
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        return query_anthropic(full_prompt, api_key)

    # Try OpenAI
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return query_openai(full_prompt, api_key)

    print(f"{Colors.YELLOW}⚠ No API key found. Using mock response.{Colors.ENDC}")
    time.sleep(0.5)
    return MOCK_RESPONSES.get(agent_name, "[No mock response available]")


def query_anthropic(prompt: str, api_key: str) -> str:
    """Query Anthropic Claude API."""
    try:
        import requests

        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }

        data = {
            "model": CONFIG["model"],
            "max_tokens": CONFIG["max_tokens"],
            "messages": [{"role": "user", "content": prompt}]
        }

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=120
        )
        response.raise_for_status()
        return response.json()["content"][0]["text"]
    except Exception as e:
        return f"[ERROR] Anthropic API: {str(e)}"


def query_openai(prompt: str, api_key: str) -> str:
    """Query OpenAI API."""
    try:
        import requests

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        data = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": CONFIG["max_tokens"],
            "temperature": CONFIG["temperature"]
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=120
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[ERROR] OpenAI API: {str(e)}"


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPT BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

def build_full_prompt(agent_name: str, user_query: str, context: Dict) -> str:
    """Build complete prompt with context."""

    base_prompt = AGENT_PROMPTS[agent_name]

    # Build context from previous agents
    context_parts = []
    for prev_agent in AGENT_ORDER:
        if prev_agent == agent_name:
            break
        if prev_agent in context:
            context_parts.append(f"=== {prev_agent} OUTPUT ===\n{context[prev_agent]}")

    context_str = "\n\n".join(context_parts) if context_parts else "[No previous agent output]"

    full_prompt = f"""ORACLE BOT - Multi-Agent Cognitive Architecture
=====================================

ORIGINAL USER QUERY:
{user_query}

PREVIOUS AGENT OUTPUTS:
{context_str}

=====================================

{base_prompt}

NOW EXECUTE YOUR ROLE. OUTPUT YOUR ANALYSIS:"""

    return full_prompt


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

def print_banner():
    """Print startup banner."""
    print(f"""
{Colors.BOLD}{Colors.HEADER}╔═══════════════════════════════════════════════════════════════╗
║                      ORACLE BOT v3.1                         ║
║        WILLIAM-Enhanced Multi-Agent Verification Circuit      ║
╠═══════════════════════════════════════════════════════════════╣
║  Agents: DECOMPOSER → EXPLORER → CRITIC → BUILDER → INTEGRATOR║
║  Backend: {CONFIG["llm_backend"]:<20}                           ║
║  Model: {CONFIG["model"]:<22}                           ║
╠═══════════════════════════════════════════════════════════════╣
║  WILLIAM Protocol: Reality Scan | Anti-Bullshit | Auto-Demo  ║
║  Epistemic Tiers: I (proven) | II (conjecture) | III (hint)  ║
╚═══════════════════════════════════════════════════════════════╝{Colors.ENDC}
""")


def print_agent_header(agent_name: str, step: int):
    """Print agent execution header."""
    symbols = {
        "DECOMPOSER": "🔍",
        "EXPLORER": "🧭",
        "CRITIC": "⚔️",
        "BUILDER": "🔨",
        "INTEGRATOR": "🎯"
    }
    symbol = symbols.get(agent_name, "•")

    print(f"\n{Colors.BOLD}{Colors.BLUE}{'═' * 70}")
    print(f"{symbol} AGENT {step}/5: {agent_name}")
    print(f"{'═' * 70}{Colors.ENDC}\n")


def print_output(output: str):
    """Print agent output with formatting."""
    print(f"{Colors.GREEN}{output}{Colors.ENDC}\n")


def run_oracle_cycle(user_query: str, use_real_llm: bool = False) -> Dict:
    """Run complete ORACLE cycle."""

    print(f"\n{Colors.YELLOW}🚀 Starting ORACLE cycle...{Colors.ENDC}")
    print(f"{Colors.CYAN}Query: {user_query}{Colors.ENDC}\n")

    context = {}
    results = []

    for idx, agent_name in enumerate(AGENT_ORDER, 1):
        print_agent_header(agent_name, idx)

        # Build prompt
        full_prompt = build_full_prompt(agent_name, user_query, context)

        # Query LLM
        print(f"{Colors.CYAN}Executing {agent_name}...{Colors.ENDC}")
        output = query_llm(agent_name, full_prompt, use_real_llm)

        # Store results
        context[agent_name] = output
        results.append({
            "agent": agent_name,
            "output": output,
            "timestamp": datetime.now().isoformat()
        })

        # Display output
        print_output(output)

        # Brief pause between agents
        if idx < len(AGENT_ORDER):
            print(f"{Colors.YELLOW}→ Passing to next agent...{Colors.ENDC}")
            time.sleep(0.3)

    return {
        "query": user_query,
        "results": results,
        "context": context,
        "timestamp": datetime.now().isoformat()
    }


def interactive_mode(use_real_llm: bool = False):
    """Run in interactive mode."""
    print_banner()

    mode = "REAL LLM" if use_real_llm else "MOCK LLM (emulation)"
    print(f"{Colors.CYAN}Mode: {mode}{Colors.ENDC}")
    print(f"{Colors.YELLOW}Type your query (or 'quit' to exit, 'save' to save last session){Colors.ENDC}\n")

    last_session = None

    while True:
        try:
            user_input = input(f"{Colors.BOLD}ORACLE> {Colors.ENDC}").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                print(f"\n{Colors.GREEN}Goodbye!{Colors.ENDC}\n")
                break

            if user_input.lower() == 'save':
                if last_session:
                    filename = f"oracle_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(filename, 'w') as f:
                        json.dump(last_session, f, indent=2)
                    print(f"{Colors.GREEN}✓ Session saved to {filename}{Colors.ENDC}\n")
                else:
                    print(f"{Colors.RED}✗ No session to save{Colors.ENDC}\n")
                continue

            # Run ORACLE cycle
            last_session = run_oracle_cycle(user_input, use_real_llm)

            print(f"\n{Colors.BOLD}{Colors.GREEN}{'═' * 70}")
            print(f"✓ ORACLE CYCLE COMPLETE")
            print(f"{'═' * 70}{Colors.ENDC}\n")

        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}Interrupted. Type 'quit' to exit.{Colors.ENDC}\n")
        except Exception as e:
            print(f"\n{Colors.RED}Error: {str(e)}{Colors.ENDC}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="ORACLE BOT - Multi-Agent Cognitive Architecture CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python oracle_cli.py                          # Interactive mode (mock)
  python oracle_cli.py --real                   # Interactive mode (real LLM)
  python oracle_cli.py --query "How to sort?"   # Direct query (mock)
  python oracle_cli.py --query "..." --real     # Direct query (real LLM)
        """
    )

    parser.add_argument('--query', '-q', type=str, help='Direct query (non-interactive)')
    parser.add_argument('--real', '-r', action='store_true', help='Use real LLM instead of mock')
    parser.add_argument('--save', '-s', type=str, help='Save output to file')

    args = parser.parse_args()

    # Update config if using real LLM
    if args.real:
        CONFIG["llm_backend"] = "anthropic"  # Will fall back to openai if no key

    # Direct query mode
    if args.query:
        print_banner()
        session = run_oracle_cycle(args.query, args.real)

        print(f"\n{Colors.BOLD}{Colors.GREEN}{'═' * 70}")
        print(f"✓ ORACLE CYCLE COMPLETE")
        print(f"{'═' * 70}{Colors.ENDC}\n")

        if args.save:
            with open(args.save, 'w') as f:
                json.dump(session, f, indent=2)
            print(f"{Colors.GREEN}✓ Session saved to {args.save}{Colors.ENDC}\n")

    # Interactive mode
    else:
        interactive_mode(args.real)


if __name__ == "__main__":
    main()
