"""
ORACLE BOT - Multi-Agent Cognitive Architecture
================================================
A 5-agent sequential brainstorming system with epistemic tier discipline.

Agents: DECOMPOSER → EXPLORER → CRITIC → BUILDER → INTEGRATOR

Usage:
    pip install flask requests --break-system-packages
    python app.py
    
Then open http://localhost:5000
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
import json
import os
import time
from pathlib import Path
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

CONFIG = {
    "llm_backend": "ollama",  # Options: "anthropic", "openai", "ollama", "lmstudio", "mock"
    "model": "mistral",
    "api_base_url": "http://localhost:11434",
    "max_tokens": 4096,
    "temperature": 0.7,
}

# Agent execution order
AGENT_ORDER = ["DECOMPOSER", "EXPLORER", "CRITIC", "BUILDER", "INTEGRATOR"]

# ═══════════════════════════════════════════════════════════════════════════════
# AGENT MEGA-PROMPTS (loaded from modular system)
# ═══════════════════════════════════════════════════════════════════════════════

# Import modular prompt system (try v3 first, then v2, then fallback)
try:
    from prompts_v3 import get_agent_prompt, get_all_prompts, AGENT_ORDER as PROMPT_AGENT_ORDER
    AGENT_PROMPTS = get_all_prompts()
    print("✓ Loaded WILLIAM-enhanced v3 prompts")
    PROMPT_VERSION = "v3"
except ImportError:
    try:
        from prompts import get_agent_prompt, get_all_prompts, AGENT_ORDER as PROMPT_AGENT_ORDER
        AGENT_PROMPTS = get_all_prompts()
        print("✓ Loaded consensus-aware v2 prompts")
        PROMPT_VERSION = "v2"
    except ImportError:
        print("⚠ No prompt module found, using fallback prompts")
        PROMPT_VERSION = "fallback"
        AGENT_PROMPTS = {
            "DECOMPOSER": "You are DECOMPOSER. Break the problem into atomic subtasks with dependencies. Output YAML.",
            "EXPLORER": "You are EXPLORER. Generate 5 diverse solution candidates. Output YAML.",
            "CRITIC": "You are CRITIC. Adversarially evaluate each candidate. Score 0-10. Output YAML.",
            "BUILDER": "You are BUILDER. Build the actual deliverable from surviving candidates. Output YAML.",
            "INTEGRATOR": "You are INTEGRATOR. Synthesize final response with confidence score. Output YAML."
        }

# Import Tier I validator
try:
    from validator import validate_builder_output, TierIValidator
    VALIDATOR_AVAILABLE = True
    print("✓ Tier I Validator loaded")
except ImportError:
    VALIDATOR_AVAILABLE = False
    print("⚠ Validator not available")

# Import Consensus Engine
try:
    from consensus import OracleConsensusOrchestrator, create_vote_from_agent_output, Proposal
    CONSENSUS_AVAILABLE = True
    print("✓ Consensus Engine loaded")
except ImportError:
    CONSENSUS_AVAILABLE = False
    print("⚠ Consensus Engine not available")

# ═══════════════════════════════════════════════════════════════════════════════
# LLM ROUTER
# ═══════════════════════════════════════════════════════════════════════════════

def query_llm(agent_name: str, full_prompt: str) -> str:
    """Route query to configured LLM backend."""
    
    backend = CONFIG["llm_backend"]
    
    if backend == "mock":
        return mock_response(agent_name)
    elif backend == "anthropic":
        return query_anthropic(full_prompt)
    elif backend == "openai":
        return query_openai(full_prompt)
    elif backend == "ollama":
        return query_ollama(full_prompt)
    elif backend == "lmstudio":
        return query_lmstudio(full_prompt)
    else:
        return f"[ERROR] Unknown backend: {backend}"


def mock_response(agent_name: str) -> str:
    """Mock responses for testing without LLM."""
    mock_outputs = {
        "DECOMPOSER": """```yaml
TASK_DECOMPOSITION:
  core_question: "How to implement the requested functionality?"
  subtasks:
    - id: S1
      description: "Analyze requirements"
      inputs_required: ["user query"]
      acceptance_test: "Clear spec document"
      failure_modes: ["ambiguous requirements"]
      dependencies: []
  dependency_dag: "S1 → S2 → S3"
  blocking_unknowns: ["Need more context"]
  minimal_next_step: "Clarify requirements"
```""",
        "EXPLORER": """```yaml
EXPLORATION:
  for_subtask: "S1"
  candidates:
    - id: C1
      approach: "CONVENTIONAL"
      key_idea: "Standard implementation"
      assumptions: ["Requirements are clear"]
      why_it_might_work: "Proven approach"
      likely_failure_mode: "May miss edge cases"
      evidence_needed: "User feedback"
      tier: "II"
  diversity_check: "Approaches are distinct"
```""",
        "CRITIC": """```yaml
CRITIQUE:
  candidate_evaluations:
    - candidate_id: C1
      strongest_counterargument: "May be too simple"
      hidden_assumptions: ["User needs are fully understood"]
      edge_cases: ["High load scenarios"]
      adversarial_example: "Concurrent users"
      what_must_be_proven: "Scalability"
      what_must_be_tested: "Load tests"
      viability_score: 7
      viability_justification: "Solid but needs validation"
  recommended_survivor: "C1"
  kill_recommendation: []
  open_obligations: ["Performance testing"]
```""",
        "BUILDER": """```yaml
BUILD:
  selected_candidate: "C1"
  artifact:
    type: "plan"
    content: |
      Implementation plan ready for execution.
  definitions_used: []
  derivation_steps: []
  resolved_objections: []
  open_obligations:
    - obligation: "Testing"
      blocker: "None"
      priority: "HIGH"
```""",
        "INTEGRATOR": """```yaml
INTEGRATION:
  executive_summary: |
    Analysis complete. Ready for implementation.
  final_answer:
    content: |
      The system has analyzed your request and prepared a structured response.
    confidence: 0.75
    confidence_justification: "Mock response"
  epistemic_status:
    tier_I_claims: ["Structure analyzed"]
    tier_II_claims: ["Implementation feasible"]
    tier_III_claims: []
  contradictions_resolved: []
  what_this_does_not_claim: ["Production readiness"]
  open_obligations: ["Real LLM integration"]
  next_steps:
    - priority: "HIGH"
      action: "Configure real LLM backend"
      rationale: "Enable full functionality"
  progress_score:
    tier_I_discharged: 1
    tier_II_conjectures: 1
    scope_leaks_caught: 0
    total: 1.5
```"""
    }
    time.sleep(0.5)  # Simulate latency
    return mock_outputs.get(agent_name, "[MOCK] Agent response")


def query_anthropic(prompt: str) -> str:
    """Query Anthropic Claude API."""
    import requests
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "[ERROR] ANTHROPIC_API_KEY not set. Set it or use 'mock' backend."
    
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
    
    try:
        response = requests.post(
            f"{CONFIG['api_base_url']}/v1/messages",
            headers=headers,
            json=data,
            timeout=120
        )
        response.raise_for_status()
        return response.json()["content"][0]["text"]
    except Exception as e:
        return f"[ERROR] Anthropic API: {str(e)}"


def query_openai(prompt: str) -> str:
    """Query OpenAI-compatible API."""
    import requests
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "[ERROR] OPENAI_API_KEY not set"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": CONFIG.get("openai_model", "gpt-4"),
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": CONFIG["max_tokens"],
        "temperature": CONFIG["temperature"]
    }
    
    try:
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


def query_ollama(prompt: str) -> str:
    """Query local Ollama instance via chat API."""
    import requests
    
    model = CONFIG.get("model", "mistral")
    base_url = CONFIG.get("api_base_url", "http://localhost:11434")
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json=data,
            timeout=300
        )
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "No content in Ollama response.")
    except Exception as e:
        return f"[ERROR] Ollama: {str(e)}"


def query_lmstudio(prompt: str) -> str:
    """Query LM Studio local server."""
    import requests
    
    data = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": CONFIG["temperature"],
        "max_tokens": CONFIG["max_tokens"]
    }
    
    try:
        response = requests.post(
            "http://localhost:1234/v1/chat/completions",
            json=data,
            timeout=300
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[ERROR] LM Studio: {str(e)}"


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPT BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

def build_full_prompt(agent_name: str, user_query: str, context: dict) -> str:
    """Build complete prompt with context injection."""
    
    base_prompt = AGENT_PROMPTS[agent_name]
    
    # Build context string from previous agent outputs
    context_parts = []
    for prev_agent in AGENT_ORDER:
        if prev_agent == agent_name:
            break
        if prev_agent in context:
            context_parts.append(f"=== {prev_agent} OUTPUT ===\n{context[prev_agent]}")
    
    context_str = "\n\n".join(context_parts) if context_parts else "[No previous agent output]"
    
    full_prompt = f"""ORACLE BOT - COGNITIVE ARCHITECTURE
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
# API ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)


