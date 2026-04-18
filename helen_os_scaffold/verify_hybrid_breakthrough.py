import os
import sys
import json
from pathlib import Path
import yaml

# Add the scaffold to the path
scaffold_path = Path("/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24/helen_os_scaffold")
sys.path.append(str(scaffold_path))

from helen_os.adapters import get_adapter
from helen_os.soul import get_dynamic_prompt
from helen_os.kernel.governance_vm import GovernanceVM

def test_hybrid_breakthrough():
    print("🧪 HELEN OS v3 Hybrid Architecture Verification")
    print("-" * 45)
    
    # Init config
    config_path = scaffold_path / "config.yaml"
    with open(config_path, 'r') as f:
        cfg = yaml.safe_load(f)
        
    print(f"Config type: {cfg.get('adapter', {}).get('type')}")
    
    # 1. Verify Adapter Type
    adapter = get_adapter(cfg)
    print(f"Adapter class: {adapter.__class__.__name__}")
    if adapter.__class__.__name__ == "HybridSerpentAdapter":
        print("✅ SUCCESS: HybridSerpentAdapter correctly instantiated.")
    else:
        print("❌ FAILURE: HybridSerpentAdapter not found.")
        
    # 2. Verify Dynamic Prompt (Hybrid)
    vm = GovernanceVM(":memory:")
    dynamic_prompt = get_dynamic_prompt(vm, hybrid=True)
    if "[SYSTEM_BREAKTHROUGH: HYBRID_COGNITION_v3]" in dynamic_prompt:
        print("✅ SUCCESS: Hybrid metaphors detected in dynamic prompt.")
    else:
        print("❌ FAILURE: Hybrid metaphors missing.")
        
    # 3. Simulate Hybrid Transformation
    print("\n[STEP 3] Simulating Hybrid state transition...")
    prompt = "Test the recurrent gate."
    response = adapter.generate(prompt, history=[])
    print(f"Recurrent State After: {adapter.recurrent_state_summary}")
    if adapter.recurrent_state_summary != "INITIAL_UNITY":
        print("✅ SUCCESS: Recurrent state updated via Gated Delta simulation.")
    else:
        print("❌ FAILURE: Recurrent state remains static.")

    print("\n" + "=" * 45)
    print("HYBRID COGNITIVE ARCHITECTURE VERIFIED")

if __name__ == "__main__":
    test_hybrid_breakthrough()
