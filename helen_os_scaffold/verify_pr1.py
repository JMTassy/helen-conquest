import sys
import os
from helen_os.kernel import GovernanceVM
import json
import concurrent.futures

def test_concurrency():
    ledger = "storage/test_ledger.ndjson"
    if os.path.exists(ledger): os.remove(ledger)
    
    vm = GovernanceVM(ledger)
    
    def run_proposal(i):
        vm.propose({"type": "test_concurrent", "val": i, "api_key": "sk-1234567890abcdef1234567890"})
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        list(executor.map(run_proposal, range(20)))
        
    # Verify results
    with open(ledger, "r") as f:
        lines = f.readlines()
        assert len(lines) == 20
        
        seqs = []
        for line in lines:
            data = json.loads(line)
            # Check for redaction
            assert "[OPENAI_KEY_REDACTED]" in line
            assert "api_key" not in data["payload"] or data["payload"]["api_key"] == "[OPENAI_KEY_REDACTED]"
            
            # Check for seq and schema
            assert "seq" in data
            assert data["schema_version"] == "ledger_v2"
            seqs.append(data["seq"])
            
        # Check sequence monotonicity
        assert seqs == sorted(seqs)
        assert len(set(seqs)) == 20
        print("PR#1 Verification: PASS (Concurrency, Redaction, Seq Monotonicity)")

if __name__ == "__main__":
    test_concurrency()
