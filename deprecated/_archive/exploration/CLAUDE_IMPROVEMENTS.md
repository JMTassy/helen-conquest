# CLAUDE.md Improvement Analysis

## Summary of Issues Found in Current CLAUDE.md

### Critical Issues (Inaccuracies)

1. **Development Commands Section References Non-Existent Modules**
   - Refers to modules that don't exist: `observation_collector.py`, `memory_linker.py`, `os_runner.py`, `insight_engine.py`, `self_evolution.py`, `interactive_explorer.py`, `scenario_simulator.py`, `dashboard_server.py`
   - These are referenced as "Fully Operational" but don't exist in the codebase
   - The VERIFY_ALL.sh script tries to run these and fails with path errors

2. **Inaccurate Architecture Description**
   - Current code is NOT organized as described in "Labor Layer (OBS → INS → BRF → PUB → MEM → EVO)"
   - Actual modules: `obs_scan.py`, `ins_cluster.py`, `brf_onepager.py` exist BUT PUB/MEM/EVO don't
   - References to "Daily OS" phases 1-8 claimed as complete, but implementation incomplete

3. **Misleading Testing Section**
   - VERIFY_ALL.sh references test files that don't exist
   - References to Phase 2, Phase 6, Phase 7 tests that are not present
   - References to governance regression tests in wrong paths

4. **Wrong Module Locations**
   - Says modules are in `oracle_town/jobs/` which is correct
   - But says `oracle_town/core/` contains modules that actually are in `oracle_town/`

### Strengths to Keep

1. **Excellent High-Level Governance Architecture**
   - The conceptual model of three layers (Labor, Authority, World) is solid
   - Constitutional principles and invariants are well articulated
   - Safety kernel concept is valuable

2. **Good Foundational Concepts**
   - K-gates explanation is clear
   - Policy pinning concepts are well explained
   - Recipe for fail-closed systems is pedagogically strong

3. **Clear Organizational Structure**
   - Table of contents is excellent
   - Section navigation is well designed
   - Examples are helpful

## Recommended Changes

### Immediate Fixes

1. **Correct Development Commands Section**
   - Remove references to non-existent modules (observer.py, memory_linker.py, etc.)
   - List only modules that actually exist and can be run
   - Provide realistic example commands for testing

2. **Fix Architecture Section**
   - Accurately describe what's implemented vs. what's planned
   - Update the "Complete Status" to reflect reality
   - Remove "Fully Operational" claims for incomplete phases

3. **Simplify Testing Section**
   - Focus on tests that actually exist
   - Provide working pytest commands
   - Remove references to missing test files

4. **Add Quick Reference for Actual Module Structure**
   - List what's actually in `oracle_town/core/`
   - List what's actually in `oracle_town/jobs/`
   - Clarify the actual entry points and CLI

### Medium-Term Improvements

1. **Add Practical Development Guide**
   - How to actually run a single job
   - How to test a module
   - How to add a new test
   - How to run the full verification suite

2. **Clarify Schema Usage**
   - Real examples of Claim, Verdict objects
   - How to work with the actual schemas in code
   - Common patterns and gotchas

3. **Better Integration Points**
   - Where to hook in new analysis
   - How the orchestrator actually works
   - Real entry points vs. conceptual ones

## Files That Actually Exist and Can Be Run

### Core Governance
- `oracle_town/core/claim_compiler.py` - Converts input to claims
- `oracle_town/core/tri_gate.py` - Verification logic
- `oracle_town/core/mayor.py` - Final verdict authority
- `oracle_town/core/orchestrator.py` - Main execution engine

### Jobs (Labor Layer)
- `oracle_town/jobs/obs_scan.py` - Observation scanning
- `oracle_town/jobs/ins_cluster.py` - Clustering/insight
- `oracle_town/jobs/brf_onepager.py` - Brief synthesis
- `oracle_town/jobs/tri_gate.py` - TRI gate verification
- `oracle_town/jobs/mayor_sign.py` - Mayor signing

### Schemas
- `oracle_town/schemas/claim.py` - Claim dataclass
- `oracle_town/schemas/verdict.py` - Verdict dataclass
- `oracle_town/schemas/reports.py` - Report types

### Districts/Agents
- `oracle_town/districts/legal/gdpr_street.py` - GDPR analysis
- `oracle_town/districts/technical/security_street.py` - Security analysis
- `oracle_town/districts/business/operations_street.py` - Operations
- `oracle_town/districts/social/impact_street.py` - Social impact

### Main Entry Points
- `oracle_town/cli.py` - Command-line interface
- `oracle_town/core/orchestrator.py` - Main orchestrator

## Key Missing / Incomplete Implementations

1. **Daily OS Phases 1-8**: Referenced as complete but mostly missing
   - Phase 1 (observation_collector.py) - Missing
   - Phase 2 (memory_linker.py) - Missing
   - Phase 3 (os_runner.py) - Missing
   - Phase 4 (insight_engine.py) - Missing
   - Phase 5 (self_evolution.py) - Missing
   - Phase 6 (interactive_explorer.py) - Missing
   - Phase 7 (scenario_simulator.py) - Missing
   - Phase 8 (dashboard_server.py) - Missing

2. **PUB, MEM, EVO Labor Modules**: Partially implemented or missing
   - Only OBS, INS, BRF are clearly implemented

3. **Complete Test Suite**: Missing many referenced test files
   - Phase 2 crypto tests
   - Phase 6 interactive tests
   - Phase 7 scenario tests
   - Adversarial runs

## Recommendations for Claude Code Users

**When using this repo:**

1. **Ignore references to Daily OS phases** - They're conceptually described but mostly not implemented
2. **Focus on what exists**: OBS_SCAN, INS_CLUSTER, BRF_ONEPAGER, TRI_GATE, MAYOR_SIGN, and the Orchestrator
3. **Use cli.py** for command-line interface, not individual phase runners
4. **Run pytest** for actual tests, not VERIFY_ALL.sh (it has path issues)
5. **Check git-tracked files** via `git ls-files | grep "\.py$"` for the real code

## How to Fix CLAUDE.md

1. **Add a "IMPORTANT: Current Implementation Status" section** that clearly states what's done and what's planned
2. **Replace the entire "Development Commands" section** with accurate, testable commands
3. **Fix all "currently operational" claims** to be honest about implementation status
4. **Add a "Practical Quick Start" section** with real, working examples
5. **Create a "Known Limitations" section** that's transparent about what's missing
6. **Keep all the good conceptual material** but ground it in what actually exists
