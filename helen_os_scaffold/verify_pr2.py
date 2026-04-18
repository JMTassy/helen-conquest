import os
import json
from helen_os.kernel import GovernanceVM
from helen_os.memory import MemoryKernel
from helen_os.adapters import get_adapter
from helen_os.helen import HELEN

def test_idempotence():
    ledger = "storage/test_pr2.ndjson"
    mem_db = "memory/test_pr2.db"
    mem_nd = "memory/test_pr2.ndjson"
    idemp_index = "storage/idempotence_index_v1.ndjson"
    
    for f in [ledger, mem_db, mem_nd, idemp_index]:
        if os.path.exists(f): os.remove(f)
    
    config = {"adapter": "openai", "openai": {"model": "gpt-3.5-turbo"}} # Mock-like if needed, but we use actual adapter
    # For local test, we might want to use the local mistral if available
    
    vm = GovernanceVM(ledger)
    memory = MemoryKernel(mem_db, mem_nd)
    config = {
        "adapter": {
            "type": "ollama",
            "model": "mistral",
            "base_url": "http://localhost:11434"
        }
    }
    adapter = get_adapter(config)
    helen = HELEN(vm, memory, adapter)
    
    task = "Test Idempotence Task"
    
    print("Run 1: Executing task...")
    res1 = helen.run_task(task)
    assert "receipt" in res1
    
    # Check ledger for tool logs
    with open(ledger, "r") as f:
        content = f.read()
        assert "tool_call_v1" in content
        assert "tool_result_v1" in content
        assert "task_execution" in content
        
    print("Run 2: Expecting idempotent hit...")
    res2 = helen.run_task(task)
    
    assert res2["status"] == "idempotent_hit"
    assert "outcome" in res2
    assert res2["outcome"]["input_hash"] != None
    
    print("PR#2 Verification: PASS (Tool-Loop Logging & Idempotence)")

if __name__ == "__main__":
    test_idempotence()