@app.route('/api/config', methods=['GET'])
def get_config():
    """Return current configuration (excluding sensitive data)."""
    return jsonify({
        "llm_backend": CONFIG["llm_backend"],
        "model": CONFIG["model"],
        "agents": AGENT_ORDER
    })


@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration."""
    data = request.json
    for key in ["llm_backend", "model", "temperature", "max_tokens"]:
        if key in data:
            CONFIG[key] = data[key]
    return jsonify({"status": "ok", "config": CONFIG})


@app.route('/api/run-agent', methods=['POST'])
def run_agent():
    """Execute a single agent."""
    data = request.json
    agent_name = data.get("agentName")
    user_query = data.get("userQuery", "")
    context = data.get("context", {})
    
    if agent_name not in AGENT_ORDER:
        return jsonify({"error": f"Unknown agent: {agent_name}"}), 400
    
    full_prompt = build_full_prompt(agent_name, user_query, context)
    output = query_llm(agent_name, full_prompt)
    
    response_data = {
        "agent": agent_name,
        "output": output,
        "timestamp": datetime.now().isoformat()
    }
    
    # If BUILDER, run Tier I validation
    if agent_name == "BUILDER" and VALIDATOR_AVAILABLE:
        validation_result = validate_builder_output(output)
        response_data["validation"] = validation_result
    
    return jsonify(response_data)


@app.route('/api/validate', methods=['POST'])
def validate_output():
    """Validate BUILDER output for Tier I claims."""
    if not VALIDATOR_AVAILABLE:
        return jsonify({"error": "Validator not available"}), 503
    
    data = request.json
    builder_output = data.get("output", "")
    
    result = validate_builder_output(builder_output)
    return jsonify(result)


@app.route('/api/consensus', methods=['POST'])
def run_consensus():
    """Run consensus algorithm on agent outputs."""
    if not CONSENSUS_AVAILABLE:
        return jsonify({"error": "Consensus Engine not available"}), 503
    
    data = request.json
    context = data.get("context", {})
    proposal_id = data.get("proposalId", f"PROP_{datetime.now().strftime('%H%M%S')}")
    
    # Create votes from agent outputs
    votes = []
    for agent_name, output in context.items():
        if agent_name in AGENT_ORDER:
            vote = create_vote_from_agent_output(agent_name, output)
            votes.append(vote)
    
    if not votes:
        return jsonify({"error": "No valid agent outputs to process"}), 400
    
    # Create proposal
    proposal = Proposal(
        id=proposal_id,
        content={"query": data.get("userQuery", ""), "context": context},
        proposer="USER"
    )
    
    # Run consensus
    orchestrator = OracleConsensusOrchestrator()
    result = orchestrator.run_consensus(proposal, votes)
    
    return jsonify(result)


@app.route('/api/run-full-cycle', methods=['POST'])
def run_full_cycle():
    """Execute complete ORACLE cycle (all 5 agents) with validation."""
    data = request.json
    user_query = data.get("userQuery", "")
    
    results = []
    context = {}
    validation_result = None
    
    for agent_name in AGENT_ORDER:
        full_prompt = build_full_prompt(agent_name, user_query, context)
        output = query_llm(agent_name, full_prompt)
        
        context[agent_name] = output
        
        agent_result = {
            "agent": agent_name,
            "output": output,
            "timestamp": datetime.now().isoformat()
        }
        
        # Validate BUILDER output
        if agent_name == "BUILDER" and VALIDATOR_AVAILABLE:
            validation_result = validate_builder_output(output)
            agent_result["validation"] = validation_result
            
            # If kill-switch triggered, abort cycle
            if validation_result.get("report", {}).get("kill_switches_triggered", 0) > 0:
                agent_result["aborted"] = True
                results.append(agent_result)
                return jsonify({
                    "status": "KILL_SWITCH_TRIGGERED",
                    "results": results,
                    "final_context": context,
                    "validation": validation_result,
                    "message": validation_result.get("message", "Kill-switch triggered")
                })
        
        results.append(agent_result)
    
    return jsonify({
        "status": "complete",
        "results": results,
        "final_context": context,
        "validation": validation_result,
        "prompt_version": PROMPT_VERSION
    })


@app.route('/api/run-full-cycle-with-consensus', methods=['POST'])
def run_full_cycle_with_consensus():
    """Execute complete ORACLE cycle with consensus analysis."""
    data = request.json
    user_query = data.get("userQuery", "")
    
    results = []
    context = {}
    validation_result = None
    
    # Run all agents
    for agent_name in AGENT_ORDER:
        full_prompt = build_full_prompt(agent_name, user_query, context)
        output = query_llm(agent_name, full_prompt)
        
        context[agent_name] = output
        
        agent_result = {
            "agent": agent_name,
            "output": output,
            "timestamp": datetime.now().isoformat()
        }
        
        # Validate BUILDER output
        if agent_name == "BUILDER" and VALIDATOR_AVAILABLE:
            validation_result = validate_builder_output(output)
            agent_result["validation"] = validation_result
            
            if validation_result.get("report", {}).get("kill_switches_triggered", 0) > 0:
                agent_result["aborted"] = True
                results.append(agent_result)
                return jsonify({
                    "status": "KILL_SWITCH_TRIGGERED",
                    "results": results,
                    "final_context": context,
                    "validation": validation_result,
                    "message": validation_result.get("message", "Kill-switch triggered")
                })
        
        results.append(agent_result)
    
    # Run consensus analysis
    consensus_result = None
    if CONSENSUS_AVAILABLE:
        votes = []
        for agent_name, output in context.items():
            if agent_name in AGENT_ORDER:
                vote = create_vote_from_agent_output(agent_name, output)
                votes.append(vote)
        
        proposal = Proposal(
            id=f"CYCLE_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            content={"query": user_query},
            proposer="USER"
        )
        
        orchestrator = OracleConsensusOrchestrator()
        consensus_result = orchestrator.run_consensus(proposal, votes)
    
    return jsonify({
        "status": "complete",
        "results": results,
        "final_context": context,
        "validation": validation_result,
        "consensus": consensus_result,
        "prompt_version": PROMPT_VERSION
    })


@app.route('/api/save-session', methods=['POST'])
def save_session():
    """Save session to file."""
    data = request.json
    session_id = data.get("sessionId", datetime.now().strftime("%Y%m%d_%H%M%S"))
    
    filepath = Path(f"sessions/{session_id}.json")
    filepath.parent.mkdir(exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    return jsonify({"status": "saved", "filepath": str(filepath)})


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    validator_status = "ACTIVE" if VALIDATOR_AVAILABLE else "DISABLED"
    consensus_status = "ACTIVE" if CONSENSUS_AVAILABLE else "DISABLED"
    
    print(f"""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                      ORACLE BOT v3.1                         ║
    ║        WILLIAM-Enhanced Multi-Agent Verification Circuit      ║
    ╠═══════════════════════════════════════════════════════════════╣
    ║  Agents: DECOMPOSER → EXPLORER → CRITIC → BUILDER → INTEGRATOR║
    ║  Prompts: {PROMPT_VERSION:<20}                              ║
    ║  Backend: {CONFIG["llm_backend"]:<20}                           ║
    ║  Model: {CONFIG["model"]:<22}                           ║
    ╠═══════════════════════════════════════════════════════════════╣
    ║  Tier I Validator: {validator_status:<10}                           ║
    ║  Consensus Engine: {consensus_status:<10}                           ║
    ╠═══════════════════════════════════════════════════════════════╣
    ║  WILLIAM Protocol: Reality Scan | Anti-Bullshit | Auto-Demo  ║
    ║  Kill-Switches: Continuum | RH-Equiv | Discrete→Continuous   ║
    ║  Consensus: Weighted Votes | Emergent Synthesis | Brutal OK  ║
    ╚═══════════════════════════════════════════════════════════════╝
    
    API Endpoints:
      /api/run-full-cycle               → Basic 5-agent cycle
      /api/run-full-cycle-with-consensus→ Cycle + consensus analysis
      /api/consensus                    → Consensus on existing context
      /api/validate                     → Validate Tier I claims
    
    To use with real LLM:
      export ANTHROPIC_API_KEY=your_key
      # or
      export OPENAI_API_KEY=your_key
    """)
    
    app.run(debug=True, port=5000)
